import subprocess
import os

BSDATA_REPO_URL = "https://github.com/BSData/wh40k-10e"
LOCAL_REPO_PATH = "./data/BSData"

if os.path.exists(LOCAL_REPO_PATH):
    print("Updating existing BSData repository...")
    subprocess.run(["git", "-C", LOCAL_REPO_PATH, "pull"], check=True)
else:
    print("Cloning BSData repository...")
    subprocess.run(["git", "clone", BSDATA_REPO_URL, LOCAL_REPO_PATH], check=True)