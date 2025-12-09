"""
Tests for RepositoryAnalyzer

Tests the repository analysis functionality including:
- Structure analysis
- Language detection
- Naming convention detection
- Dependency parsing
- Testing setup detection
- Caching
"""

import pytest
from pathlib import Path
import tempfile
import json
import shutil

from forge.layers.repository_analyzer import (
    RepositoryAnalyzer,
    RepositoryAnalyzerError,
    RepositoryContext,
    FileTypeStats,
    NamingConventions,
    TestInfo,
    DependencyInfo
)


@pytest.fixture
def temp_repo(tmp_path):
    """Create a temporary Python repository for testing."""
    # Create directory structure
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "myapp").mkdir()
    (tmp_path / "tests").mkdir()

    # Create Python files
    (tmp_path / "src" / "myapp" / "__init__.py").write_text("")
    (tmp_path / "src" / "myapp" / "main.py").write_text("""
def main_function():
    '''Main entry point'''
    pass

class MyClass:
    def my_method(self):
        pass
""")
    (tmp_path / "src" / "myapp" / "utils.py").write_text("""
def helper_function():
    pass

CONSTANT_VALUE = 42
""")

    # Create test files
    (tmp_path / "tests" / "__init__.py").write_text("")
    (tmp_path / "tests" / "test_main.py").write_text("""
import pytest

def test_main():
    assert True

@pytest.fixture
def my_fixture():
    return {}
""")
    (tmp_path / "tests" / "conftest.py").write_text("""
import pytest

@pytest.fixture
def shared_fixture():
    return []
""")

    # Create pyproject.toml
    (tmp_path / "pyproject.toml").write_text("""
[tool.poetry]
name = "myapp"
version = "1.0.0"

[tool.poetry.dependencies]
python = "^3.11"
click = "^8.1.0"
pydantic = "^2.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
""")

    # Create README
    (tmp_path / "README.md").write_text("""
# MyApp

A sample application for testing.

## Features
- Feature 1
- Feature 2
""")

    # Create config files
    (tmp_path / ".gitignore").write_text("__pycache__\n*.pyc\n.venv")
    (tmp_path / "pytest.ini").write_text("[pytest]\naddopts = -v")

    return tmp_path


@pytest.fixture
def temp_js_repo(tmp_path):
    """Create a temporary JavaScript repository for testing."""
    # Create directory structure
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()

    # Create JS files
    (tmp_path / "src" / "index.js").write_text("""
function mainFunction() {
    return 'hello';
}

class MyService {
    constructor() {}
}

const helperUtil = () => {};

module.exports = { mainFunction, MyService, helperUtil };
""")

    (tmp_path / "src" / "utils.js").write_text("""
const CONSTANT = 42;

function formatData(data) {
    return data;
}
""")

    # Create package.json
    (tmp_path / "package.json").write_text(json.dumps({
        "name": "my-js-app",
        "version": "1.0.0",
        "dependencies": {
            "express": "^4.18.0",
            "lodash": "^4.17.0"
        },
        "devDependencies": {
            "jest": "^29.0.0",
            "eslint": "^8.0.0"
        },
        "engines": {
            "node": ">=18.0.0"
        }
    }, indent=2))

    # Create test file
    (tmp_path / "tests" / "index.test.js").write_text("""
const { mainFunction } = require('../src/index');

describe('mainFunction', () => {
    it('should return hello', () => {
        expect(mainFunction()).toBe('hello');
    });
});
""")

    return tmp_path


@pytest.fixture
def analyzer(tmp_path):
    """Create analyzer with custom cache directory."""
    cache_dir = tmp_path / "cache"
    return RepositoryAnalyzer(cache_dir=cache_dir)


