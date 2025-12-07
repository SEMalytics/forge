"""
Tests for Git workflows, PR creation, and deployment
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from forge.git.repository import ForgeRepository, GitStatus, GitError
from forge.git.commits import (
    ConventionalCommit,
    CommitType,
    CommitStrategy,
    validate_commit_message
)
from forge.integrations.github_client import GitHubClient, GitHubError, PullRequest
from forge.layers.deployment import (
    DeploymentGenerator,
    DeploymentConfig,
    Platform,
    DeploymentError
)


# Git Repository Tests

def test_conventional_commit_format():
    """Test conventional commit formatting"""
    commit = ConventionalCommit(
        type=CommitType.FEAT,
        description="add user authentication",
        scope="auth",
        body="Implemented JWT-based authentication",
        issues=["123"],
        footers={"Reviewed-by": "John Doe"}
    )

    formatted = commit.format()

    assert "feat(auth): add user authentication" in formatted
    assert "Implemented JWT-based authentication" in formatted
    assert "Closes #123" in formatted
    assert "Reviewed-by: John Doe" in formatted


def test_conventional_commit_breaking():
    """Test breaking change commit"""
    commit = ConventionalCommit(
        type=CommitType.FEAT,
        description="redesign API",
        breaking=True,
        footers={"BREAKING CHANGE": "API endpoints changed"}
    )

    formatted = commit.format()

    assert "feat!: redesign API" in formatted
    assert "BREAKING CHANGE: API endpoints changed" in formatted


def test_conventional_commit_parse():
    """Test parsing conventional commit"""
    message = """feat(auth): add user authentication

Implemented JWT-based authentication

