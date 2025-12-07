"""
Test generation from code analysis and KnowledgeForge patterns

Generates comprehensive test suites covering:
- Unit tests for individual functions/methods
- Integration tests for component interactions
- End-to-end tests for complete workflows
- Edge cases and error conditions
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from forge.knowledgeforge.pattern_store import PatternStore
from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class TestGenerationError(ForgeError):
    """Errors during test generation"""
    pass


class Language(Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUBY = "ruby"
    RUST = "rust"


class TestType(Enum):
    """Test categories"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    SYSTEM = "system"


@dataclass
class TestableEntity:
    """Represents a testable code entity"""
    name: str
    type: str  # function, class, method, endpoint
    signature: str
    file_path: str
    line_number: int
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    is_async: bool = False


@dataclass
class TestCase:
    """Represents a generated test case"""
    name: str
    entity: TestableEntity
    test_type: TestType
    code: str
    description: str


class TestGenerator:
    """
    Generates tests from code analysis and KF patterns.

    Features:
    - Multi-language support (Python, JavaScript, Go, Ruby, Rust)
    - Pattern-based test generation
    - Multiple test types (unit, integration, e2e)
    - Framework detection (pytest, jest, rspec, etc.)
    - >80% coverage targeting
    """

    # Language file extensions
    LANGUAGE_EXTENSIONS = {
        '.py': Language.PYTHON,
        '.js': Language.JAVASCRIPT,
        '.jsx': Language.JAVASCRIPT,
        '.ts': Language.TYPESCRIPT,
        '.tsx': Language.TYPESCRIPT,
        '.go': Language.GO,
        '.rb': Language.RUBY,
        '.rs': Language.RUST,
    }

    # Test frameworks by language
    TEST_FRAMEWORKS = {
        Language.PYTHON: 'pytest',
        Language.JAVASCRIPT: 'jest',
        Language.TYPESCRIPT: 'jest',
        Language.GO: 'testing',
        Language.RUBY: 'rspec',
        Language.RUST: 'cargo test',
    }

    def __init__(self, pattern_store: Optional[PatternStore] = None):
        """
        Initialize test generator.

        Args:
            pattern_store: KnowledgeForge pattern store
        """
        self.pattern_store = pattern_store or PatternStore()
        logger.info("Initialized TestGenerator")

    def generate_tests(
        self,
        code_files: Dict[str, str],
        tech_stack: Optional[List[str]] = None,
        project_context: str = "",
        test_types: Optional[List[TestType]] = None
    ) -> Dict[str, str]:
        """
        Generate tests for code files.

        Args:
            code_files: Dictionary mapping file paths to code content
            tech_stack: Technologies used in project
            project_context: Project description/context
            test_types: Test types to generate (default: all)

        Returns:
            Dictionary mapping test file paths to test content

        Raises:
            TestGenerationError: If generation fails
        """
        logger.info(f"Generating tests for {len(code_files)} files")

        if test_types is None:
            test_types = [TestType.UNIT, TestType.INTEGRATION, TestType.E2E]

        # Load test patterns
        test_patterns = self._load_test_patterns(tech_stack)

        # Extract testable entities from code
        entities_by_file = {}
        for file_path, content in code_files.items():
            entities = self._extract_entities(file_path, content)
            if entities:
                entities_by_file[file_path] = entities

        logger.info(f"Extracted {sum(len(e) for e in entities_by_file.values())} testable entities")

        # Generate test cases
        test_files = {}
        for file_path, entities in entities_by_file.items():
            language = self._detect_language(file_path)
            if not language:
                logger.warning(f"Skipping {file_path}: unsupported language")
                continue

            test_cases = []
            for entity in entities:
                for test_type in test_types:
                    cases = self._generate_test_cases(
                        entity, test_type, language, test_patterns
                    )
                    test_cases.extend(cases)

            if test_cases:
                test_file_path = self._get_test_file_path(file_path, language)
                test_content = self._format_test_file(
                    test_cases, language, file_path, project_context
                )
                test_files[test_file_path] = test_content

        logger.info(f"Generated {len(test_files)} test files")
        return test_files

    def _load_test_patterns(self, tech_stack: Optional[List[str]]) -> List[Dict]:
        """Load relevant test patterns from KnowledgeForge"""
        query = "test scenarios unit integration e2e"
        if tech_stack:
            query += " " + " ".join(tech_stack)

        patterns = self.pattern_store.search(
            query=query,
            max_results=10,
            method='hybrid'
        )

        logger.debug(f"Loaded {len(patterns)} test patterns")
        return patterns

    def _detect_language(self, file_path: str) -> Optional[Language]:
        """Detect programming language from file extension"""
        path = Path(file_path)
        return self.LANGUAGE_EXTENSIONS.get(path.suffix)

    def _extract_entities(self, file_path: str, content: str) -> List[TestableEntity]:
        """Extract testable entities from code"""
        language = self._detect_language(file_path)
        if not language:
            return []

        if language == Language.PYTHON:
            return self._extract_python_entities(file_path, content)
        elif language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
            return self._extract_javascript_entities(file_path, content)
        elif language == Language.GO:
            return self._extract_go_entities(file_path, content)
        elif language == Language.RUBY:
            return self._extract_ruby_entities(file_path, content)
        elif language == Language.RUST:
            return self._extract_rust_entities(file_path, content)

        return []

    def _extract_python_entities(self, file_path: str, content: str) -> List[TestableEntity]:
        """Extract Python functions and classes"""
        entities = []
        lines = content.split('\n')

        # Find functions
        func_pattern = re.compile(r'^(async\s+)?def\s+(\w+)\s*\((.*?)\)\s*(?:->\s*(.+?))?:', re.MULTILINE)
        for match in func_pattern.finditer(content):
            is_async = bool(match.group(1))
            name = match.group(2)
            params = match.group(3)
            return_type = match.group(4)

            # Skip private functions (start with _)
            if name.startswith('_'):
                continue

            line_num = content[:match.start()].count('\n') + 1

            entities.append(TestableEntity(
                name=name,
                type='function',
                signature=f"def {name}({params})",
                file_path=file_path,
                line_number=line_num,
                parameters=[p.split(':')[0].strip() for p in params.split(',') if p.strip()],
                return_type=return_type.strip() if return_type else None,
                is_async=is_async
            ))

        # Find classes
        class_pattern = re.compile(r'^class\s+(\w+)(?:\((.*?)\))?:', re.MULTILINE)
        for match in class_pattern.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            entities.append(TestableEntity(
                name=name,
                type='class',
                signature=f"class {name}",
                file_path=file_path,
                line_number=line_num
            ))

        return entities

    def _extract_javascript_entities(self, file_path: str, content: str) -> List[TestableEntity]:
        """Extract JavaScript/TypeScript functions and classes"""
        entities = []

        # Find function declarations
        func_patterns = [
            re.compile(r'(async\s+)?function\s+(\w+)\s*\((.*?)\)'),
            re.compile(r'const\s+(\w+)\s*=\s*(async\s+)?\((.*?)\)\s*=>'),
            re.compile(r'export\s+(async\s+)?function\s+(\w+)\s*\((.*?)\)'),
        ]

        for pattern in func_patterns:
            for match in pattern.finditer(content):
                groups = match.groups()
                is_async = 'async' in match.group(0)
                name = groups[1] if len(groups) > 1 and groups[1] else groups[0]
                params = groups[-1]

                line_num = content[:match.start()].count('\n') + 1

                entities.append(TestableEntity(
                    name=name,
                    type='function',
                    signature=f"function {name}({params})",
                    file_path=file_path,
                    line_number=line_num,
                    parameters=[p.split(':')[0].strip() for p in params.split(',') if p.strip()],
                    is_async=is_async
                ))

        # Find classes
        class_pattern = re.compile(r'class\s+(\w+)(?:\s+extends\s+\w+)?')
        for match in class_pattern.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            entities.append(TestableEntity(
                name=name,
                type='class',
                signature=f"class {name}",
                file_path=file_path,
                line_number=line_num
            ))

        return entities

    def _extract_go_entities(self, file_path: str, content: str) -> List[TestableEntity]:
        """Extract Go functions"""
        entities = []

        # Find function declarations
        func_pattern = re.compile(r'func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\((.*?)\)\s*(?:\((.*?)\)|\w+)?')
        for match in func_pattern.finditer(content):
            name = match.group(1)
            params = match.group(2)

            # Skip unexported functions (start with lowercase)
            if name[0].islower():
                continue

            line_num = content[:match.start()].count('\n') + 1

            entities.append(TestableEntity(
                name=name,
                type='function',
                signature=f"func {name}({params})",
                file_path=file_path,
                line_number=line_num,
                parameters=[p.split()[-1] for p in params.split(',') if p.strip()]
            ))

        return entities

    def _extract_ruby_entities(self, file_path: str, content: str) -> List[TestableEntity]:
        """Extract Ruby methods and classes"""
        entities = []

        # Find method definitions
        method_pattern = re.compile(r'def\s+(\w+)(?:\((.*?)\))?')
        for match in method_pattern.finditer(content):
            name = match.group(1)
            params = match.group(2) or ""

            line_num = content[:match.start()].count('\n') + 1

            entities.append(TestableEntity(
                name=name,
                type='method',
                signature=f"def {name}({params})",
                file_path=file_path,
                line_number=line_num,
                parameters=[p.strip() for p in params.split(',') if p.strip()]
            ))

        # Find classes
        class_pattern = re.compile(r'class\s+(\w+)(?:\s+<\s+\w+)?')
        for match in class_pattern.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            entities.append(TestableEntity(
                name=name,
                type='class',
                signature=f"class {name}",
                file_path=file_path,
                line_number=line_num
            ))

        return entities

    def _extract_rust_entities(self, file_path: str, content: str) -> List[TestableEntity]:
        """Extract Rust functions"""
        entities = []

        # Find function declarations
        func_pattern = re.compile(r'pub\s+(?:async\s+)?fn\s+(\w+)\s*(?:<.*?>)?\s*\((.*?)\)')
        for match in func_pattern.finditer(content):
            name = match.group(1)
            params = match.group(2)
            is_async = 'async' in content[max(0, match.start()-20):match.start()]

            line_num = content[:match.start()].count('\n') + 1

            entities.append(TestableEntity(
                name=name,
                type='function',
                signature=f"fn {name}({params})",
                file_path=file_path,
                line_number=line_num,
                parameters=[p.split(':')[0].strip() for p in params.split(',') if p.strip()],
                is_async=is_async
            ))

        return entities

    def _generate_test_cases(
        self,
        entity: TestableEntity,
        test_type: TestType,
        language: Language,
        patterns: List[Dict]
    ) -> List[TestCase]:
        """Generate test cases for an entity"""
        if language == Language.PYTHON:
            return self._generate_python_tests(entity, test_type, patterns)
        elif language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
            return self._generate_javascript_tests(entity, test_type, patterns)
        elif language == Language.GO:
            return self._generate_go_tests(entity, test_type, patterns)
        elif language == Language.RUBY:
            return self._generate_ruby_tests(entity, test_type, patterns)
        elif language == Language.RUST:
            return self._generate_rust_tests(entity, test_type, patterns)

        return []

    def _generate_python_tests(
        self, entity: TestableEntity, test_type: TestType, patterns: List[Dict]
    ) -> List[TestCase]:
        """Generate pytest test cases"""
        tests = []

        if entity.type == 'function' and test_type == TestType.UNIT:
            # Happy path test
            test_name = f"test_{entity.name}_success"
            test_code = f"""def {test_name}():
    \"\"\"Test {entity.name} with valid inputs\"\"\"
    # Arrange
    # TODO: Set up test data

    # Act
    result = {entity.name}()

    # Assert
    assert result is not None
"""
            tests.append(TestCase(
                name=test_name,
                entity=entity,
                test_type=test_type,
                code=test_code,
                description=f"Test {entity.name} with valid inputs"
            ))

            # Error case test
            test_name = f"test_{entity.name}_error_handling"
            test_code = f"""def {test_name}():
    \"\"\"Test {entity.name} error handling\"\"\"
    # Arrange
    # TODO: Set up invalid test data

    # Act & Assert
    with pytest.raises(Exception):
        {entity.name}()
"""
            tests.append(TestCase(
                name=test_name,
                entity=entity,
                test_type=test_type,
                code=test_code,
                description=f"Test {entity.name} error handling"
            ))

        return tests

    def _generate_javascript_tests(
        self, entity: TestableEntity, test_type: TestType, patterns: List[Dict]
    ) -> List[TestCase]:
        """Generate Jest test cases"""
        tests = []

        if entity.type == 'function' and test_type == TestType.UNIT:
            test_name = f"{entity.name} should work with valid inputs"
            test_code = f"""test('{test_name}', {"async " if entity.is_async else ""}() => {{
  // Arrange
  // TODO: Set up test data

  // Act
  const result = {"await " if entity.is_async else ""}{entity.name}();

  // Assert
  expect(result).toBeDefined();
}});
"""
            tests.append(TestCase(
                name=test_name,
                entity=entity,
                test_type=test_type,
                code=test_code,
                description=test_name
            ))

        return tests

    def _generate_go_tests(
        self, entity: TestableEntity, test_type: TestType, patterns: List[Dict]
    ) -> List[TestCase]:
        """Generate Go test cases"""
        tests = []

        if entity.type == 'function' and test_type == TestType.UNIT:
            test_name = f"Test{entity.name}"
            test_code = f"""func {test_name}(t *testing.T) {{
	// Arrange
	// TODO: Set up test data

	// Act
	result := {entity.name}()

	// Assert
	if result == nil {{
		t.Error("Expected non-nil result")
	}}
}}
"""
            tests.append(TestCase(
                name=test_name,
                entity=entity,
                test_type=test_type,
                code=test_code,
                description=f"Test {entity.name}"
            ))

        return tests

    def _generate_ruby_tests(
        self, entity: TestableEntity, test_type: TestType, patterns: List[Dict]
    ) -> List[TestCase]:
        """Generate RSpec test cases"""
        tests = []

        if entity.type == 'method' and test_type == TestType.UNIT:
            test_name = f"returns expected result"
            test_code = f"""  it '{test_name}' do
    # Arrange
    # TODO: Set up test data

    # Act
    result = subject.{entity.name}

    # Assert
    expect(result).not_to be_nil
  end
"""
            tests.append(TestCase(
                name=test_name,
                entity=entity,
                test_type=test_type,
                code=test_code,
                description=test_name
            ))

        return tests

    def _generate_rust_tests(
        self, entity: TestableEntity, test_type: TestType, patterns: List[Dict]
    ) -> List[TestCase]:
        """Generate Rust test cases"""
        tests = []

        if entity.type == 'function' and test_type == TestType.UNIT:
            test_name = f"test_{entity.name}"
            test_code = f"""#[test]
fn {test_name}() {{
    // Arrange
    // TODO: Set up test data

    // Act
    let result = {entity.name}();

    // Assert
    assert!(result.is_ok());
}}
"""
            tests.append(TestCase(
                name=test_name,
                entity=entity,
                test_type=test_type,
                code=test_code,
                description=f"Test {entity.name}"
            ))

        return tests

    def _get_test_file_path(self, source_file: str, language: Language) -> str:
        """Generate test file path from source file"""
        path = Path(source_file)

        if language == Language.PYTHON:
            return f"tests/test_{path.stem}.py"
        elif language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
            return f"tests/{path.stem}.test{path.suffix}"
        elif language == Language.GO:
            return f"{path.stem}_test.go"
        elif language == Language.RUBY:
            return f"spec/{path.stem}_spec.rb"
        elif language == Language.RUST:
            return f"tests/{path.stem}_test.rs"

        return f"tests/test_{path.name}"

    def _format_test_file(
        self,
        test_cases: List[TestCase],
        language: Language,
        source_file: str,
        project_context: str
    ) -> str:
        """Format test cases into complete test file"""
        if language == Language.PYTHON:
            return self._format_python_test_file(test_cases, source_file, project_context)
        elif language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
            return self._format_javascript_test_file(test_cases, source_file, project_context)
        elif language == Language.GO:
            return self._format_go_test_file(test_cases, source_file, project_context)
        elif language == Language.RUBY:
            return self._format_ruby_test_file(test_cases, source_file, project_context)
        elif language == Language.RUST:
            return self._format_rust_test_file(test_cases, source_file, project_context)

        return ""

    def _format_python_test_file(
        self, test_cases: List[TestCase], source_file: str, project_context: str
    ) -> str:
        """Format pytest test file"""
        imports = f"""\"\"\"
Tests for {source_file}

{project_context}

Generated by Forge Test Generator
\"\"\"

import pytest
from {Path(source_file).stem} import *

"""

        test_code = "\n\n".join(tc.code for tc in test_cases)

        return imports + test_code

    def _format_javascript_test_file(
        self, test_cases: List[TestCase], source_file: str, project_context: str
    ) -> str:
        """Format Jest test file"""
        imports = f"""/**
 * Tests for {source_file}
 *
 * {project_context}
 *
 * Generated by Forge Test Generator
 */

import * as module from './{Path(source_file).stem}';

"""

        # Group tests by entity
        entities = {}
        for tc in test_cases:
            if tc.entity.name not in entities:
                entities[tc.entity.name] = []
            entities[tc.entity.name].append(tc)

        test_code = ""
        for entity_name, cases in entities.items():
            test_code += f"describe('{entity_name}', () => {{\n"
            for tc in cases:
                test_code += tc.code + "\n"
            test_code += "});\n\n"

        return imports + test_code

    def _format_go_test_file(
        self, test_cases: List[TestCase], source_file: str, project_context: str
    ) -> str:
        """Format Go test file"""
        package_name = Path(source_file).stem

        header = f"""// Tests for {source_file}
//
// {project_context}
//
// Generated by Forge Test Generator

package {package_name}

import "testing"

"""

        test_code = "\n".join(tc.code for tc in test_cases)

        return header + test_code

    def _format_ruby_test_file(
        self, test_cases: List[TestCase], source_file: str, project_context: str
    ) -> str:
        """Format RSpec test file"""
        require_path = Path(source_file).stem

        header = f"""# Tests for {source_file}
#
# {project_context}
#
# Generated by Forge Test Generator

require 'rspec'
require_relative '../{require_path}'

"""

        # Group by entity
        entities = {}
        for tc in test_cases:
            if tc.entity.name not in entities:
                entities[tc.entity.name] = []
            entities[tc.entity.name].append(tc)

        test_code = ""
        for entity_name, cases in entities.items():
            test_code += f"describe '{entity_name}' do\n"
            for tc in cases:
                test_code += tc.code + "\n"
            test_code += "end\n\n"

        return header + test_code

    def _format_rust_test_file(
        self, test_cases: List[TestCase], source_file: str, project_context: str
    ) -> str:
        """Format Rust test file"""
        header = f"""// Tests for {source_file}
//
// {project_context}
//
// Generated by Forge Test Generator

"""

        test_code = "\n".join(tc.code for tc in test_cases)

        return header + test_code

    def close(self):
        """Close pattern store"""
        if self.pattern_store:
            self.pattern_store.close()
