# ruff: noqa: RUF002, RUF001
"""端到端测试：注册 → 登录 → 上传 → 获取 → 下载"""

import hashlib
import json
import time

import httpx

BASE = "http://127.0.0.1:8000"
PASS = "Str0ng!Pass"

email = f"e2e_{int(time.time())}@test.com"
client = httpx.Client(timeout=30)


def step(name):
    print(f"\n{'=' * 60}\n  {name}\n{'=' * 60}")


# ══════════════════════════════════════════════════════
# Step 1: 注册
# ══════════════════════════════════════════════════════
step("1. 注册用户")
resp = client.post(
    f"{BASE}/api/v1/user",
    json={
        "name": "e2e_tester",
        "email": email,
        "password": PASS,
    },
)
print(f"  POST /api/v1/user → {resp.status_code}")
data = resp.json()
print(f"  {json.dumps(data, ensure_ascii=False)}")
assert data["success"], f"注册失败: {data['error']}"
print("  [OK] 注册成功")

# ══════════════════════════════════════════════════════
# Step 2: 登录
# ══════════════════════════════════════════════════════
step("2. 登录获取 token")
resp = client.post(
    f"{BASE}/api/v1/auth/login",
    json={
        "email": email,
        "password": PASS,
    },
)
print(f"  POST /api/v1/auth/login → {resp.status_code}")
data = resp.json()
print(f"  user_id={data.get('user_id')}, success={data['success']}")
assert data["success"], f"登录失败: {data['error']}"
access_token = data["access_token"]
print(f"  access_token: {access_token[:40]}...")
print("  [OK] 登录成功")

auth = {"Authorization": f"Bearer {access_token}"}


# ══════════════════════════════════════════════════════
# Step 3: 上传文件
# ══════════════════════════════════════════════════════
step("3. 分块上传数据集")

content = b'{"instruction":"hello","output":"world"}\n' * 1000
file_hash = hashlib.sha256(content).hexdigest()
print(f"  文件大小: {len(content)} bytes, SHA-256: {file_hash[:16]}...")

# 3a. initiate
resp = client.post(
    f"{BASE}/api/v1/dataset/upload/initiate",
    json={"filename": "test.jsonl", "file_size": len(content), "file_hash": file_hash},
    headers=auth,
)
print(f"  POST /upload/initiate → {resp.status_code}")
print(f"  Body: {resp.text[:500]}")
init = resp.json()
upload_id = init["upload_id"]
total = init["total_chunks"]
print(f"  upload_id={upload_id}, total_chunks={total}")
assert init["upload_id"], "initiate 失败"

# 3b. upload chunks
chunk_size = init["chunk_size"]
for i in range(total):
    start = i * chunk_size
    end = min(start + chunk_size, len(content))
    chunk = content[start:end]
    resp = client.post(
        f"{BASE}/api/v1/dataset/upload/chunk",
        data={"upload_id": upload_id, "chunk_index": str(i)},
        files={"file": (f"chunk_{i}", chunk)},
        headers=auth,
    )
    assert resp.json()["received"], f"chunk {i} upload failed"
print(f"  [OK] {total} 个分片上传完成")

# 3c. complete
resp = client.post(
    f"{BASE}/api/v1/dataset/upload/complete",
    json={"upload_id": upload_id, "owner_id": 0, "name": "e2e_test_dataset", "desc": "端到端测试"},
    headers=auth,
)
print(f"  POST /upload/complete → {resp.status_code}")
complete = resp.json()
print(f"  {json.dumps(complete, ensure_ascii=False)}")
assert complete["success"], f"上传失败: {complete.get('error')}"
dataset_id = complete["dataset_id"]
print(f"  [OK] 上传完成, dataset_id={dataset_id}")


# ══════════════════════════════════════════════════════
# Step 4: 获取数据集信息
# ══════════════════════════════════════════════════════
step("4. 获取数据集详情")
resp = client.get(f"{BASE}/api/v1/dataset/{dataset_id}", headers=auth)
print(f"  GET /dataset/{dataset_id} → {resp.status_code}")
data = resp.json()
ds = data.get("dataset", {})
print(f"  name={ds.get('name')}, format={ds.get('meta', {}).get('format')}, size={ds.get('meta', {}).get('file_size')}")
assert ds, f"获取失败: {data.get('error')}"
print("  [OK] 获取成功")


# ══════════════════════════════════════════════════════
# Step 5: 下载文件
# ══════════════════════════════════════════════════════
step("5. 下载文件")
# 5a. 获取下载令牌
resp = client.post(f"{BASE}/api/v1/dataset/{dataset_id}/download", headers=auth)
print(f"  POST /dataset/{dataset_id}/download → {resp.status_code}")
download_data = resp.json()
download_token = download_data.get("download_token")
print(f"  filename={download_data.get('filename')}, token={download_token[:40]}...")
assert download_token, "获取下载令牌失败"
print("  [OK] 令牌生成成功")

# 5b. 凭令牌下载
resp = client.get(f"{BASE}/down_dataset/{download_token}")
print(f"  GET /down_dataset/{{token}} → {resp.status_code}")
assert resp.status_code == 200, f"下载失败: {resp.status_code}"
downloaded = resp.content
downloaded_hash = hashlib.sha256(downloaded).hexdigest()
print(f"  下载文件大小: {len(downloaded)} bytes")
print(f"  下载文件 SHA-256: {downloaded_hash[:16]}...")
assert downloaded_hash == file_hash, f"哈希不匹配! 期望 {file_hash[:16]}, 实际 {downloaded_hash[:16]}"
print("  [OK] 哈希校验通过，下载成功")


# ══════════════════════════════════════════════════════
# 总结
# ══════════════════════════════════════════════════════
client.close()
print(f"\n{'=' * 60}")
print("  [ALL PASS] 端到端测试全部通过!")
print(f"  用户: {email}")
print(f"  数据集 ID: {dataset_id}")
print(f"  文件大小: {len(content)} bytes, 哈希校验: [OK]")
print(f"{'=' * 60}")
