# Deployment Changelog

All notable changes implemented for Milestone C are documented below.

## [1.1.0] - 2026-07-26

### Added
- Docker compose manifest generator in `flock.deployment.docker`.
- Kubernetes manifest generator in `flock.deployment.kubernetes`.
- Deployment controller manager `DeploymentController`.
- Rollout and Rollback planners.
- Unit and integration tests verifying all Docker and Kubernetes generation flows.