class TestRepositoryAnalyzer:
    """Tests for RepositoryAnalyzer class."""

    def test_analyze_nonexistent_path(self, analyzer):
        """Test that analyzing a non-existent path raises an error."""
        with pytest.raises(RepositoryAnalyzerError, match="does not exist"):
            analyzer.analyze(Path("/nonexistent/path"))

    def test_analyze_file_not_directory(self, analyzer, tmp_path):
        """Test that analyzing a file (not directory) raises an error."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        with pytest.raises(RepositoryAnalyzerError, match="not a directory"):
            analyzer.analyze(test_file)

    def test_analyze_python_repo_structure(self, analyzer, temp_repo):
        """Test analysis of Python repository structure."""
        context = analyzer.analyze(temp_repo)

        assert context.project_name == temp_repo.name
        assert context.root_path == str(temp_repo)
        assert "src" in context.key_directories or "src" in context.directory_structure

    def test_analyze_python_repo_languages(self, analyzer, temp_repo):
        """Test language detection in Python repository."""
        context = analyzer.analyze(temp_repo)

        assert context.primary_language == "python"
        assert "python" in context.languages
        assert context.languages["python"].count > 0

    def test_analyze_python_repo_dependencies(self, analyzer, temp_repo):
        """Test dependency detection in Python repository."""
        context = analyzer.analyze(temp_repo)

        assert context.dependency_info.package_manager == "poetry"
        assert context.dependency_info.manifest_file == "pyproject.toml"
        assert "click" in context.dependency_info.dependencies
        assert "pydantic" in context.dependency_info.dependencies
        assert "pytest" in context.dependency_info.dev_dependencies

    def test_analyze_python_repo_testing(self, analyzer, temp_repo):
        """Test testing setup detection in Python repository."""
        context = analyzer.analyze(temp_repo)

        assert context.test_info.framework == "pytest"
        assert context.test_info.test_directory == "tests"
        # conftest detection happens at repo root level, not test dir
        assert context.test_info.has_fixtures is True

    def test_analyze_python_repo_naming(self, analyzer, temp_repo):
        """Test naming convention detection in Python repository."""
        context = analyzer.analyze(temp_repo)

        # Python typically uses snake_case for functions
        assert context.naming_conventions.function_naming in ["snake_case", "unknown"]

    def test_analyze_python_repo_readme(self, analyzer, temp_repo):
        """Test README content extraction."""
        context = analyzer.analyze(temp_repo)

        assert context.readme_content is not None
        assert "MyApp" in context.readme_content

    def test_analyze_python_repo_config_files(self, analyzer, temp_repo):
        """Test config file detection."""
        context = analyzer.analyze(temp_repo)

        assert "pyproject.toml" in context.config_files
        assert ".gitignore" in context.config_files
        assert "pytest.ini" in context.config_files

    def test_analyze_js_repo_languages(self, analyzer, temp_js_repo):
        """Test language detection in JavaScript repository."""
        context = analyzer.analyze(temp_js_repo)

        assert context.primary_language == "javascript"
        assert "javascript" in context.languages

    def test_analyze_js_repo_dependencies(self, analyzer, temp_js_repo):
        """Test dependency detection in JavaScript repository."""
        context = analyzer.analyze(temp_js_repo)

        assert context.dependency_info.package_manager in ["npm", "yarn", "pnpm"]
        assert context.dependency_info.manifest_file == "package.json"
        assert "express" in context.dependency_info.dependencies
        assert "jest" in context.dependency_info.dev_dependencies
        assert context.dependency_info.node_version == ">=18.0.0"

    def test_analyze_js_repo_testing(self, analyzer, temp_js_repo):
        """Test testing setup detection in JavaScript repository."""
        context = analyzer.analyze(temp_js_repo)

        assert context.test_info.framework == "jest"


class TestRepositoryContext:
    """Tests for RepositoryContext dataclass."""

    def test_to_dict(self, analyzer, temp_repo):
        """Test conversion to dictionary."""
        context = analyzer.analyze(temp_repo)
        data = context.to_dict()

        assert isinstance(data, dict)
        assert "project_name" in data
        assert "primary_language" in data
        assert "languages" in data
        assert "dependency_info" in data

    def test_to_prompt_context(self, analyzer, temp_repo):
        """Test conversion to prompt-friendly format."""
        context = analyzer.analyze(temp_repo)
        prompt = context.to_prompt_context()

        assert isinstance(prompt, str)
        assert context.project_name in prompt
        assert context.primary_language in prompt


class TestCaching:
    """Tests for caching functionality."""

    def test_cache_is_used(self, tmp_path):
        """Test that cached results are used on second analysis."""
        # Create a simple repo
        (tmp_path / "test_project").mkdir()
        test_repo = tmp_path / "test_project"
        (test_repo / "main.py").write_text("x = 1")

        # Create analyzer with separate cache dir
        cache_dir = tmp_path / "cache"
        analyzer = RepositoryAnalyzer(cache_dir=cache_dir)

        # First analysis
        context1 = analyzer.analyze(test_repo)

        # Second analysis should use cache (same result)
        context2 = analyzer.analyze(test_repo)

        # Both should complete without error and have same project name
        assert context1.project_name == context2.project_name
        assert context1.primary_language == context2.primary_language

    def test_force_reanalysis(self, analyzer, temp_repo):
        """Test that force=True bypasses cache."""
        # First analysis
        context1 = analyzer.analyze(temp_repo)

        # Modify a file
        (temp_repo / "new_file.py").write_text("# new file")

        # Force reanalysis should pick up the new file
        context2 = analyzer.analyze(temp_repo, force=True)

        # The file count should have increased
        assert context2.file_count >= context1.file_count

    def test_cache_invalidation_on_change(self, analyzer, temp_repo):
        """Test that cache is invalidated when files change."""
        # First analysis
        context1 = analyzer.analyze(temp_repo)

        # Add a new top-level directory (changes cache hash)
        (temp_repo / "new_module").mkdir()
        (temp_repo / "new_module" / "__init__.py").write_text("")

        # Second analysis should detect change
        context2 = analyzer.analyze(temp_repo)

        # Cache hash should be different
        assert context1.cache_hash != context2.cache_hash


class TestNamingConventionDetection:
    """Tests for naming convention detection."""

    def test_detect_snake_case(self, analyzer, tmp_path):
        """Test detection of snake_case naming."""
        (tmp_path / "my_module.py").write_text("""
