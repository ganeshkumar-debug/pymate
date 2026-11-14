import os
import hashlib
import json
import urllib.request
import urllib.error
import sys

DEPLOY_FILES = [
    "vercel.json",
    "requirements.txt",
    "api/index.py",
    "public/index.html",
    "public/css/style.css",
    "public/js/app.js",
    "public/assets/logo.svg",
    "public/assets/favicon.svg"
]

def get_file_manifest():
    manifest = []
    for rel_path in DEPLOY_FILES:
        if not os.path.exists(rel_path):
            raise FileNotFoundError(f"Missing required deployment file: {rel_path}")
        with open(rel_path, "rb") as f:
            data = f.read()
        sha = hashlib.sha1(data).hexdigest()
        manifest.append({
            "file": rel_path.replace("\\", "/"),
            "size": len(data),
            "sha": sha,
            "data": data
        })
    return manifest

def upload_file(token, file_data, sha, size):
    url = "https://api.vercel.com/v2/files"
    req = urllib.request.Request(
        url,
        data=file_data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream",
            "Content-Length": str(size),
            "x-vercel-digest": sha
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status in (200, 201)
    except urllib.error.HTTPError as e:
        # 409 means file already exists/uploaded on Vercel's CAS
        if e.code == 409:
            return True
        raise

def create_deployment(token, manifest, project_name="pymate"):
    url = "https://api.vercel.com/v13/deployments"
    files_payload = [
        {"file": item["file"], "sha": item["sha"], "size": item["size"]}
        for item in manifest
    ]
    
    payload = {
        "name": project_name,
        "files": files_payload,
        "projectSettings": {
            "framework": None
        }
    }
    
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def deploy(token=None):
    if not token:
        token = os.getenv("VERCEL_TOKEN")
    if not token:
        print("ERROR: No VERCEL_TOKEN provided.")
        print("Usage: python deploy_vercel.py <YOUR_VERCEL_TOKEN>")
        print("Or set VERCEL_TOKEN in your environment or .env file.")
        return None

    manifest = get_file_manifest()
    print(f"Uploading {len(manifest)} files to Vercel Content Storage...")
    for item in manifest:
        print(f"  Uploading {item['file']} ({item['size']} bytes)...")
        upload_file(token, item["data"], item["sha"], item["size"])

    print("\nCreating deployment on Vercel...")
    res = create_deployment(token, manifest)
    url = res.get("url")
    print(f"\nDEPLOYMENT SUCCESSFUL!")
    print(f"URL: https://{url}")
    print(f"Deployment ID: {res.get('id')}")
    print(f"Ready State: {res.get('readyState')}")
    return res

if __name__ == "__main__":
    tok = sys.argv[1] if len(sys.argv) > 1 else os.getenv("VERCEL_TOKEN")
    deploy(tok)
