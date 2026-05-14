"""Abstract port for Docker container lifecycle control.

The concrete implementation lives in `src/adapters/docker_adapter.py`.
Business services depend on this port so they can be unit-tested with stubs.
"""

import abc
from collections.abc import Iterator

from src.core.docker_job import DockerJob, DockerJobStatus


class DockerClient(abc.ABC):
    @abc.abstractmethod
    def submit(self, job: DockerJob) -> str:
        """Start a container for the job, return Docker container id.

        If a container with the same name already exists, force-remove it
        before starting. Raises DockerJobError on any failure.
        """

    @abc.abstractmethod
    def status(self, job_id: str) -> DockerJobStatus:
        """Return current state of the container by job_id.

        If no container with that name exists, return state='missing'.
        """

    @abc.abstractmethod
    def stream_logs(self, job_id: str, *, follow: bool = False) -> Iterator[str]:
        """Yield log lines from the container.

        When follow=True, blocks until the container exits.
        """

    @abc.abstractmethod
    def stop(self, job_id: str, *, timeout: int = 10) -> None:
        """Gracefully stop the container. Silently no-op if missing."""

    @abc.abstractmethod
    def wait(self, job_id: str, *, timeout: int | None = None) -> int:
        """Block until the container exits. Returns exit_code.

        Raises TimeoutError if timeout is reached.
        """

    @abc.abstractmethod
    def cleanup_failed(self, *, max_age_hours: int = 24) -> int:
        """Remove failed containers older than max_age_hours.

        "Failed" = state=exited AND exit_code != 0.
        Only containers whose name starts with "lf-" are considered
        (avoids removing unrelated containers).
        Returns the number of containers removed.
        """
