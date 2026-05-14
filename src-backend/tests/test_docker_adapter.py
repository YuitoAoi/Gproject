"""Unit tests for src/adapters/docker_adapter.py.

All Docker SDK calls are mocked; no real Docker daemon required.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.docker_job import DockerJob, VolumeMount


@pytest.fixture
def fake_docker():
    """Patch docker.from_env() so the adapter sees a fully-mocked SDK client."""
    with patch("src.adapters.docker_adapter.docker.from_env") as from_env:
        client = MagicMock()
        from_env.return_value = client
        yield client


def test_submit_passes_expected_args_to_containers_run(fake_docker):
    from src.adapters.docker_adapter import DockerClientAdapter

    fake_docker.containers.get.side_effect = _not_found()
    fake_docker.images.get.return_value = MagicMock()
    container = MagicMock()
    container.id = "abc123"
    fake_docker.containers.run.return_value = container

    adapter = DockerClientAdapter()
    job = DockerJob(
        job_id="lf-training-1",
        image="hiyouga/llamafactory:latest",
        command=["llamafactory-cli", "train", "/apps/data/cfg.yaml"],
        mounts=[VolumeMount(host_path="/h/data", container_path="/apps/data", mode="rw")],
        ports={8000: 18000},
        env={"FOO": "bar"},
    )
    cid = adapter.submit(job)

    assert cid == "abc123"
    kwargs = fake_docker.containers.run.call_args.kwargs
    assert kwargs["image"] == "hiyouga/llamafactory:latest"
    assert kwargs["name"] == "lf-training-1"
    assert kwargs["command"] == ["llamafactory-cli", "train", "/apps/data/cfg.yaml"]
    assert kwargs["environment"] == {"FOO": "bar"}
    assert kwargs["detach"] is True
    assert kwargs["remove"] is False
    # Ports formatted as Docker expects ("8000/tcp" -> 18000)
    assert kwargs["ports"] == {"8000/tcp": 18000}
    # One bind mount, rw
    [mount] = kwargs["mounts"]
    assert mount["Source"] == "/h/data"
    assert mount["Target"] == "/apps/data"
    assert mount["Type"] == "bind"
    assert mount["ReadOnly"] is False
    # GPU all -> single DeviceRequest with count=-1
    [dev_req] = kwargs["device_requests"]
    assert dev_req["Count"] == -1
    assert dev_req["Capabilities"] == [["gpu"]]


def _not_found():
    import docker.errors
    return docker.errors.NotFound("not found")


def test_submit_force_removes_existing_container_with_same_name(fake_docker):
    from src.adapters.docker_adapter import DockerClientAdapter

    existing = MagicMock()
    fake_docker.containers.get.return_value = existing
    fake_docker.images.get.return_value = MagicMock()
    fake_docker.containers.run.return_value = MagicMock(id="new")

    DockerClientAdapter().submit(_minimal_job())

    existing.remove.assert_called_once_with(force=True)


def test_submit_pulls_image_when_missing(fake_docker):
    from src.adapters.docker_adapter import DockerClientAdapter
    import docker.errors as derr

    fake_docker.containers.get.side_effect = derr.NotFound("nf")
    fake_docker.images.get.side_effect = derr.ImageNotFound("nope")
    fake_docker.containers.run.return_value = MagicMock(id="new")

    DockerClientAdapter().submit(_minimal_job())

    fake_docker.images.pull.assert_called_once_with("img:tag")


def test_submit_translates_api_error_to_docker_job_error(fake_docker):
    from src.adapters.docker_adapter import DockerClientAdapter
    from src.core.docker_job import DockerJobError
    import docker.errors as derr

    fake_docker.containers.get.side_effect = derr.NotFound("nf")
    fake_docker.images.get.return_value = MagicMock()
    fake_docker.containers.run.side_effect = derr.APIError("boom")

    with pytest.raises(DockerJobError) as exc_info:
        DockerClientAdapter().submit(_minimal_job())
    assert "lf-training-1" in str(exc_info.value)


def _minimal_job():
    from src.core.docker_job import DockerJob
    return DockerJob(
        job_id="lf-training-1",
        image="img:tag",
        command=["true"],
    )


@pytest.mark.parametrize("docker_status,expected_state", [
    ("created", "pending"),
    ("running", "running"),
    ("exited", "exited"),
    ("dead", "exited"),
    ("removing", "removed"),
    ("paused", "running"),
    ("restarting", "running"),
])
def test_status_maps_container_state(fake_docker, docker_status, expected_state):
    from src.adapters.docker_adapter import DockerClientAdapter

    container = MagicMock()
    container.status = docker_status
    container.attrs = {
        "State": {
            "ExitCode": 0,
            "StartedAt": "2026-05-13T10:00:00.000000000Z",
            "FinishedAt": "0001-01-01T00:00:00Z",
            "Error": "",
        },
        "NetworkSettings": {"Ports": {}},
    }
    fake_docker.containers.get.return_value = container

    result = DockerClientAdapter().status("lf-training-1")
    assert result.state == expected_state


def test_status_returns_missing_when_container_not_found(fake_docker):
    from src.adapters.docker_adapter import DockerClientAdapter
    import docker.errors as derr

    fake_docker.containers.get.side_effect = derr.NotFound("nf")
    result = DockerClientAdapter().status("lf-training-1")
    assert result.state == "missing"


def test_status_extracts_host_port_from_network_settings(fake_docker):
    from src.adapters.docker_adapter import DockerClientAdapter

    container = MagicMock()
    container.status = "running"
    container.attrs = {
        "State": {
            "ExitCode": 0,
            "StartedAt": "2026-05-13T10:00:00.000000000Z",
            "FinishedAt": "0001-01-01T00:00:00Z",
            "Error": "",
        },
        "NetworkSettings": {
            "Ports": {"8000/tcp": [{"HostIp": "0.0.0.0", "HostPort": "18000"}]},
        },
    }
    fake_docker.containers.get.return_value = container

    result = DockerClientAdapter().status("lf-training-1")
    assert result.host_port == 18000
