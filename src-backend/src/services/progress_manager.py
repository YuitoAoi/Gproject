"""WebSocket 连接管理器 —— 按 job_id 订阅 Redis Pub/Sub 并转发进度消息。"""
import json
import threading
from typing import Optional

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
                self._channels[job_id] = {
                    "connections": set(),
                    "thread": None,
                    "stop_event": threading.Event(),
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
        """后台线程：订阅 Redis Pub/Sub 并广播给所有 WebSocket 连接。"""
        r: Optional[redis.Redis] = None
        pubsub: Optional[redis.client.PubSub] = None
        try:
            r = redis.Redis.from_url(self._redis_url, decode_responses=True)
            pubsub = r.pubsub()
            pubsub.subscribe(f"progress:{job_id}")

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
        except Exception:
            pass
        finally:
            if pubsub is not None:
                try:
                    pubsub.close()
                except Exception:
                    pass
            if r is not None:
                try:
                    r.close()
                except Exception:
                    pass

    def _broadcast(self, job_id: str, data: dict) -> None:
        """向指定 job_id 的所有 WebSocket 连接广播消息。

        使用线程安全的 asyncio 事件循环调度。
        """
        import asyncio

        with self._lock:
            entry = self._channels.get(job_id)
            if entry is None:
                return
            dead: list[WebSocket] = []
            text = json.dumps(data, ensure_ascii=False)
            for ws in list(entry["connections"]):
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.call_soon_threadsafe(
                            lambda w=ws, t=text: asyncio.ensure_future(w.send_text(t))
                        )
                    else:
                        dead.append(ws)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                entry["connections"].discard(ws)


_progress_manager: Optional[ProgressManager] = None


def get_progress_manager() -> ProgressManager:
    """获取全局单例 ProgressManager。"""
    global _progress_manager
    if _progress_manager is None:
        _progress_manager = ProgressManager()
    return _progress_manager
