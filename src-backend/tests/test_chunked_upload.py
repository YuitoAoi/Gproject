"""ChunkedUploadService 集成测试：分块→续传→校验→组装→秒传"""
import hashlib
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_PROJECT = Path(__file__).resolve().parent.parent
if str(_PROJECT) not in sys.path:
    sys.path.insert(0, str(_PROJECT))
_SVC = str(_PROJECT / "src" / "services")
if _SVC not in sys.path:
    sys.path.insert(0, _SVC)

from src.core.dataset import Dataset, DatasetMeta
from src.services.chunked_upload_service import (
    ChunkedUploadService,
    CompleteUploadRequest,
    InitiateUploadRequest,
    _upload_state,
)


@pytest.fixture(autouse=True)
def _clean_upload_state():
    """每个测试前清空上传会话状态。"""
    _upload_state._sessions.clear()
    yield
    _upload_state._sessions.clear()


@pytest.fixture
def svc(tmp_path, monkeypatch):
    """用临时目录替代 datasets/ 和 chunks/ 路径。"""
    from src.core import config
    monkeypatch.setattr(config.config, "DATA_DIR", str(tmp_path))

    mock_ds_repo = MagicMock()

    # mock create: 设置 dataset.id = 100
    def _create(dataset):
        dataset.id = 100
        return None

    mock_ds_repo.create.side_effect = _create
    mock_ds_repo.update.return_value = None

    return ChunkedUploadService(
        dataset_repo=mock_ds_repo,
        file_repo=MagicMock(),  # 不使用 file_repo，直接用 Path 读写
    ), mock_ds_repo, tmp_path


# ══════════════════════════════════════════════════════════
# 完整上传流程
# ══════════════════════════════════════════════════════════

def test_full_upload_flow(svc):
    """initiate → upload_chunks → complete → 文件存在且哈希正确"""
    svc_inst, mock_repo, tmp = svc

    # 准备测试数据
    content = b"Hello GProject! " * 50000  # ~800KB
    file_hash = hashlib.sha256(content).hexdigest()

    # Step 1: initiate
    init = svc_inst.initiate(InitiateUploadRequest(
        filename="test.json",
        file_size=len(content),
        file_hash=file_hash,
        chunk_size=1024 * 1024,  # 1MB chunks
    ))
    assert init.upload_id
    assert init.total_chunks == 1  # ~800KB → 1 chunk
    assert init.is_instant_complete is False

    # Step 2: upload chunk
    for i in range(init.total_chunks):
        start = i * 1024 * 1024
        end = min(start + 1024 * 1024, len(content))
        chunk_data = content[start:end]
        resp = svc_inst.upload_chunk(init.upload_id, i, chunk_data)
        assert resp.received is True

    # Step 3: complete
    complete = svc_inst.complete(CompleteUploadRequest(
        upload_id=init.upload_id,
        owner_id=1,
        name="test-dataset",
        desc="desc",
    ))
    assert complete.success is True
    assert complete.dataset_id == 100
    assert "test.json" not in str(complete.file_path)  # 文件已重命名为 100.json

    # 验证文件存在且内容正确
    final = Path(complete.file_path)
    assert final.exists()
    assert final.read_bytes() == content


# ══════════════════════════════════════════════════════════
# 断点续传
# ══════════════════════════════════════════════════════════

def test_resume_upload(svc):
    """上传部分分片后查询状态 → 断点续传 → 完成"""
    svc_inst, mock_repo, tmp = svc

    content = b"X" * (3 * 1024 * 1024)  # 3MB
    file_hash = hashlib.sha256(content).hexdigest()

    init = svc_inst.initiate(InitiateUploadRequest(
        filename="big.json",
        file_size=len(content),
        file_hash=file_hash,
        chunk_size=1024 * 1024,
    ))
    assert init.total_chunks == 3

    # 只上传第 0 和第 2 片
    svc_inst.upload_chunk(init.upload_id, 0, content[0:1*1024*1024])
    svc_inst.upload_chunk(init.upload_id, 2, content[2*1024*1024:3*1024*1024])

    # 查询状态
    status = svc_inst.get_status(init.upload_id)
    assert status["uploaded_chunks"] == [0, 2]
    assert status["is_complete"] is False

    # 续传第 1 片
    svc_inst.upload_chunk(init.upload_id, 1, content[1*1024*1024:2*1024*1024])

    status = svc_inst.get_status(init.upload_id)
    assert status["uploaded_chunks"] == [0, 1, 2]
    assert status["is_complete"] is True

    # 完成
    complete = svc_inst.complete(CompleteUploadRequest(
        upload_id=init.upload_id, owner_id=1, name="resumed",
    ))
    assert complete.success is True
    assert Path(complete.file_path).read_bytes() == content


# ══════════════════════════════════════════════════════════
# 哈希校验失败
# ══════════════════════════════════════════════════════════

def test_hash_mismatch(svc):
    """客户端提交的哈希与实际文件哈希不一致 → complete 失败"""
    svc_inst, mock_repo, tmp = svc

    content = b"correct data"
    wrong_hash = "deadbeef" * 8

    init = svc_inst.initiate(InitiateUploadRequest(
        filename="bad.json",
        file_size=len(content),
        file_hash=wrong_hash,  # 故意给错
        chunk_size=1024 * 1024,
    ))
    svc_inst.upload_chunk(init.upload_id, 0, content)

    complete = svc_inst.complete(CompleteUploadRequest(
        upload_id=init.upload_id, owner_id=1, name="bad",
    ))
    assert complete.success is False
    assert "Hash mismatch" in complete.error


# ══════════════════════════════════════════════════════════
# 相同文件秒传（相同哈希 → 需由调用方处理）
# ══════════════════════════════════════════════════════════

def test_same_hash_two_uploads(svc):
    """两个相同文件分别上传 → 各自成功，文件独立存储"""
    svc_inst, mock_repo, tmp = svc

    content = b"dedup test content"
    file_hash = hashlib.sha256(content).hexdigest()

    # 第一个文件
    init1 = svc_inst.initiate(InitiateUploadRequest(
        filename="a.json", file_size=len(content),
        file_hash=file_hash, chunk_size=1024 * 1024,
    ))
    svc_inst.upload_chunk(init1.upload_id, 0, content)
    r1 = svc_inst.complete(CompleteUploadRequest(
        upload_id=init1.upload_id, owner_id=1, name="ds1",
    ))
    assert r1.success

    # 第二个文件（相同哈希，不同的 mock ID）
    call_count = [0]

    def _create2(dataset):
        call_count[0] += 1
        dataset.id = 200 + call_count[0]
        return None

    mock_repo.create.side_effect = _create2

    init2 = svc_inst.initiate(InitiateUploadRequest(
        filename="b.json", file_size=len(content),
        file_hash=file_hash, chunk_size=1024 * 1024,
    ))
    svc_inst.upload_chunk(init2.upload_id, 0, content)
    r2 = svc_inst.complete(CompleteUploadRequest(
        upload_id=init2.upload_id, owner_id=1, name="ds2",
    ))
    assert r2.success
    # 两个文件都独立存在
    assert Path(r1.file_path).exists()
    assert Path(r2.file_path).exists()
