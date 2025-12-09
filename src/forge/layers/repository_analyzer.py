"""
Repository Analyzer for Forge

Analyzes existing codebases before code generation to understand:
- Directory structure and naming conventions
- Existing code patterns and style
- Test patterns and frameworks
- Dependencies and versions
- API patterns and data models

This enables more consistent code generation that respects existing conventions.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime

from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class RepositoryAnalyzerError(ForgeError):
    """Errors during repository analysis"""
    pass


@dataclass
class FileTypeStats:
    """Statistics for a file type"""
    count: int = 0
    total_lines: int = 0
    extensions: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "count": self.count,
            "total_lines": self.total_lines,
            "extensions": list(self.extensions)
        }


@dataclass
class NamingConventions:
    """Detected naming conventions"""
    file_naming: str = "unknown"  # snake_case, kebab-case, camelCase, PascalCase
    function_naming: str = "unknown"
    class_naming: str = "unknown"
    variable_naming: str = "unknown"
    constant_naming: str = "unknown"

    def to_dict(self) -> Dict[str, str]:
        return {
            "file_naming": self.file_naming,
            "function_naming": self.function_naming,
            "class_naming": self.class_naming,
            "variable_naming": self.variable_naming,
            "constant_naming": self.constant_naming
        }


@dataclass
class TestInfo:
    """Information about testing setup"""
    framework: Optional[str] = None
    test_directory: Optional[str] = None
    test_file_pattern: str = "test_*.py"
    test_count: int = 0
    has_fixtures: bool = False
    has_conftest: bool = False
    coverage_configured: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "framework": self.framework,
            "test_directory": self.test_directory,
            "test_file_pattern": self.test_file_pattern,
            "test_count": self.test_count,
            "has_fixtures": self.has_fixtures,
            "has_conftest": self.has_conftest,
            "coverage_configured": self.coverage_configured
        }


@dataclass
class DependencyInfo:
    """Information about project dependencies"""
    package_manager: Optional[str] = None  # pip, poetry, npm, yarn, cargo, etc.
    manifest_file: Optional[str] = None
    dependencies: Dict[str, str] = field(default_factory=dict)
    dev_dependencies: Dict[str, str] = field(default_factory=dict)
    python_version: Optional[str] = None
    node_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "package_manager": self.package_manager,
            "manifest_file": self.manifest_file,
            "dependencies": self.dependencies,
            "dev_dependencies": self.dev_dependencies,
            "python_version": self.python_version,
            "node_version": self.node_version
        }


@dataclass
class RepositoryContext:
    """
    Complete analysis of a repository.

    This context is passed to the planning agent and code generator
    to ensure generated code respects existing conventions.
    """
    # Basic info
    root_path: str
    project_name: str
    analyzed_at: str

    # Structure
    directory_structure: Dict[str, List[str]] = field(default_factory=dict)
    key_directories: List[str] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)

    # Languages and files
    primary_language: str = "unknown"
    languages: Dict[str, FileTypeStats] = field(default_factory=dict)
    file_count: int = 0
    total_lines: int = 0

    # Patterns
    naming_conventions: NamingConventions = field(default_factory=NamingConventions)
    code_patterns: List[str] = field(default_factory=list)

    # Testing
    test_info: TestInfo = field(default_factory=TestInfo)

    # Dependencies
    dependency_info: DependencyInfo = field(default_factory=DependencyInfo)

    # Important files
    readme_content: Optional[str] = None
    config_files: List[str] = field(default_factory=list)

    # Cache hash for invalidation
    cache_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "root_path": self.root_path,
            "project_name": self.project_name,
            "analyzed_at": self.analyzed_at,
            "directory_structure": self.directory_structure,
            "key_directories": self.key_directories,
            "entry_points": self.entry_points,
            "primary_language": self.primary_language,
            "languages": {k: v.to_dict() for k, v in self.languages.items()},
            "file_count": self.file_count,
            "total_lines": self.total_lines,
            "naming_conventions": self.naming_conventions.to_dict(),
            "code_patterns": self.code_patterns,
            "test_info": self.test_info.to_dict(),
            "dependency_info": self.dependency_info.to_dict(),
            "readme_content": self.readme_content[:1000] if self.readme_content else None,
            "config_files": self.config_files,
            "cache_hash": self.cache_hash
        }

    def to_prompt_context(self) -> str:
        """
        Format as context string for inclusion in prompts.

        This is a condensed, prompt-friendly version of the analysis.
        """
        sections = []

        # Project overview
        sections.append(f"## Project: {self.project_name}")
        sections.append(f"Primary Language: {self.primary_language}")
        sections.append(f"Files: {self.file_count} | Lines: {self.total_lines}")

        # Key directories
        if self.key_directories:
            sections.append(f"\n### Key Directories")
            for d in self.key_directories[:10]:
                sections.append(f"- {d}")

        # Naming conventions
        nc = self.naming_conventions
        sections.append(f"\n### Naming Conventions")
        sections.append(f"- Files: {nc.file_naming}")
        sections.append(f"- Functions: {nc.function_naming}")
        sections.append(f"- Classes: {nc.class_naming}")

        # Dependencies
        if self.dependency_info.package_manager:
            sections.append(f"\n### Dependencies")
            sections.append(f"Package Manager: {self.dependency_info.package_manager}")
            if self.dependency_info.python_version:
                sections.append(f"Python: {self.dependency_info.python_version}")

            # Key dependencies (first 10)
            deps = list(self.dependency_info.dependencies.items())[:10]
            if deps:
                sections.append("Key packages:")
                for name, version in deps:
                    sections.append(f"  - {name}: {version}")

        # Testing
        if self.test_info.framework:
            sections.append(f"\n### Testing")
            sections.append(f"Framework: {self.test_info.framework}")
            sections.append(f"Test Directory: {self.test_info.test_directory}")
            sections.append(f"Pattern: {self.test_info.test_file_pattern}")

        # Code patterns
        if self.code_patterns:
            sections.append(f"\n### Detected Patterns")
            for pattern in self.code_patterns[:5]:
                sections.append(f"- {pattern}")

        # README summary
        if self.readme_content:
            # First 500 chars of README
            readme_preview = self.readme_content[:500]
            if len(self.readme_content) > 500:
                readme_preview += "..."
            sections.append(f"\n### README Preview")
            sections.append(readme_preview)

        return "\n".join(sections)


class RepositoryAnalyzer:
    """
    Analyzes repositories to extract context for code generation.

    This analyzer examines:
    - Directory structure
    - File types and languages
    - Naming conventions
    - Dependencies
    - Testing setup
    - Common patterns

    Results are cached based on file modification times.
    """

    # File extensions to language mapping
    LANGUAGE_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".rb": "ruby",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".kt": "kotlin",
        ".swift": "swift",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".php": "php",
        ".scala": "scala",
        ".r": "r",
        ".R": "r",
        ".sql": "sql",
        ".sh": "shell",
        ".bash": "shell",
        ".zsh": "shell",
        ".html": "html",
        ".css": "css",
        ".scss": "scss",
        ".sass": "sass",
        ".less": "less",
        ".md": "markdown",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".xml": "xml",
    }

    # Directories to skip
    SKIP_DIRS = {
        ".git", ".svn", ".hg",
        "node_modules", "__pycache__", ".pytest_cache",
        "venv", ".venv", "env", ".env",
        "dist", "build", "target",
        ".tox", ".nox", ".mypy_cache",
        "coverage", "htmlcov", ".coverage",
        ".idea", ".vscode",
        "vendor", "third_party",
    }

    # Config file patterns
    CONFIG_PATTERNS = {
        "pyproject.toml", "setup.py", "setup.cfg",
        "package.json", "package-lock.json", "yarn.lock",
        "Cargo.toml", "Cargo.lock",
        "go.mod", "go.sum",
        "Gemfile", "Gemfile.lock",
        "requirements.txt", "requirements-dev.txt",
        "Pipfile", "Pipfile.lock",
        ".gitignore", ".dockerignore",
        "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
        "Makefile", "CMakeLists.txt",
        ".eslintrc", ".eslintrc.js", ".eslintrc.json",
        ".prettierrc", ".prettierrc.js", ".prettierrc.json",
        "tsconfig.json", "jsconfig.json",
        "pytest.ini", "tox.ini", "noxfile.py",
        ".pre-commit-config.yaml",
    }

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize analyzer.

        Args:
            cache_dir: Directory for caching analysis results
        """
        self.cache_dir = cache_dir or Path.home() / ".forge" / "cache" / "repo_analysis"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def analyze(self, repo_path: Path, force: bool = False) -> RepositoryContext:
        """
        Analyze a repository.

        Args:
            repo_path: Path to repository root
            force: Force re-analysis even if cached

        Returns:
            RepositoryContext with analysis results

        Raises:
            RepositoryAnalyzerError: If analysis fails
        """
        repo_path = Path(repo_path).resolve()

        if not repo_path.exists():
            raise RepositoryAnalyzerError(f"Repository path does not exist: {repo_path}")

        if not repo_path.is_dir():
            raise RepositoryAnalyzerError(f"Path is not a directory: {repo_path}")

        logger.info(f"Analyzing repository: {repo_path}")

        # Check cache
        cache_hash = self._compute_cache_hash(repo_path)
        if not force:
            cached = self._load_from_cache(repo_path, cache_hash)
            if cached:
                logger.info("Using cached repository analysis")
                return cached

        # Perform analysis
        context = RepositoryContext(
            root_path=str(repo_path),
            project_name=repo_path.name,
            analyzed_at=datetime.now().isoformat(),
            cache_hash=cache_hash
        )

        # Run analysis steps
        self._analyze_structure(repo_path, context)
        self._analyze_languages(repo_path, context)
        self._analyze_naming_conventions(repo_path, context)
        self._analyze_dependencies(repo_path, context)
        self._analyze_testing(repo_path, context)
        self._analyze_patterns(repo_path, context)
        self._read_readme(repo_path, context)
        self._find_config_files(repo_path, context)

        # Save to cache
        self._save_to_cache(repo_path, context)

        logger.info(f"Repository analysis complete: {context.file_count} files, {context.primary_language}")

        return context

    def _compute_cache_hash(self, repo_path: Path) -> str:
        """Compute hash based on file modification times."""
        hasher = hashlib.md5()

        # Include top-level files and directories
        for item in sorted(repo_path.iterdir()):
            if item.name.startswith("."):
                continue
            try:
                stat = item.stat()
                hasher.update(f"{item.name}:{stat.st_mtime}".encode())
            except OSError:
                pass

        return hasher.hexdigest()[:16]

    def _get_cache_path(self, repo_path: Path) -> Path:
        """Get cache file path for a repository."""
        # Use hash of repo path as cache filename
        path_hash = hashlib.md5(str(repo_path).encode()).hexdigest()[:16]
        return self.cache_dir / f"{path_hash}.json"

    def _load_from_cache(self, repo_path: Path, current_hash: str) -> Optional[RepositoryContext]:
        """Load analysis from cache if valid."""
        cache_path = self._get_cache_path(repo_path)

        if not cache_path.exists():
            return None

        try:
            data = json.loads(cache_path.read_text())
            if data.get("cache_hash") == current_hash:
                # Reconstruct RepositoryContext from cached data
                return self._dict_to_context(data)
        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.debug(f"Cache invalid: {e}")

        return None

    def _save_to_cache(self, repo_path: Path, context: RepositoryContext):
        """Save analysis to cache."""
        cache_path = self._get_cache_path(repo_path)

        try:
            cache_path.write_text(json.dumps(context.to_dict(), indent=2))
            logger.debug(f"Saved analysis to cache: {cache_path}")
        except OSError as e:
            logger.warning(f"Failed to save cache: {e}")

    def _dict_to_context(self, data: Dict[str, Any]) -> RepositoryContext:
        """Reconstruct RepositoryContext from dictionary."""
        # Reconstruct nested dataclasses
        languages = {}
        for lang, stats in data.get("languages", {}).items():
            languages[lang] = FileTypeStats(
                count=stats["count"],
                total_lines=stats["total_lines"],
                extensions=set(stats["extensions"])
            )

        nc_data = data.get("naming_conventions", {})
        naming_conventions = NamingConventions(
            file_naming=nc_data.get("file_naming", "unknown"),
            function_naming=nc_data.get("function_naming", "unknown"),
            class_naming=nc_data.get("class_naming", "unknown"),
            variable_naming=nc_data.get("variable_naming", "unknown"),
            constant_naming=nc_data.get("constant_naming", "unknown")
        )

        ti_data = data.get("test_info", {})
        test_info = TestInfo(
            framework=ti_data.get("framework"),
            test_directory=ti_data.get("test_directory"),
            test_file_pattern=ti_data.get("test_file_pattern", "test_*.py"),
            test_count=ti_data.get("test_count", 0),
            has_fixtures=ti_data.get("has_fixtures", False),
            has_conftest=ti_data.get("has_conftest", False),
            coverage_configured=ti_data.get("coverage_configured", False)
        )

        di_data = data.get("dependency_info", {})
        dependency_info = DependencyInfo(
            package_manager=di_data.get("package_manager"),
            manifest_file=di_data.get("manifest_file"),
            dependencies=di_data.get("dependencies", {}),
            dev_dependencies=di_data.get("dev_dependencies", {}),
            python_version=di_data.get("python_version"),
            node_version=di_data.get("node_version")
        )

        return RepositoryContext(
            root_path=data["root_path"],
            project_name=data["project_name"],
            analyzed_at=data["analyzed_at"],
            directory_structure=data.get("directory_structure", {}),
            key_directories=data.get("key_directories", []),
            entry_points=data.get("entry_points", []),
            primary_language=data.get("primary_language", "unknown"),
            languages=languages,
            file_count=data.get("file_count", 0),
            total_lines=data.get("total_lines", 0),
            naming_conventions=naming_conventions,
            code_patterns=data.get("code_patterns", []),
            test_info=test_info,
            dependency_info=dependency_info,
            readme_content=data.get("readme_content"),
            config_files=data.get("config_files", []),
            cache_hash=data.get("cache_hash")
        )

    def _analyze_structure(self, repo_path: Path, context: RepositoryContext):
        """Analyze directory structure."""
        structure = {}
        key_dirs = []

        for item in repo_path.iterdir():
            if item.name.startswith(".") or item.name in self.SKIP_DIRS:
                continue

            if item.is_dir():
                # Get immediate children
                try:
                    children = [
                        c.name for c in item.iterdir()
                        if not c.name.startswith(".")
                    ][:20]  # Limit children
                    structure[item.name] = children

                    # Identify key directories
                    if item.name in {"src", "lib", "app", "core", "api", "tests", "test"}:
                        key_dirs.append(item.name)
                except PermissionError:
                    pass

        context.directory_structure = structure
        context.key_directories = key_dirs

        # Find entry points
        entry_points = []
        for pattern in ["main.py", "app.py", "__main__.py", "index.js", "index.ts", "main.go", "main.rs"]:
            if (repo_path / pattern).exists():
                entry_points.append(pattern)
            if (repo_path / "src" / pattern).exists():
                entry_points.append(f"src/{pattern}")

        context.entry_points = entry_points

    def _analyze_languages(self, repo_path: Path, context: RepositoryContext):
        """Analyze languages used in the repository."""
        languages: Dict[str, FileTypeStats] = {}
        file_count = 0
        total_lines = 0

        for root, dirs, files in os.walk(repo_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS and not d.startswith(".")]

            for file in files:
                if file.startswith("."):
                    continue

                filepath = Path(root) / file
                ext = filepath.suffix.lower()

                if ext in self.LANGUAGE_MAP:
                    lang = self.LANGUAGE_MAP[ext]

                    if lang not in languages:
                        languages[lang] = FileTypeStats()

                    languages[lang].count += 1
                    languages[lang].extensions.add(ext)

                    # Count lines (with limit to avoid huge files)
                    try:
                        with open(filepath, 'r', errors='ignore') as f:
                            lines = sum(1 for _ in f)
                            languages[lang].total_lines += min(lines, 10000)
                            total_lines += min(lines, 10000)
                    except (OSError, UnicodeDecodeError):
                        pass

                    file_count += 1

        context.languages = languages
        context.file_count = file_count
        context.total_lines = total_lines

        # Determine primary language
        if languages:
            primary = max(languages.items(), key=lambda x: x[1].total_lines)
            context.primary_language = primary[0]

    def _analyze_naming_conventions(self, repo_path: Path, context: RepositoryContext):
        """Analyze naming conventions used in the codebase."""
        conventions = NamingConventions()

        # Analyze file naming
        file_names = []
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS and not d.startswith(".")]
            for file in files:
                if file.startswith(".") or file.startswith("_"):
                    continue
                name = Path(file).stem
                if name and len(name) > 2:
                    file_names.append(name)
                if len(file_names) >= 50:
                    break
            if len(file_names) >= 50:
                break

        if file_names:
            conventions.file_naming = self._detect_naming_style(file_names)

        # For Python projects, analyze function/class naming
        if context.primary_language == "python":
            self._analyze_python_naming(repo_path, conventions)
        elif context.primary_language in ("javascript", "typescript"):
            self._analyze_js_naming(repo_path, conventions)

        context.naming_conventions = conventions

    def _detect_naming_style(self, names: List[str]) -> str:
        """Detect predominant naming style from a list of names."""
        snake = 0
        kebab = 0
        camel = 0
        pascal = 0

        for name in names:
            if "_" in name and name.islower():
                snake += 1
            elif "-" in name:
                kebab += 1
            elif name[0].isupper() and not "_" in name:
                pascal += 1
            elif name[0].islower() and any(c.isupper() for c in name):
                camel += 1

        max_count = max(snake, kebab, camel, pascal)
        if max_count == 0:
            return "unknown"

        if snake == max_count:
            return "snake_case"
        elif kebab == max_count:
            return "kebab-case"
        elif camel == max_count:
            return "camelCase"
        elif pascal == max_count:
            return "PascalCase"

        return "mixed"

    def _analyze_python_naming(self, repo_path: Path, conventions: NamingConventions):
        """Analyze Python-specific naming conventions."""
        import re

        function_names = []
        class_names = []

        # Sample a few Python files
        py_files = list(repo_path.rglob("*.py"))[:20]

        for py_file in py_files:
            if any(skip in str(py_file) for skip in self.SKIP_DIRS):
                continue

            try:
                content = py_file.read_text(errors='ignore')

                # Find function definitions
                functions = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
                function_names.extend(functions[:10])

                # Find class definitions
                classes = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[:\(]', content)
                class_names.extend(classes[:10])

            except (OSError, UnicodeDecodeError):
                pass

        if function_names:
            conventions.function_naming = self._detect_naming_style(function_names)
        if class_names:
            conventions.class_naming = self._detect_naming_style(class_names)

    def _analyze_js_naming(self, repo_path: Path, conventions: NamingConventions):
        """Analyze JavaScript/TypeScript naming conventions."""
        import re

        function_names = []
        class_names = []

        # Sample JS/TS files
        js_files = list(repo_path.rglob("*.js"))[:10] + list(repo_path.rglob("*.ts"))[:10]

        for js_file in js_files:
            if any(skip in str(js_file) for skip in self.SKIP_DIRS):
                continue

            try:
                content = js_file.read_text(errors='ignore')

                # Find function definitions
                functions = re.findall(r'(?:function|const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*[=\(]', content)
                function_names.extend(functions[:10])

                # Find class definitions
                classes = re.findall(r'class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)', content)
                class_names.extend(classes[:10])

            except (OSError, UnicodeDecodeError):
                pass

        if function_names:
            conventions.function_naming = self._detect_naming_style(function_names)
        if class_names:
            conventions.class_naming = self._detect_naming_style(class_names)

    def _analyze_dependencies(self, repo_path: Path, context: RepositoryContext):
        """Analyze project dependencies."""
        dep_info = DependencyInfo()

        # Check for Python project
        if (repo_path / "pyproject.toml").exists():
            dep_info.package_manager = "poetry"
            dep_info.manifest_file = "pyproject.toml"
            self._parse_pyproject(repo_path / "pyproject.toml", dep_info)
        elif (repo_path / "requirements.txt").exists():
            dep_info.package_manager = "pip"
            dep_info.manifest_file = "requirements.txt"
            self._parse_requirements(repo_path / "requirements.txt", dep_info)
        elif (repo_path / "setup.py").exists():
            dep_info.package_manager = "setuptools"
            dep_info.manifest_file = "setup.py"

        # Check for Node.js project
        if (repo_path / "package.json").exists():
            if dep_info.package_manager:
                # Multi-language project
                pass
            elif (repo_path / "yarn.lock").exists():
                dep_info.package_manager = "yarn"
            elif (repo_path / "pnpm-lock.yaml").exists():
                dep_info.package_manager = "pnpm"
            else:
                dep_info.package_manager = "npm"
            dep_info.manifest_file = "package.json"
            self._parse_package_json(repo_path / "package.json", dep_info)

        # Check for other package managers
        if (repo_path / "Cargo.toml").exists():
            dep_info.package_manager = "cargo"
            dep_info.manifest_file = "Cargo.toml"
        elif (repo_path / "go.mod").exists():
            dep_info.package_manager = "go mod"
            dep_info.manifest_file = "go.mod"
        elif (repo_path / "Gemfile").exists():
            dep_info.package_manager = "bundler"
            dep_info.manifest_file = "Gemfile"

        context.dependency_info = dep_info

    def _parse_pyproject(self, filepath: Path, dep_info: DependencyInfo):
        """Parse pyproject.toml for dependencies."""
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                return

        try:
            content = filepath.read_text()
            data = tomllib.loads(content)

            # Poetry dependencies
            if "tool" in data and "poetry" in data["tool"]:
                poetry = data["tool"]["poetry"]
                deps = poetry.get("dependencies", {})
                for name, version in deps.items():
                    if name == "python":
                        dep_info.python_version = str(version)
                    elif isinstance(version, str):
                        dep_info.dependencies[name] = version
                    elif isinstance(version, dict):
                        dep_info.dependencies[name] = version.get("version", "*")

                dev_deps = poetry.get("group", {}).get("dev", {}).get("dependencies", {})
                for name, version in dev_deps.items():
                    if isinstance(version, str):
                        dep_info.dev_dependencies[name] = version
                    elif isinstance(version, dict):
                        dep_info.dev_dependencies[name] = version.get("version", "*")

            # PEP 621 dependencies
            if "project" in data:
                project = data["project"]
                if "requires-python" in project:
                    dep_info.python_version = project["requires-python"]
                for dep in project.get("dependencies", []):
                    # Parse "package>=1.0" format
                    parts = dep.split(">=")
                    if len(parts) == 2:
                        dep_info.dependencies[parts[0].strip()] = f">={parts[1].strip()}"
                    else:
                        dep_info.dependencies[dep.split("[")[0].strip()] = "*"

        except Exception as e:
            logger.debug(f"Failed to parse pyproject.toml: {e}")

    def _parse_requirements(self, filepath: Path, dep_info: DependencyInfo):
        """Parse requirements.txt for dependencies."""
        try:
            content = filepath.read_text()
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue

                # Parse "package==1.0" or "package>=1.0" format
                for sep in ["==", ">=", "<=", "~=", "!="]:
                    if sep in line:
                        parts = line.split(sep)
                        dep_info.dependencies[parts[0].strip()] = f"{sep}{parts[1].strip()}"
                        break
                else:
                    dep_info.dependencies[line.split("[")[0]] = "*"

        except Exception as e:
            logger.debug(f"Failed to parse requirements.txt: {e}")

    def _parse_package_json(self, filepath: Path, dep_info: DependencyInfo):
        """Parse package.json for dependencies."""
        try:
            data = json.loads(filepath.read_text())

            for name, version in data.get("dependencies", {}).items():
                dep_info.dependencies[name] = version

            for name, version in data.get("devDependencies", {}).items():
                dep_info.dev_dependencies[name] = version

            if "engines" in data:
                dep_info.node_version = data["engines"].get("node")

        except Exception as e:
            logger.debug(f"Failed to parse package.json: {e}")

    def _analyze_testing(self, repo_path: Path, context: RepositoryContext):
        """Analyze testing setup."""
        test_info = TestInfo()

        # Check for test directories
        for test_dir in ["tests", "test", "spec", "__tests__"]:
            if (repo_path / test_dir).is_dir():
                test_info.test_directory = test_dir
                break

        # Detect testing framework
        if context.primary_language == "python":
            # Check for pytest
            if (repo_path / "pytest.ini").exists() or (repo_path / "conftest.py").exists():
                test_info.framework = "pytest"
                test_info.has_conftest = (repo_path / "conftest.py").exists()
            elif "pytest" in context.dependency_info.dependencies or "pytest" in context.dependency_info.dev_dependencies:
                test_info.framework = "pytest"
            # Check for unittest
            elif any((repo_path / "tests").rglob("test_*.py")):
                test_info.framework = "unittest"

            # Check for coverage
            if "pytest-cov" in context.dependency_info.dev_dependencies or "coverage" in context.dependency_info.dev_dependencies:
                test_info.coverage_configured = True

            # Count tests
            if test_info.test_directory:
                test_files = list((repo_path / test_info.test_directory).rglob("test_*.py"))
                test_info.test_count = len(test_files)

                # Check for fixtures
                if any("@pytest.fixture" in f.read_text(errors='ignore') for f in test_files[:5] if f.exists()):
                    test_info.has_fixtures = True

        elif context.primary_language in ("javascript", "typescript"):
            # Check for Jest
            if (repo_path / "jest.config.js").exists() or "jest" in context.dependency_info.dev_dependencies:
                test_info.framework = "jest"
                test_info.test_file_pattern = "*.test.{js,ts}"
            # Check for Mocha
            elif "mocha" in context.dependency_info.dev_dependencies:
                test_info.framework = "mocha"
            # Check for Vitest
            elif "vitest" in context.dependency_info.dev_dependencies:
                test_info.framework = "vitest"

        context.test_info = test_info

    def _analyze_patterns(self, repo_path: Path, context: RepositoryContext):
        """Analyze common code patterns."""
        patterns = []

        # Python patterns
        if context.primary_language == "python":
            # Check for FastAPI
            if "fastapi" in context.dependency_info.dependencies:
                patterns.append("FastAPI web framework")
            # Check for Django
            if "django" in context.dependency_info.dependencies:
                patterns.append("Django web framework")
            # Check for Flask
            if "flask" in context.dependency_info.dependencies:
                patterns.append("Flask web framework")
            # Check for Click CLI
            if "click" in context.dependency_info.dependencies:
                patterns.append("Click CLI framework")
            # Check for Pydantic
            if "pydantic" in context.dependency_info.dependencies:
                patterns.append("Pydantic data validation")
            # Check for SQLAlchemy
            if "sqlalchemy" in context.dependency_info.dependencies:
                patterns.append("SQLAlchemy ORM")
            # Check for async
            if "asyncio" in context.dependency_info.dependencies or "httpx" in context.dependency_info.dependencies:
                patterns.append("Async/await patterns")

        # JavaScript/TypeScript patterns
        elif context.primary_language in ("javascript", "typescript"):
            if "react" in context.dependency_info.dependencies:
                patterns.append("React frontend")
            if "vue" in context.dependency_info.dependencies:
                patterns.append("Vue.js frontend")
            if "express" in context.dependency_info.dependencies:
                patterns.append("Express.js backend")
            if "next" in context.dependency_info.dependencies:
                patterns.append("Next.js framework")

        # General patterns
        if (repo_path / ".github" / "workflows").is_dir():
            patterns.append("GitHub Actions CI/CD")
        if (repo_path / "Dockerfile").exists():
            patterns.append("Docker containerization")
        if (repo_path / ".pre-commit-config.yaml").exists():
            patterns.append("Pre-commit hooks")

        context.code_patterns = patterns

    def _read_readme(self, repo_path: Path, context: RepositoryContext):
        """Read README file content."""
        for readme in ["README.md", "README.rst", "README.txt", "README"]:
            readme_path = repo_path / readme
            if readme_path.exists():
                try:
                    context.readme_content = readme_path.read_text(errors='ignore')[:5000]
                    break
                except OSError:
                    pass

    def _find_config_files(self, repo_path: Path, context: RepositoryContext):
        """Find configuration files in the repository."""
        config_files = []

        for pattern in self.CONFIG_PATTERNS:
            if (repo_path / pattern).exists():
                config_files.append(pattern)

        context.config_files = config_files