Closes #123
Reviewed-by: John Doe"""

    commit = ConventionalCommit.parse(message)

    assert commit is not None
    assert commit.type == CommitType.FEAT
    assert commit.scope == "auth"
    assert commit.description == "add user authentication"
    assert "123" in commit.issues
    assert commit.footers.get("Reviewed-by") == "John Doe"


def test_commit_strategy_from_task():
    """Test creating commit from task"""
    commit = CommitStrategy.from_task(
        task_description="Add database migration",
        files_changed=["migrations/001_create_users.sql", "models/user.py"],
        scope="database"
    )

    assert commit.type in [CommitType.FEAT, CommitType.CHORE]
    assert commit.scope == "database"
    assert "database migration" in commit.description.lower()


def test_commit_strategy_from_fix():
    """Test creating fix commit"""
    commit = CommitStrategy.from_fix(
        issue="456",
        description="fix authentication bug",
        files_changed=["auth/login.py"],
        scope="auth"
    )

    assert commit.type == CommitType.FIX
    assert commit.scope == "auth"
    assert "456" in commit.issues


def test_commit_strategy_infer_type():
    """Test type inference from files"""
    # Test files should infer TEST type
    test_files = ["test_auth.py", "test_user.py", "test_api.py"]
    commit = CommitStrategy.from_changes(test_files)
    assert commit.type == CommitType.TEST

    # Doc files should infer DOCS type
    doc_files = ["README.md", "docs/api.md"]
    commit = CommitStrategy.from_changes(doc_files)
    assert commit.type == CommitType.DOCS


def test_commit_strategy_infer_scope():
    """Test scope inference from file paths"""
    files = ["src/auth/login.py", "src/auth/logout.py"]
    commit = CommitStrategy.from_changes(files)
    assert commit.scope == "auth"


def test_validate_commit_message():
    """Test commit message validation"""
    valid = "feat: add new feature"
    invalid = "added some stuff"

    assert validate_commit_message(valid) is True
    assert validate_commit_message(invalid) is False


def test_commit_merge():
    """Test merging multiple commits"""
    commits = [
        ConventionalCommit(
            type=CommitType.FEAT,
            description="add login",
            scope="auth"
        ),
        ConventionalCommit(
            type=CommitType.FEAT,
            description="add logout",
            scope="auth"
        ),
        ConventionalCommit(
            type=CommitType.FIX,
            description="fix session bug",
            scope="auth"
        )
    ]

    merged = CommitStrategy.merge_commits(commits, "Authentication features")

    assert merged.type == CommitType.FEAT  # Most common
    assert merged.description == "Authentication features"
    assert "add login" in merged.body
    assert "add logout" in merged.body


# GitHub Client Tests

def test_github_client_initialization():
    """Test GitHub client initialization"""
    with patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'}):
        client = GitHubClient("owner/repo")

        assert client.owner == "owner"
        assert client.repo_name == "repo"
        assert client.token == "test_token"


def test_github_client_invalid_repo():
    """Test GitHub client with invalid repo format"""
    with patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'}):
        with pytest.raises(GitHubError):
            GitHubClient("invalid-repo-format")


@patch('requests.Session')
def test_github_create_pr(mock_session):
    """Test creating GitHub PR"""
    # Mock response
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "number": 42,
        "title": "Test PR",
        "url": "https://api.github.com/repos/owner/repo/pulls/42",
        "html_url": "https://github.com/owner/repo/pull/42",
        "state": "open",
        "head": {"ref": "feature-branch"},
        "base": {"ref": "main"}
    }
    mock_response.raise_for_status = Mock()

    mock_session_instance = Mock()
    mock_session_instance.request.return_value = mock_response
    mock_session.return_value = mock_session_instance

    with patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'}):
        client = GitHubClient("owner/repo")

        pr = client.create_pr(
            title="Test PR",
            body="Test description",
            head="feature-branch",
            base="main"
        )

        assert pr.number == 42
        assert pr.title == "Test PR"
        assert pr.state == "open"


@patch('requests.Session')
def test_github_create_pr_with_checklist(mock_session):
    """Test creating PR with checklist"""
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "number": 43,
        "title": "Test PR",
        "url": "https://api.github.com/repos/owner/repo/pulls/43",
        "html_url": "https://github.com/owner/repo/pull/43",
        "state": "open",
        "head": {"ref": "feature-branch"},
        "base": {"ref": "main"}
    }
    mock_response.raise_for_status = Mock()

    mock_session_instance = Mock()
    mock_session_instance.request.return_value = mock_response
    mock_session.return_value = mock_session_instance

    with patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'}):
        client = GitHubClient("owner/repo")

        pr = client.create_pr_with_checklist(
            title="Test PR",
            description="Test description",
            head="feature-branch",
            base="main",
            checklist_items=["Review code", "Test locally"],
            issues=["123", "456"],
            labels=["bug", "urgent"]
        )

        assert pr.number == 43


# Deployment Tests

def test_deployment_config_creation():
    """Test deployment config creation"""
    config = DeploymentConfig(
        platform=Platform.FLYIO,
        project_name="test-app",
        runtime="python",
        entry_point="app.py",
        environment_vars={"PORT": "8080"},
        port=8080
    )

    assert config.platform == Platform.FLYIO
    assert config.project_name == "test-app"
    assert config.runtime == "python"


def test_deployment_generator_initialization():
    """Test deployment generator initialization"""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = DeploymentGenerator(Path(tmpdir))
        assert generator.project_path == Path(tmpdir)


def test_deployment_generator_invalid_path():
    """Test deployment generator with invalid path"""
    with pytest.raises(DeploymentError):
        DeploymentGenerator(Path("/nonexistent/path"))


def test_generate_dockerfile_python():
    """Test Dockerfile generation for Python"""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = DeploymentGenerator(Path(tmpdir))

        config = DeploymentConfig(
            platform=Platform.DOCKER,
            project_name="test-app",
            runtime="python",
            entry_point="app.py",
            environment_vars={},
            start_command="python app.py",
            port=8080
        )

        dockerfile = generator._generate_dockerfile(config, Path(tmpdir))

        assert dockerfile.exists()
        content = dockerfile.read_text()

        assert "FROM python:" in content
        assert "EXPOSE 8080" in content
        assert "python app.py" in content


def test_generate_dockerfile_node():
    """Test Dockerfile generation for Node.js"""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = DeploymentGenerator(Path(tmpdir))

        config = DeploymentConfig(
            platform=Platform.DOCKER,
            project_name="test-app",
            runtime="node",
            entry_point="index.js",
            environment_vars={},
            start_command="node index.js",
            port=3000
        )

        dockerfile = generator._generate_dockerfile(config, Path(tmpdir))

        content = dockerfile.read_text()

        assert "FROM node:" in content
        assert "EXPOSE 3000" in content
        assert "node index.js" in content


def test_generate_docker_compose():
    """Test docker-compose.yml generation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = DeploymentGenerator(Path(tmpdir))

        config = DeploymentConfig(
            platform=Platform.DOCKER,
            project_name="test-app",
            runtime="python",
            entry_point="app.py",
            environment_vars={"DEBUG": "true"},
            port=8080
        )

        files = generator._generate_docker(config, Path(tmpdir))

        compose_file = Path(tmpdir) / "docker-compose.yml"
        assert compose_file in files
        assert compose_file.exists()


