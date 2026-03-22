import requests
import os

# --- CONFIG ---
BASE_URL = "https://api.lantmateriet.se/stac-hojd/v1/search"

bbox = [12.112, 62.066, 12.608, 62.976]

DOWNLOAD_DIR = "downloads"

# --- READ CREDENTIALS FROM ENV ---
username = os.getenv("GEOTORGET_USERNAME")
password = os.getenv("GEOTORGET_PASSWORD")

if not username or not password:
    raise ValueError("Missing credentials: set GEOTORGET_USERNAME and GEOTORGET_PASSWORD")

auth = (username, password)

# --- PREPARE FOLDER ---
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- REQUEST ---
params = {
    "bbox": ",".join(map(str, bbox)),
    "limit": 1000
}

response = requests.get(BASE_URL, params=params, auth=auth)
response.raise_for_status()

data = response.json()

print(f"Found {len(data['features'])} items")

# --- EXTRACT DOWNLOAD URLS ---
download_urls = []

for item in data["features"]:
    assets = item.get("assets", {})
    
    if "data" in assets:
        url = assets["data"]["href"]
        download_urls.append(url)

print(f"Found {len(download_urls)} downloadable assets\n")

# --- DOWNLOAD STEP ---
for i, url in enumerate(download_urls, start=1):
    filename = url.split("/")[-1]
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    if os.path.exists(filepath):
        print(f"[{i}/{len(download_urls)}] Skipping (exists): {filename}")
        continue

    print(f"[{i}/{len(download_urls)}] Downloading: {filename}")

    try:
        with requests.get(url, stream=True, auth=auth) as r:
            r.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        print("   → Done")

    except Exception as e:
        print(f"   → Failed: {e}")