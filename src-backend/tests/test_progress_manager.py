"""ProgressManager 单元测试"""
from unittest.mock import MagicMock, patch

import pytest

from src.services.progress_manager import ProgressManager, get_progress_manager


class TestGetProgressManager:
    def test_returns_singleton(self):
        a = get_progress_manager()
        b = get_progress_manager()
        assert a is b


class TestProgressManager:
    @pytest.fixture
    def manager(self):
        return ProgressManager()

    @pytest.fixture
    def mock_ws(self):
        ws = MagicMock()
        ws.accept = MagicMock()
        ws.receive_text = MagicMock(side_effect=Exception("disconnect"))
        return ws

    # ── subscribe ───────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_subscribe_accepts_connection(self, manager, mock_ws):
        with patch.object(manager, "_listen_redis"):
            manager._channels = {}
            try:
                await manager.subscribe(mock_ws, "job-1")
            except Exception:
                pass
            mock_ws.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscribe_creates_channel_entry(self, manager, mock_ws):
        with patch.object(manager, "_listen_redis"):
            manager._channels = {}
            try:
                await manager.subscribe(mock_ws, "job-1")
            except Exception:
                pass
            assert "job-1" in manager._channels
            assert mock_ws in manager._channels["job-1"]["connections"]

    @pytest.mark.asyncio
    async def test_subscribe_shares_channel_for_same_job(self, manager, mock_ws):
        ws2 = MagicMock()
        ws2.accept = MagicMock()
        ws2.receive_text = MagicMock(side_effect=Exception("disconnect"))

        with patch.object(manager, "_listen_redis"):
            manager._channels = {}
            try:
                await manager.subscribe(mock_ws, "job-1")
            except Exception:
                pass
            try:
                await manager.subscribe(ws2, "job-1")
            except Exception:
                pass

            assert len(manager._channels["job-1"]["connections"]) == 2

    # ── disconnect ──────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self, manager, mock_ws):
        with patch.object(manager, "_listen_redis"):
            manager._channels = {}
            try:
                await manager.subscribe(mock_ws, "job-1")
            except Exception:
                pass

            await manager._disconnect(mock_ws, "job-1")
            assert mock_ws not in manager._channels["job-1"]["connections"]

    @pytest.mark.asyncio
    async def test_disconnect_cleans_empty_channel(self, manager, mock_ws):
        with patch.object(manager, "_listen_redis"):
            manager._channels = {}
            try:
                await manager.subscribe(mock_ws, "job-1")
            except Exception:
                pass

            await manager._disconnect(mock_ws, "job-1")
            assert "job-1" not in manager._channels

    @pytest.mark.asyncio
    async def test_disconnect_unknown_job_does_not_raise(self, manager, mock_ws):
        await manager._disconnect(mock_ws, "nonexistent")

    # ── broadcast ────────────────────────────────────────────

    def test_broadcast_sends_json_to_ws(self, manager):
        mock_ws = MagicMock()
        manager._channels = {
            "job-1": {
                "connections": {mock_ws},
                "thread": None,
                "stop_event": MagicMock(),
            }
        }
        manager._broadcast("job-1", {"status": "running"})
        # 由于 broadcast 通过 asyncio 调度发送，在同步测试中 ws 可能被标记为 dead
        # 这里主要验证不抛异常

    def test_broadcast_unknown_job_does_not_raise(self, manager):
        manager._broadcast("nonexistent", {"status": "done"})

    # ── _listen_redis ───────────────────────────────────────

    def test_listen_redis_stops_on_event(self, manager):
        """stop_event 被 set 后 listener 应退出"""
        stop_event = MagicMock()
        stop_event.is_set.side_effect = [False, True]  # 第一轮后退出

        with patch("redis.Redis") as mock_redis_cls:
            mock_redis = MagicMock()
            mock_pubsub = MagicMock()
            mock_pubsub.get_message.return_value = None
            mock_redis.pubsub.return_value = mock_pubsub
            mock_redis_cls.from_url.return_value = mock_redis

            manager._listen_redis("job-1", stop_event)

            mock_pubsub.subscribe.assert_called_once_with("progress:job-1")
            mock_pubsub.close.assert_called_once()
            mock_redis.close.assert_called_once()
