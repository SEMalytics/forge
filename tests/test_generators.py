"""
Tests for code generation system
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from forge.generators.base import (
    GeneratorBackend,
    GenerationContext,
    GenerationResult,
    CodeGenerator,
    GeneratorError
)
from forge.generators.factory import GeneratorFactory
from forge.generators.codegen_api import CodeGenAPIGenerator
from forge.generators.claude_code import ClaudeCodeGenerator


# Fixtures

@pytest.fixture
def sample_context():
    """Create sample generation context"""
    return GenerationContext(
        task_id="task-001",
        specification="Build a REST API endpoint for user authentication",
        project_context="User management system with FastAPI",
        tech_stack=["Python", "FastAPI", "PostgreSQL"],
        dependencies=["task-000"],
        knowledgeforge_patterns=["API_Security.md", "Authentication.md"]
    )


@pytest.fixture
def sample_result():
    """Create sample generation result"""
    return GenerationResult(
        success=True,
        files={
            "api/auth.py": "def authenticate(user): pass",
            "tests/test_auth.py": "def test_auth(): pass"
        },
        duration_seconds=5.2,
        tokens_used=1500
    )


# Base Class Tests

def test_generation_context_creation(sample_context):
    """Test creating generation context"""
    assert sample_context.task_id == "task-001"
    assert "authentication" in sample_context.specification.lower()
    assert "Python" in sample_context.tech_stack
    assert len(sample_context.knowledgeforge_patterns) == 2


def test_generation_context_to_dict(sample_context):
    """Test context serialization"""
    data = sample_context.to_dict()

    assert data["task_id"] == "task-001"
    assert "specification" in data
    assert "tech_stack" in data


def test_generation_result_creation(sample_result):
    """Test creating generation result"""
    assert sample_result.success is True
    assert len(sample_result.files) == 2
    assert sample_result.duration_seconds > 0


def test_generation_result_to_dict(sample_result):
    """Test result serialization"""
    data = sample_result.to_dict()

    assert data["success"] is True
    assert data["file_count"] == 2
    assert "generated_at" in data


def test_generation_result_merge():
    """Test merging results"""
    result1 = GenerationResult(
        success=True,
        files={"file1.py": "code1"},
        duration_seconds=5.0,
        tokens_used=1000
    )

    result2 = GenerationResult(
        success=True,
        files={"file2.py": "code2"},
        duration_seconds=3.0,
        tokens_used=500
    )

    merged = result1.merge(result2)

    assert merged.success is True
    assert len(merged.files) == 2
    assert merged.duration_seconds == 8.0
    assert merged.tokens_used == 1500


def test_generator_backend_enum():
    """Test generator backend enum"""
    assert GeneratorBackend.CODEGEN_API.value == "codegen_api"
    assert GeneratorBackend.CLAUDE_CODE.value == "claude_code"


# Factory Tests

def test_factory_create_codegen_api():
    """Test creating CodeGen API generator"""
    generator = GeneratorFactory.create(
        GeneratorBackend.CODEGEN_API,
        api_key="test-key",
        org_id="test-org"
    )

    assert isinstance(generator, CodeGenAPIGenerator)
    assert generator.api_key == "test-key"


def test_factory_create_codegen_api_no_org():
    """Test creating CodeGen API generator without org_id"""
    generator = GeneratorFactory.create(
        GeneratorBackend.CODEGEN_API,
        api_key="test-key"
    )

    assert isinstance(generator, CodeGenAPIGenerator)
    assert generator.org_id is None


def test_factory_create_claude_code():
    """Test creating Claude Code generator"""
    generator = GeneratorFactory.create(
        GeneratorBackend.CLAUDE_CODE,
        workspace_dir=Path("/tmp/test")
    )

    assert isinstance(generator, ClaudeCodeGenerator)


def test_factory_create_invalid_backend():
    """Test creating with invalid backend"""
    with pytest.raises(GeneratorError):
        GeneratorFactory.create("invalid_backend")


def test_factory_create_from_config():
    """Test creating from config dictionary"""
    config = {
        "api_key": "test-key",
        "org_id": None
    }

    generator = GeneratorFactory.create_from_config("codegen_api", config)

    assert isinstance(generator, CodeGenAPIGenerator)


def test_factory_get_available_backends():
    """Test getting available backends"""
    backends = GeneratorFactory.get_available_backends()

    assert "codegen_api" in backends
    assert "claude_code" in backends


@patch.dict('os.environ', {'CODEGEN_API_KEY': 'test-key'})
def test_factory_detect_best_backend_api():
    """Test detecting CodeGen API backend"""
    backend = GeneratorFactory.detect_best_backend()

    assert backend == GeneratorBackend.CODEGEN_API


# CodeGen API Generator Tests

def test_codegen_api_initialization():
    """Test CodeGen API generator initialization"""
    generator = CodeGenAPIGenerator(
        api_key="test-key",
        org_id="test-org"
    )

    assert generator.api_key == "test-key"
    assert generator.org_id == "test-org"


def test_codegen_api_no_api_key():
    """Test CodeGen API without API key"""
    with pytest.raises(GeneratorError, match="API key is required"):
        CodeGenAPIGenerator(api_key="")


def test_codegen_api_build_headers():
    """Test building API headers"""
    generator = CodeGenAPIGenerator(
        api_key="test-key",
        org_id="test-org"
    )

    headers = generator._build_headers()

    assert "Authorization" in headers
    assert headers["Authorization"] == "Bearer test-key"
    assert headers["X-Organization-ID"] == "test-org"


def test_codegen_api_build_prompt(sample_context):
    """Test building generation prompt"""
    generator = CodeGenAPIGenerator(api_key="test-key")

    prompt = generator._build_prompt(sample_context)

    assert "authentication" in prompt.lower()
    assert "Python" in prompt
    assert "FastAPI" in prompt
    assert "API_Security.md" in prompt


def test_codegen_api_parse_files():
    """Test parsing files from generated text"""
    generator = CodeGenAPIGenerator(api_key="test-key")

    generated_text = """
