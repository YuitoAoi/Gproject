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
