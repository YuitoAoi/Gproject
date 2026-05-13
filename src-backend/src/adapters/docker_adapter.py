"""docker-py implementation of the DockerClient port."""

from __future__ import annotations

import logging
import threading
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import docker
import docker.errors
from docker.types import DeviceRequest, Mount

from src.core.docker_job import (
    DockerJob,
    DockerJobError,
    DockerJobStatus,
)
from src.services.interfaces.docker_client import DockerClient

_logger = logging.getLogger(__name__)


class DockerClientAdapter(DockerClient):
    def __init__(self) -> None:
        self._client = docker.from_env()

    def submit(self, job: DockerJob) -> str:
        try:
            self._remove_if_exists(job.job_id)
            self._ensure_image(job.image)
            container = self._client.containers.run(
                image=job.image,
                name=job.job_id,
                command=job.command,
                environment=dict(job.env),
                mounts=self._build_mounts(job),
                device_requests=self._build_device_requests(job),
                ports=self._build_ports(job),
                detach=True,
                remove=False,
                stdout=True,
                stderr=True,
            )
        except docker.errors.APIError as exc:
            raise DockerJobError(f"failed to submit {job.job_id}: {exc}") from exc

        if job.log_path:
            self._spawn_log_writer(container, job.log_path)
        return container.id

    # ── helpers ─────────────────────────────────────────────────

    def _remove_if_exists(self, job_id: str) -> None:
        try:
            existing = self._client.containers.get(job_id)
        except docker.errors.NotFound:
            return
        existing.remove(force=True)

    def _ensure_image(self, image: str) -> None:
        try:
            self._client.images.get(image)
        except docker.errors.ImageNotFound:
            self._client.images.pull(image)

    @staticmethod
    def _build_mounts(job: DockerJob) -> list[Mount]:
        return [
            Mount(
                target=vm.container_path,
                source=vm.host_path,
                type="bind",
                read_only=(vm.mode == "ro"),
            )
            for vm in job.mounts
        ]

    @staticmethod
    def _build_device_requests(job: DockerJob) -> list[DeviceRequest]:
        if job.gpus == "none":
            return []
        if job.gpus == "all":
            return [DeviceRequest(count=-1, capabilities=[["gpu"]])]
        if job.gpus.startswith("device="):
            ids = job.gpus.removeprefix("device=").split(",")
            return [DeviceRequest(device_ids=ids, capabilities=[["gpu"]])]
        return []

    @staticmethod
    def _build_ports(job: DockerJob) -> dict[str, int] | None:
        if not job.ports:
            return None
        return {f"{c}/tcp": h for c, h in job.ports.items()}

    @staticmethod
    def _spawn_log_writer(container, log_path: str) -> None:
        def _run() -> None:
            try:
                with open(log_path, "ab") as f:
                    for chunk in container.logs(stream=True, follow=True):
                        if not chunk:
                            continue
                        f.write(chunk if isinstance(chunk, bytes) else chunk.encode())
                        f.flush()
            except Exception:
                _logger.exception("log writer for %s exited", container.name)

        threading.Thread(target=_run, daemon=True).start()

    # ── unimplemented in this task ──────────────────────────────

    def status(self, job_id: str) -> DockerJobStatus:
        raise NotImplementedError

    def stream_logs(self, job_id: str, *, follow: bool = False) -> Iterator[str]:
        raise NotImplementedError

    def stop(self, job_id: str, *, timeout: int = 10) -> None:
        raise NotImplementedError

    def wait(self, job_id: str, *, timeout: int | None = None) -> int:
        raise NotImplementedError

    def cleanup_failed(self, *, max_age_hours: int = 24) -> int:
        raise NotImplementedError
