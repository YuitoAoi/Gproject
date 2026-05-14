"""docker-py implementation of the DockerClient port."""

from __future__ import annotations

import logging
import threading
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import docker
import docker.errors
import requests.exceptions
from docker.types import DeviceRequest, Mount

from src.core.docker_job import (
    DockerJob,
    DockerJobError,
    DockerJobStatus,
)
from src.services.interfaces.docker_client import DockerClient

_logger = logging.getLogger(__name__)


def _parse_docker_time(raw: str | None) -> datetime | None:
    """Docker emits RFC3339 with nanoseconds and 'Z'. Parse or return None."""
    if not raw or raw.startswith("0001-01-01"):
        return None
    # Truncate to microseconds; replace trailing Z with +00:00 for fromisoformat.
    core, _, frac_tz = raw.partition(".")
    if frac_tz:
        # keep up to 6 digits of fraction, then whatever timezone tail is there
        digits = ""
        tail = ""
        for i, ch in enumerate(frac_tz):
            if ch.isdigit() and len(digits) < 6:
                digits += ch
            else:
                tail = frac_tz[i:]
                break
        raw = f"{core}.{digits}{tail}"
    raw = raw.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


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
        try:
            container = self._client.containers.get(job_id)
        except docker.errors.NotFound:
            return DockerJobStatus(state="missing")
        except docker.errors.APIError as exc:
            raise DockerJobError(f"failed to inspect {job_id}: {exc}") from exc

        state_map = {
            "created": "pending",
            "running": "running",
            "paused": "running",
            "restarting": "running",
            "exited": "exited",
            "dead": "exited",
            "removing": "removed",
        }
        state = state_map.get(container.status, "running")

        attrs = container.attrs or {}
        state_attrs = attrs.get("State", {})
        net_attrs = attrs.get("NetworkSettings", {}).get("Ports") or {}

        host_port: int | None = None
        for _, bindings in net_attrs.items():
            if bindings:
                host_port = int(bindings[0]["HostPort"])
                break

        return DockerJobStatus(
            state=state,  # type: ignore[arg-type]
            exit_code=state_attrs.get("ExitCode"),
            started_at=_parse_docker_time(state_attrs.get("StartedAt")),
            finished_at=_parse_docker_time(state_attrs.get("FinishedAt")),
            host_port=host_port,
            error=(state_attrs.get("Error") or None),
        )

    def stream_logs(self, job_id: str, *, follow: bool = False) -> Iterator[str]:
        raise NotImplementedError

    def stop(self, job_id: str, *, timeout: int = 10) -> None:
        try:
            container = self._client.containers.get(job_id)
        except docker.errors.NotFound:
            return
        try:
            container.stop(timeout=timeout)
        except docker.errors.APIError as exc:
            raise DockerJobError(f"stop {job_id} failed: {exc}") from exc

    def wait(self, job_id: str, *, timeout: int | None = None) -> int:
        try:
            container = self._client.containers.get(job_id)
        except docker.errors.NotFound as exc:
            raise DockerJobError(f"{job_id} not found") from exc
        try:
            result = container.wait(timeout=timeout) if timeout is not None else container.wait()
        except requests.exceptions.ReadTimeout as exc:
            raise TimeoutError(f"wait for {job_id} timed out") from exc
        except docker.errors.APIError as exc:
            raise DockerJobError(f"wait for {job_id} failed: {exc}") from exc
        return int(result.get("StatusCode", -1))

    def cleanup_failed(self, *, max_age_hours: int = 24) -> int:
        raise NotImplementedError
