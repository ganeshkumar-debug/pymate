import os
import sys
import json
import base64
import urllib.request
import urllib.error

PROJECT_FILES = [
    "README.md",
    ".gitignore",
    "requirements.txt",
    "vercel.json",
    "main.py",
    "api/index.py",
    "public/index.html",
    "public/css/style.css",
    "public/js/app.js",
    "public/assets/logo.svg",
    "public/assets/favicon.svg"
]

def make_request(url, token, data=None, method="GET"):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "PyMate-Deployer",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def push_project(token, repo_name="Pymate", private=False):
    print("Connecting to GitHub...")
    try:
        user_info = make_request("https://api.github.com/user", token)
    except urllib.error.HTTPError as e:
        print(f"Authentication failed: HTTP {e.code} - {e.read().decode('utf-8')}")
        return False
    
    username = user_info.get("login")
    print(f"Authenticated as GitHub user: @{username}")

    # Step 1: Create repository if it doesn't exist
    print(f"Creating repository '{repo_name}' on GitHub...")
    repo_url = f"https://api.github.com/repos/{username}/{repo_name}"
    try:
        repo_data = make_request("https://api.github.com/user/repos", token, {
            "name": repo_name,
            "description": "PyMate — Dedicated Python AI Chatbot with Black & Violet Cyber Theme. Vercel & Supabase ready.",
            "private": private,
            "auto_init": False
        }, method="POST")
        print(f"Repository created: {repo_data.get('html_url')}")
    except urllib.error.HTTPError as e:
        if e.code == 422:
            print(f"Repository '{repo_name}' already exists. Updating files...")
        else:
            print(f"Failed to create repo: HTTP {e.code} - {e.read().decode('utf-8')}")
            return False

    # Step 2: Push files
    print(f"\nPushing {len(PROJECT_FILES)} files to main branch...")
    for rel_path in PROJECT_FILES:
        clean_path = rel_path.replace("\\", "/")
        if not os.path.exists(clean_path):
            print(f"  [SKIP] Missing: {clean_path}")
            continue

        with open(clean_path, "rb") as f:
            content_bytes = f.read()
        b64_content = base64.b64encode(content_bytes).decode("utf-8")

        # Check if file exists in repo to get sha for update
        file_api_url = f"https://api.github.com/repos/{username}/{repo_name}/contents/{clean_path}"
        existing_sha = None
        try:
            cur = make_request(file_api_url, token)
            existing_sha = cur.get("sha")
        except urllib.error.HTTPError as e:
            if e.code != 404:
                print(f"  Notice checking {clean_path}: {e.code}")

        payload = {
            "message": f"Deploy {clean_path}",
            "content": b64_content,
            "branch": "main"
        }
        if existing_sha:
            payload["sha"] = existing_sha

        try:
            res = make_request(file_api_url, token, payload, method="PUT")
            status = "Updated" if existing_sha else "Created"
            print(f"  ✓ {status}: {clean_path}")
        except urllib.error.HTTPError as e:
            print(f"  ✗ Error pushing {clean_path}: HTTP {e.code} - {e.read().decode('utf-8')}")

    target_url = f"https://github.com/{username}/{repo_name}"
    print(f"\n🚀 ALL FILES SUCCESSFULLY PUSHED TO GITHUB!")
    print(f"Repository URL: {target_url}")
    return target_url

if __name__ == "__main__":
    token = sys.argv[1] if len(sys.argv) > 1 else os.getenv("GITHUB_TOKEN")
    if not token:
        print("Usage: python push_to_github.py <GITHUB_PERSONAL_ACCESS_TOKEN>")
        sys.exit(1)
    push_project(token)
