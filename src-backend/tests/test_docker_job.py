"""Unit tests for src/core/docker_job.py value objects."""

import pytest

from src.core.docker_job import (
    DockerJob,
    DockerJobError,
    DockerJobStatus,
    VolumeMount,
)


def test_volume_mount_defaults_to_rw():
    vm = VolumeMount(host_path="/h", container_path="/c")
    assert vm.mode == "rw"


def test_volume_mount_is_frozen():
    vm = VolumeMount(host_path="/h", container_path="/c")
    with pytest.raises(Exception):
        vm.mode = "ro"  # type: ignore[misc]


def test_docker_job_minimal_required_fields():
    job = DockerJob(
        job_id="lf-training-1",
        image="img:tag",
        command=["echo", "hi"],
    )
    assert job.gpus == "all"
    assert job.auto_remove_on_success is True
    assert job.timeout_seconds == 4 * 3600
    assert job.mounts == []
    assert job.ports == {}
    assert job.env == {}
    assert job.log_path == ""


def test_docker_job_status_defaults():
    s = DockerJobStatus(state="pending")
    assert s.exit_code is None
    assert s.started_at is None
    assert s.host_port is None
    assert s.error is None


def test_docker_job_error_is_exception():
    err = DockerJobError("boom")
    assert isinstance(err, Exception)
    assert str(err) == "boom"