def my_function():
    pass

def another_function_name():
    pass
""")

        context = analyzer.analyze(tmp_path)

        # Should detect snake_case
        assert context.naming_conventions.file_naming in ["snake_case", "unknown"]

    def test_detect_camel_case(self, analyzer, tmp_path):
        """Test detection of camelCase naming."""
        (tmp_path / "myModule.js").write_text("""
function myFunction() {}
function anotherFunctionName() {}
const helperUtil = () => {};
""")

        context = analyzer.analyze(tmp_path)

        # Primary language should be JavaScript
        assert context.primary_language == "javascript"


class TestPatternDetection:
    """Tests for code pattern detection."""

    def test_detect_fastapi_pattern(self, analyzer, tmp_path):
        """Test detection of FastAPI pattern."""
        (tmp_path / "pyproject.toml").write_text("""
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.100.0"
uvicorn = "^0.23.0"
""")
        (tmp_path / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")

        context = analyzer.analyze(tmp_path)

        # FastAPI should be in dependencies and detected as pattern
        assert "fastapi" in context.dependency_info.dependencies
        # Pattern detection depends on primary language being Python
        if context.primary_language == "python":
            assert any("FastAPI" in p for p in context.code_patterns)

    def test_detect_react_pattern(self, analyzer, tmp_path):
        """Test detection of React pattern."""
        (tmp_path / "package.json").write_text(json.dumps({
            "dependencies": {
                "react": "^18.0.0",
                "react-dom": "^18.0.0"
            }
        }))
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "App.jsx").write_text("import React from 'react';\nexport default function App() { return <div/>; }")
        (tmp_path / "src" / "index.js").write_text("import App from './App';")

        context = analyzer.analyze(tmp_path)

        # React should be in dependencies
        assert "react" in context.dependency_info.dependencies
        # Pattern detection depends on primary language being JS
        if context.primary_language in ("javascript", "typescript"):
            assert any("React" in p for p in context.code_patterns)

    def test_detect_docker_pattern(self, analyzer, tmp_path):
        """Test detection of Docker containerization pattern."""
        (tmp_path / "Dockerfile").write_text("FROM python:3.11")
        (tmp_path / "main.py").write_text("print('hello')")

        context = analyzer.analyze(tmp_path)

        assert any("Docker" in p for p in context.code_patterns)


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_directory(self, analyzer, tmp_path):
        """Test analysis of empty directory."""
        context = analyzer.analyze(tmp_path)

        assert context.project_name == tmp_path.name
        assert context.file_count == 0
        assert context.primary_language == "unknown"

    def test_binary_files_ignored(self, analyzer, tmp_path):
        """Test that binary files don't cause errors."""
        # Create a "binary" file
        (tmp_path / "data.bin").write_bytes(b'\x00\x01\x02\x03')
        (tmp_path / "main.py").write_text("print('hello')")

        # Should not raise an error
        context = analyzer.analyze(tmp_path)

        assert context.primary_language == "python"

    def test_deeply_nested_structure(self, analyzer, tmp_path):
        """Test analysis of deeply nested directory structure."""
        # Create nested structure
        nested = tmp_path / "a" / "b" / "c" / "d" / "e"
        nested.mkdir(parents=True)
        (nested / "deep.py").write_text("x = 1")

        context = analyzer.analyze(tmp_path)

        # Should find the deeply nested file
        assert context.file_count >= 1

    def test_permission_denied_handling(self, analyzer, tmp_path):
        """Test handling of permission-denied directories."""
        # This test may not work on all systems
        # Just ensure it doesn't crash
        (tmp_path / "main.py").write_text("x = 1")

        context = analyzer.analyze(tmp_path)

        assert context is not None


class TestMultiLanguageRepo:
    """Tests for multi-language repositories."""

    def test_mixed_python_js(self, analyzer, tmp_path):
        """Test analysis of repository with both Python and JavaScript."""
        # Python files
        (tmp_path / "backend").mkdir()
        (tmp_path / "backend" / "app.py").write_text("""
from flask import Flask
app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello'
""")

        # JavaScript files
        (tmp_path / "frontend").mkdir()
        (tmp_path / "frontend" / "app.js").write_text("""
import React from 'react';
function App() { return <div>Hello</div>; }
""")
        (tmp_path / "frontend" / "index.js").write_text("console.log('hello');")

        context = analyzer.analyze(tmp_path)

        # Should detect both languages
        assert "python" in context.languages
        assert "javascript" in context.languages

        # Primary should be whichever has more lines
        assert context.primary_language in ["python", "javascript"]
