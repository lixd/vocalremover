# ci-cd-pipeline Specification

## Purpose
TBD - created by archiving change docker-ci-docs. Update Purpose after archive.
## Requirements
### Requirement: Automated Docker image build on commit
The system SHALL provide a GitHub Actions workflow at `.github/workflows/ci.yml` that triggers on every push to any branch and builds both backend and frontend Docker images.

#### Scenario: Push triggers build
- **WHEN** developer pushes a commit to any branch
- **THEN** GitHub Actions workflow SHALL trigger and build Docker images

### Requirement: Image tagging by branch name
The system SHALL tag built images with the branch name. For pushes to `main` or `master` branch, the image SHALL ALSO be tagged with `latest`.

#### Scenario: Feature branch push
- **WHEN** push occurs on branch `feature/audio-split`
- **THEN** image SHALL be tagged as `vocalremover:feature-audio-split`

#### Scenario: Main branch push
- **WHEN** push occurs on `main` branch
- **THEN** image SHALL be tagged as both `vocalremover:main` and `vocalremover:latest`

### Requirement: Docker Hub push
The system SHALL authenticate to Docker Hub using `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` GitHub Secrets, then push built images to Docker Hub under the `vocalremover` repository.

#### Scenario: Successful push to Docker Hub
- **WHEN** workflow builds images successfully
- **THEN** images SHALL be pushed to Docker Hub with appropriate tags

#### Scenario: Missing secrets
- **WHEN** `DOCKERHUB_USERNAME` or `DOCKERHUB_TOKEN` secrets are not configured
- **THEN** workflow SHALL fail with a clear error message indicating missing credentials

### Requirement: Branch name sanitization
The system SHALL sanitize branch names for use as Docker tags by replacing `/` with `-` and truncating to valid tag format.

#### Scenario: Slash in branch name
- **WHEN** branch name is `feature/fix-bpm`
- **THEN** Docker tag SHALL be `vocalremover:feature-fix-bpm`

