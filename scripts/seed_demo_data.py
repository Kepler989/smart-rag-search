"""
Seed demo data into the Smart RAG backend via the REST API.
Uploads all documents located in `sample_documents/`.
"""
import sys
import time
from pathlib import Path
import httpx

API_BASE_URL = "http://localhost:8000/api/v1"
SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_documents"


def seed():
    print(f"🔍 Checking backend health at {API_BASE_URL.replace('/api/v1', '')}/health...")
    try:
        health_resp = httpx.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=5.0)
        health_resp.raise_for_status()
        print("✅ Backend is healthy!")
    except Exception as e:
        print(f"❌ Could not reach backend: {e}")
        print("Please ensure the backend is running with './scripts/start_backend.sh'")
        sys.exit(1)

    sample_files = list(SAMPLE_DIR.glob("*.*"))
    if not sample_files:
        print(f"⚠️ No sample files found in {SAMPLE_DIR}")
        sys.exit(0)

    print(f"📂 Found {len(sample_files)} sample files to upload:")
    for file_path in sample_files:
        print(f"   - {file_path.name}")

    for file_path in sample_files:
        print(f"\n⬆️  Uploading {file_path.name}...")
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "application/octet-stream")}
            resp = httpx.post(f"{API_BASE_URL}/documents/upload", files=files, timeout=30.0)

        if resp.status_code == 201:
            doc = resp.json()
            doc_id = doc["id"]
            print(f"   ✅ Created document ID: {doc_id} (Status: {doc['status']})")
            
            # Poll status until ready
            print("   ⏳ Waiting for indexing to complete...", end="", flush=True)
            for _ in range(30):
                time.sleep(1.5)
                status_resp = httpx.get(f"{API_BASE_URL}/documents/{doc_id}")
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    current_status = status_data["status"]
                    if current_status == "ready":
                        print(f" Ready! ({status_data['total_chunks']} chunks indexed)")
                        break
                    elif current_status == "failed":
                        print(f" Failed: {status_data.get('error_message')}")
                        break
                    else:
                        print(".", end="", flush=True)
        else:
            print(f"   ❌ Upload failed: {resp.status_code} - {resp.text}")

    print("\n🎉 Seeding completed!")


if __name__ == "__main__":
    seed()
