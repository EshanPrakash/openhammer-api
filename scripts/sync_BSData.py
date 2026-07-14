import subprocess
import os

REPOS = [
    ("https://github.com/BSData/wh40k-10e", "./data/BSData-10e"),
    ("https://github.com/BSData/wh40k-11e", "./data/BSData-11e"),
]

for repo_url, local_path in REPOS:
    if os.path.exists(local_path):
        print(f"Updating existing BSData repository at {local_path}...")
        subprocess.run(["git", "-C", local_path, "pull"], check=True)
    else:
        print(f"Cloning BSData repository {repo_url}...")
        subprocess.run(["git", "clone", repo_url, local_path], check=True)