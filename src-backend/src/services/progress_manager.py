# ruff: noqa: RUF002
"""WebSocket 连接管理器 —— 按 job_id 订阅 Redis Pub/Sub 并转发进度消息。"""

import json
import logging
import threading
import time

import redis
from fastapi import WebSocket
from src.core.config import config as proj_config


class ProgressManager:
    """管理 WebSocket 连接池，按 job_id 订阅 Redis Pub/Sub channel。

    每个 job_id 维护一个 subscriber 线程 + 一组 WebSocket 连接，
    当同 job_id 的所有连接断开后自动取消 Redis 订阅。
    """

    def __init__(self) -> None:
        self._redis_url = proj_config.REDIS_URL
        self._channels: dict[str, dict] = {}
        self._lock = threading.Lock()

    async def subscribe(self, websocket: WebSocket, job_id: str) -> None:
        """建立 WebSocket 连接并加入对应 job_id 的消息广播组。"""
        await websocket.accept()
        with self._lock:
            if job_id not in self._channels:
                import asyncio

                self._channels[job_id] = {
                    "connections": set(),
                    "thread": None,
                    "stop_event": threading.Event(),
                    "loop": asyncio.get_running_loop(),
                }
            entry = self._channels[job_id]
            entry["connections"].add(websocket)

        if entry["thread"] is None:
            entry["thread"] = threading.Thread(
                target=self._listen_redis,
                args=(job_id, entry["stop_event"]),
                daemon=True,
            )
            entry["thread"].start()

        try:
            while True:
                try:
                    await websocket.receive_text()
                except Exception:
                    break
        finally:
            await self._disconnect(websocket, job_id)

    async def _disconnect(self, websocket: WebSocket, job_id: str) -> None:
        """断开 WebSocket 连接，清理无连接的 channel。"""
        with self._lock:
            entry = self._channels.get(job_id)
            if entry is None:
                return
            entry["connections"].discard(websocket)
            if not entry["connections"]:
                entry["stop_event"].set()
                del self._channels[job_id]

    def _listen_redis(self, job_id: str, stop_event: threading.Event) -> None:
        """后台线程：订阅 Redis Pub/Sub 并广播给所有 WebSocket 连接。

        自动重连：Redis 重启或网络断开后 3s 重新订阅。
        """
        _logger = logging.getLogger("gproject.progress")
        while not stop_event.is_set():
            r: redis.Redis | None = None
            pubsub: redis.client.PubSub | None = None
            try:
                r = redis.Redis.from_url(self._redis_url, decode_responses=True)
                pubsub = r.pubsub()
                pubsub.subscribe(f"progress:{job_id}")
                _logger.info("Redis subscribed to progress:%s", job_id)

                while not stop_event.is_set():
                    message = pubsub.get_message(timeout=1.0)
                    if message is None:
                        continue
                    if message["type"] != "message":
                        continue
                    data_str = message.get("data", "")
                    if not data_str:
                        continue
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    self._broadcast(job_id, data)
            except Exception as exc:
                _logger.error(
                    "Redis listen thread for job_id=%s failed, retry in 3s: %s",
                    job_id,
                    exc,
                )
                time.sleep(3)
            finally:
                import contextlib

                if pubsub is not None:
                    with contextlib.suppress(Exception):
                        pubsub.close()
                if r is not None:
                    with contextlib.suppress(Exception):
                        r.close()

    def _broadcast(self, job_id: str, data: dict) -> None:
        """向指定 job_id 的所有 WebSocket 连接广播消息。

        使用 asyncio.run_coroutine_threadsafe 从后台线程安全调度到主事件循环。
        """
        import asyncio

        with self._lock:
            entry = self._channels.get(job_id)
            if entry is None:
                return
            loop = entry.get("loop")
            if loop is None:
                return
            dead: list[WebSocket] = []
            text = json.dumps(data, ensure_ascii=False)
            for ws in list(entry["connections"]):
                try:
                    asyncio.run_coroutine_threadsafe(ws.send_text(text), loop)
                except RuntimeError:
                    dead.append(ws)
            for ws in dead:
                entry["connections"].discard(ws)


_progress_manager: ProgressManager | None = None


def get_progress_manager() -> ProgressManager:
    """获取全局单例 ProgressManager。"""
    global _progress_manager
    if _progress_manager is None:
        _progress_manager = ProgressManager()
    return _progress_manager
