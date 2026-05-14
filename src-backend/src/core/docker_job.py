"""Docker job value objects used across the Docker control adapter.

Boundary: these types carry NO LlamaFactory-specific semantics. They describe
a generic containerized job (image + command + mounts + GPUs + ports).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class VolumeMount:
    host_path: str
    container_path: str
    mode: Literal["ro", "rw"] = "rw"


@dataclass(frozen=True)
class DockerJob:
    job_id: str
    image: str
    command: list[str]
    env: dict[str, str] = field(default_factory=dict)
    mounts: list[VolumeMount] = field(default_factory=list)
    gpus: str = "all"
    ports: dict[int, int] = field(default_factory=dict)
    auto_remove_on_success: bool = True
    timeout_seconds: int = 4 * 3600
    log_path: str = ""


@dataclass
class DockerJobStatus:
    state: Literal["pending", "running", "exited", "removed", "missing"]
    exit_code: int | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    host_port: int | None = None
    error: str | None = None


class DockerJobError(Exception):
    """Unified exception for Docker operation failures.

    Wraps docker-py exceptions so upper layers never depend on docker.errors.*.
    """
