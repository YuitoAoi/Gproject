import json
import os
import tempfile

import pytest
from api.job_manager import JobManager


class TestJobManager:
    @pytest.fixture
    def manager(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield JobManager(jobs_dir=tmpdir)

    def test_create_creates_status_file(self, manager):
        job_id = manager.create({"test": "config"})
        status = manager.get(job_id)
        assert status["job_id"] == job_id
        assert status["status"] == "pending"
        assert status["progress"] == 0.0
        assert status["error"] is None
        assert "created_at" in status

    def test_create_generates_unique_ids(self, manager):
        id1 = manager.create({})
        id2 = manager.create({})
        assert id1 != id2

    def test_get_nonexistent_raises(self, manager):
        with pytest.raises(FileNotFoundError):
            manager.get("nonexistent")

    def test_update_changes_status(self, manager):
        job_id = manager.create({})
        manager.update(job_id, status="running", progress=0.5)
        status = manager.get(job_id)
        assert status["status"] == "running"
        assert status["progress"] == 0.5

    def test_update_preserves_other_fields(self, manager):
        job_id = manager.create({})
        original = manager.get(job_id)
        manager.update(job_id, status="done")
        updated = manager.get(job_id)
        assert updated["status"] == "done"
        assert updated["created_at"] == original["created_at"]

    def test_get_output_dir_creates_directory(self, manager):
        job_id = manager.create({})
        output_dir = manager.get_output_dir(job_id)
        assert os.path.isdir(output_dir)

    def test_get_output_file_returns_none_when_empty(self, manager):
        job_id = manager.create({})
        assert manager.get_output_file(job_id) is None

    def test_get_output_file_finds_jsonl(self, manager):
        job_id = manager.create({})
        output_dir = manager.get_output_dir(job_id)
        generate_dir = os.path.join(output_dir, "generate")
        os.makedirs(generate_dir)
        expected = os.path.join(generate_dir, "test.jsonl")
        with open(expected, "w") as f:
            f.write("{}")
        result = manager.get_output_file(job_id)
        assert result == expected

    def test_update_if_matches_condition(self, manager):
        """update_if 在条件匹配时应执行更新并返回 True"""
        job_id = manager.create({})
        applied = manager.update_if(
            job_id,
            condition={"status": "pending"},
            updates={"status": "running", "progress": 0.3},
        )
        assert applied is True
        status = manager.get(job_id)
        assert status["status"] == "running"
        assert status["progress"] == 0.3

    def test_update_if_no_match_returns_false(self, manager):
        """update_if 条件不匹配时应返回 False 且不修改状态"""
        job_id = manager.create({})
        # 先改状态为 running
        manager.update(job_id, status="running")
        # 条件要求 pending，实际是 running，不应匹配
        applied = manager.update_if(
            job_id,
            condition={"status": "pending"},
            updates={"status": "done"},
        )
        assert applied is False
        status = manager.get(job_id)
        assert status["status"] == "running"  # 未变

    def test_update_if_partial_condition(self, manager):
        """update_if 条件只检查指定字段，其他字段无所谓"""
        job_id = manager.create({})
        manager.update(job_id, status="running", progress=0.5)
        # 只检查 progress 是否等于 0.5，不管 status 是什么
        applied = manager.update_if(
            job_id,
            condition={"progress": 0.5},
            updates={"stage": "generate"},
        )
        assert applied is True
        status = manager.get(job_id)
        assert status["stage"] == "generate"

    def test_update_if_missing_job_raises(self, manager):
        """对不存在的 job_id 调用 update_if 应抛 FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            manager.update_if("nonexistent", condition={}, updates={"status": "done"})