### api/auth.py
```python
def authenticate(user):
    return True
```

### tests/test_auth.py
```python
def test_auth():
    assert True
```
"""

    files = generator._parse_files(generated_text)

    assert len(files) == 2
    assert "api/auth.py" in files
    assert "tests/test_auth.py" in files
    assert "authenticate" in files["api/auth.py"]


def test_codegen_api_estimate_duration(sample_context):
    """Test duration estimation"""
    generator = CodeGenAPIGenerator(api_key="test-key")

    duration = generator.estimate_duration(sample_context)

    assert duration > 0
    assert duration < 300  # Less than timeout


def test_codegen_api_supports_parallel():
    """Test parallel support"""
    generator = CodeGenAPIGenerator(api_key="test-key")

    assert generator.supports_parallel() is True


def test_codegen_api_max_context_tokens():
    """Test max context tokens"""
    generator = CodeGenAPIGenerator(api_key="test-key")

    max_tokens = generator.max_context_tokens()

    assert max_tokens > 0


# Claude Code Generator Tests

def test_claude_code_initialization(tmp_path):
    """Test Claude Code generator initialization"""
    generator = ClaudeCodeGenerator(workspace_dir=tmp_path)

    assert generator.workspace_dir == tmp_path
    assert tmp_path.exists()


def test_claude_code_create_workspace(tmp_path, sample_context):
    """Test workspace creation"""
    generator = ClaudeCodeGenerator(workspace_dir=tmp_path)

    workspace = generator._create_workspace(sample_context)

    assert workspace.exists()
    assert workspace.name == "task-001"


def test_claude_code_create_specification(tmp_path, sample_context):
    """Test specification file creation"""
    generator = ClaudeCodeGenerator(workspace_dir=tmp_path)

    workspace = generator._create_workspace(sample_context)
    spec_file = generator._create_specification(workspace, sample_context)

    assert spec_file.exists()
    assert spec_file.name == "SPEC.md"

    content = spec_file.read_text()
    assert "task-001" in content
    assert "authentication" in content.lower()
    assert "Python" in content


def test_claude_code_collect_files(tmp_path, sample_context):
    """Test collecting generated files"""
    generator = ClaudeCodeGenerator(workspace_dir=tmp_path)

    workspace = generator._create_workspace(sample_context)

    # Create test files
    (workspace / "api").mkdir()
    (workspace / "api" / "auth.py").write_text("def auth(): pass")
    (workspace / "test.py").write_text("def test(): pass")

    files = generator._collect_files(workspace)

    assert len(files) == 2
    assert "api/auth.py" in files or "api\\auth.py" in files  # Handle Windows paths


def test_claude_code_supports_parallel():
    """Test parallel support (should be False)"""
    generator = ClaudeCodeGenerator()

    assert generator.supports_parallel() is False


def test_claude_code_max_context_tokens():
    """Test max context tokens"""
    generator = ClaudeCodeGenerator()

    max_tokens = generator.max_context_tokens()

    assert max_tokens == 200000  # Claude's extended context


# Validation Tests

def test_validate_context_valid(sample_context):
    """Test valid context validation"""
    generator = CodeGenAPIGenerator(api_key="test-key")

    assert generator.validate_context(sample_context) is True


def test_validate_context_no_task_id():
    """Test validation with missing task_id"""
    generator = CodeGenAPIGenerator(api_key="test-key")

    context = GenerationContext(
        task_id="",
        specification="test",
        project_context="test"
    )

    with pytest.raises(GeneratorError, match="task_id is required"):
        generator.validate_context(context)


def test_validate_context_no_specification():
    """Test validation with missing specification"""
    generator = CodeGenAPIGenerator(api_key="test-key")

    context = GenerationContext(
        task_id="task-001",
        specification="",
        project_context="test"
    )

    with pytest.raises(GeneratorError, match="specification is required"):
        generator.validate_context(context)


# Integration Test (mock)

@pytest.mark.asyncio
async def test_codegen_api_generate_mock(sample_context):
    """Test CodeGen API generation with mocked HTTP"""
    generator = CodeGenAPIGenerator(api_key="test-key")

    # Mock HTTP response
    with patch.object(generator.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "completion": """
### api/auth.py
```python
def authenticate(user):
    return True
```
""",
            "usage": {"total_tokens": 500}
        }
        mock_post.return_value = mock_response

        result = await generator.generate(sample_context)

        assert result.success is True
        assert len(result.files) > 0
        assert result.tokens_used == 500
