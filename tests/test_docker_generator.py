"""Unit tests for DockerDeploymentEngine."""

from flock.deployment.models import DeploymentDefinition
from flock.deployment.docker import DockerDeploymentEngine


def test_docker_compose_manifest_generation() -> None:
    engine = DockerDeploymentEngine()
    dep = DeploymentDefinition(
        deployment_id="dep-docker",
        name="worker-node",
        namespace="staging",
        image="flock-worker:latest",
        replicas=2,
    )

    compose_content = engine.generate_compose_file(dep)
    assert "version: '3.8'" in compose_content
    assert "image: flock-worker:latest" in compose_content
    assert "replicas: 2" in compose_content
    assert "FLOCK_NAMESPACE=staging" in compose_content


def test_dockerfile_generator_output() -> None:
    from flock.deployment.docker import DockerfileGenerator, DockerHealthCheck
    gen = DockerfileGenerator()
    hc = DockerHealthCheck(test_command=["curl", "-f", "http://localhost:80/health"])
    
    dockerfile = gen.generate_dockerfile(
        base_image="python:3.11-slim",
        working_dir="/app",
        ports=[80, 443],
        healthcheck=hc,
        env_vars={"FLOCK_ENV": "production"},
        labels={"maintainer": "flock-dev"},
        entrypoint=["python", "-m", "flock.cli.main"],
    )

    assert "FROM python:3.11-slim" in dockerfile
    assert "WORKDIR /app" in dockerfile
    assert "EXPOSE 80" in dockerfile
    assert "EXPOSE 443" in dockerfile
    assert "ENV FLOCK_ENV=production" in dockerfile
    assert "LABEL maintainer=flock-dev" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert 'ENTRYPOINT ["python", "-m", "flock.cli.main"]' in dockerfile


def test_docker_validator_rules() -> None:
    from flock.deployment.docker import (
        DockerValidator, DockerContainer, DockerImage,
        DockerRuntimeConfig, DockerNetworkConfig, DockerVolumeConfig
    )

    # 1. Valid container
    img = DockerImage(image_name="flock-worker")
    rc = DockerRuntimeConfig(memory_limit_mb=512, memory_reservation_mb=256)
    net = DockerNetworkConfig(published_ports={8080: 80})
    vol = DockerVolumeConfig(source="/host/data", target="/app/data")
    container = DockerContainer(
        container_name="test-worker",
        image=img,
        runtime_config=rc,
        networks=[net],
        volumes=[vol],
    )

    val_res = DockerValidator.validate_container(container)
    assert val_res.is_valid is True
    assert len(val_res.errors) == 0

    # 2. Invalid port and duplicate mount
    rc_invalid = DockerRuntimeConfig(memory_limit_mb=256, memory_reservation_mb=512)
    net_invalid = DockerNetworkConfig(published_ports={70000: 80})
    vol_dup = [
        DockerVolumeConfig(source="/host/a", target="/app/share"),
        DockerVolumeConfig(source="/host/b", target="/app/share"),
    ]
    container_invalid = DockerContainer(
        container_name="test-worker-invalid",
        image=img,
        runtime_config=rc_invalid,
        networks=[net_invalid],
        volumes=vol_dup,
    )

    val_res_invalid = DockerValidator.validate_container(container_invalid)
    assert val_res_invalid.is_valid is False
    assert any("port mapping" in err for err in val_res_invalid.errors)
    assert any("Duplicate mount target" in err for err in val_res_invalid.errors)
    assert any("Memory reservation cannot exceed" in err for err in val_res_invalid.errors)


def test_compose_engine_and_validation() -> None:
    from flock.deployment.docker import (
        ComposeEngine, ComposeValidator, ComposeService,
        ComposeProject, ComposeDependsOn
    )

    engine = ComposeEngine()
    
    # 1. Test multi-node cluster compose generation
    proj = engine.generate_cluster_compose(
        cluster_name="flock-dev",
        replicas=3,
        image="flock:v1.1.0",
        ports_start=9000,
    )
    
    yaml_content = engine.generate_compose(proj)
    assert "flock-dev-coordinator:" in yaml_content
    assert "flock-dev-worker-1:" in yaml_content
    assert "flock-dev-worker-2:" in yaml_content
    assert "FLOCK_ROLE: coordinator" in yaml_content
    assert "FLOCK_ROLE: worker" in yaml_content
    assert "condition: service_started" in yaml_content

    # 2. Test validator
    val_res = ComposeValidator.validate_project(proj)
    assert val_res.is_valid is True
    assert len(val_res.errors) == 0

    # 3. Test validation errors (missing service dependency, invalid port map)
    invalid_service = ComposeService(
        container_name="bad-node",
        image="nginx",
        ports=["80"],  # Missing colon -> invalid
        depends_on={"missing-node": ComposeDependsOn()},
    )
    invalid_proj = ComposeProject(
        services={"bad-node": invalid_service}
    )
    val_res_invalid = ComposeValidator.validate_project(invalid_proj)
    assert val_res_invalid.is_valid is False
    assert any("depends on missing service" in err for err in val_res_invalid.errors)
    assert any("Invalid port mapping" in err for err in val_res_invalid.errors)