def test_generate_flyio_config():
    """Test fly.toml generation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = DeploymentGenerator(Path(tmpdir))

        config = DeploymentConfig(
            platform=Platform.FLYIO,
            project_name="test-app",
            runtime="python",
            entry_point="app.py",
            environment_vars={"ENV": "production"},
            port=8080,
            region="lax"
        )

        files = generator._generate_flyio(config, Path(tmpdir))

        fly_toml = Path(tmpdir) / "fly.toml"
        assert fly_toml in files
        assert fly_toml.exists()

        content = fly_toml.read_text()
        assert "test-app" in content
        assert "lax" in content


def test_generate_vercel_config():
    """Test vercel.json generation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = DeploymentGenerator(Path(tmpdir))

        config = DeploymentConfig(
            platform=Platform.VERCEL,
            project_name="test-app",
            runtime="node",
            entry_point="api/index.js",
            environment_vars={"NODE_ENV": "production"},
            port=3000
        )

        files = generator._generate_vercel(config, Path(tmpdir))

        vercel_json = Path(tmpdir) / "vercel.json"
        assert vercel_json in files
        assert vercel_json.exists()


def test_generate_kubernetes_manifests():
    """Test Kubernetes manifest generation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = DeploymentGenerator(Path(tmpdir))

        config = DeploymentConfig(
            platform=Platform.KUBERNETES,
            project_name="test-app",
            runtime="python",
            entry_point="app.py",
            environment_vars={"REPLICAS": "3"},
            port=8080
        )

        files = generator._generate_kubernetes(config, Path(tmpdir))

        k8s_dir = Path(tmpdir) / "k8s"
        assert k8s_dir.exists()

        deployment_file = k8s_dir / "deployment.yaml"
        service_file = k8s_dir / "service.yaml"

        assert deployment_file in files
        assert service_file in files


def test_generate_aws_lambda_config():
    """Test AWS Lambda SAM template generation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = DeploymentGenerator(Path(tmpdir))

        config = DeploymentConfig(
            platform=Platform.AWS_LAMBDA,
            project_name="test-function",
            runtime="python",
            entry_point="lambda_handler",
            environment_vars={"STAGE": "prod"},
            port=8080
        )

        files = generator._generate_aws_lambda(config, Path(tmpdir))

        template_file = Path(tmpdir) / "template.yaml"
        assert template_file in files
        assert template_file.exists()


# Integration Tests

def test_end_to_end_commit_workflow():
    """Test complete commit workflow"""
    # Create commit
    commit = CommitStrategy.from_task(
        task_description="Add user registration feature",
        files_changed=["auth/register.py", "models/user.py"],
        scope="auth"
    )

    # Format commit message
    message = commit.format()

    # Validate
    assert validate_commit_message(message)

    # Parse back
    parsed = ConventionalCommit.parse(message)
    assert parsed is not None
    assert parsed.scope == "auth"


def test_deployment_complete_workflow():
    """Test complete deployment workflow"""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = DeploymentGenerator(Path(tmpdir))

        # Generate for multiple platforms
        platforms = [
            Platform.DOCKER,
            Platform.FLYIO,
            Platform.VERCEL
        ]

        for platform in platforms:
            config = DeploymentConfig(
                platform=platform,
                project_name="test-app",
                runtime="python",
                entry_point="app.py",
                environment_vars={"ENV": "test"},
                port=8080
            )

            files = generator.generate_configs(config)
            assert len(files) > 0


def test_platform_specific_configurations():
    """Test platform-specific configuration details"""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = DeploymentGenerator(Path(tmpdir))

        # Test Python runtime
        config = DeploymentConfig(
            platform=Platform.DOCKER,
            project_name="python-app",
            runtime="python",
            entry_point="main.py",
            environment_vars={},
            port=8000
        )

        files = generator.generate_configs(config)
        dockerfile = Path(tmpdir) / "Dockerfile"
        content = dockerfile.read_text()

        assert "python:" in content
        assert "requirements.txt" in content
