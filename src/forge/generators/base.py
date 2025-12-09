"""
Abstract base class for code generators

Defines the interface that all code generation backends must implement.
Supports streaming output for real-time progress feedback.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, AsyncIterator, TYPE_CHECKING
from enum import Enum
from datetime import datetime

from forge.utils.errors import ForgeError

if TYPE_CHECKING:
    from forge.core.streaming import StreamEmitter


class GeneratorError(ForgeError):
    """Errors during code generation"""
    pass


class GeneratorBackend(Enum):
    """Supported generator backends."""
    CODEGEN_API = "codegen_api"
    CLAUDE_CODE = "claude_code"


@dataclass
class GenerationContext:
    """
    Context for code generation.

    Contains all information needed for a generator to produce code.
    """
    task_id: str
    specification: str
    project_context: str
    tech_stack: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    knowledgeforge_patterns: List[str] = field(default_factory=list)
    file_structure: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "task_id": self.task_id,
            "specification": self.specification,
            "project_context": self.project_context,
            "tech_stack": self.tech_stack,
            "dependencies": self.dependencies,
            "knowledgeforge_patterns": self.knowledgeforge_patterns,
            "file_structure": self.file_structure,
            "metadata": self.metadata
        }


@dataclass
class GenerationResult:
    """
    Result of code generation.

    Contains generated files, metrics, and any errors encountered.
    """
    success: bool
    files: Dict[str, str] = field(default_factory=dict)  # filepath -> content
    duration_seconds: float = 0.0
    tokens_used: Optional[int] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "success": self.success,
            "files": self.files,
            "duration_seconds": self.duration_seconds,
            "tokens_used": self.tokens_used,
            "error": self.error,
            "metadata": self.metadata,
            "generated_at": self.generated_at,
            "file_count": len(self.files)
        }

    def merge(self, other: 'GenerationResult') -> 'GenerationResult':
        """
        Merge another generation result into this one.

        Used for combining results from multiple tasks.
        """
        return GenerationResult(
            success=self.success and other.success,
            files={**self.files, **other.files},
            duration_seconds=self.duration_seconds + other.duration_seconds,
            tokens_used=(self.tokens_used or 0) + (other.tokens_used or 0) if self.tokens_used or other.tokens_used else None,
            error=self.error or other.error,
            metadata={**self.metadata, **other.metadata}
        )


class CodeGenerator(ABC):
    """
    Abstract base class for code generators.

    All generator backends must implement this interface.
    Supports both synchronous and streaming generation modes.
    """

    @abstractmethod
    async def generate(self, context: GenerationContext) -> GenerationResult:
        """
        Generate code for a task.

        Args:
            context: Generation context with specification and patterns

        Returns:
            GenerationResult with generated files or error

        Raises:
            GeneratorError: If generation fails
        """
        pass

    async def generate_streaming(
        self,
        context: GenerationContext,
        emitter: 'StreamEmitter'
    ) -> GenerationResult:
        """
        Generate code with streaming output.

        Override this method to provide streaming support.
        Default implementation falls back to non-streaming generate().

        Args:
            context: Generation context with specification and patterns
            emitter: StreamEmitter for progress and content events

        Returns:
            GenerationResult with generated files or error

        Raises:
            GeneratorError: If generation fails
        """
        # Default: fall back to non-streaming
        await emitter.started(f"Generating {context.task_id}...")
        await emitter.stage("generation", "Generating code...")

        try:
            result = await self.generate(context)

            if result.success:
                # Emit file events for each generated file
                for file_path, content in result.files.items():
                    await emitter.file_completed(file_path, len(content))

                await emitter.completed(
                    f"Generated {len(result.files)} files",
                    metadata={"files": list(result.files.keys())}
                )
            else:
                await emitter.failed(result.error or "Generation failed")

            return result

        except Exception as e:
            await emitter.failed(str(e))
            raise

    def supports_streaming(self) -> bool:
        """
        Whether this generator supports streaming output.

        Override and return True if generate_streaming() is implemented.

        Returns:
            True if streaming is supported
        """
        return False

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if generator backend is available.

        Returns:
            True if backend is healthy and ready to generate
        """
        pass

    @abstractmethod
    def estimate_duration(self, context: GenerationContext) -> int:
        """
        Estimate generation duration in seconds.

        Args:
            context: Generation context to estimate for

        Returns:
            Estimated duration in seconds
        """
        pass

    @abstractmethod
    def supports_parallel(self) -> bool:
        """
        Whether this generator supports parallel execution.

        Returns:
            True if multiple tasks can be generated in parallel
        """
        pass

    @abstractmethod
    def max_context_tokens(self) -> int:
        """
        Maximum context window size.

        Returns:
            Maximum tokens that can fit in context
        """
        pass

    def get_backend_name(self) -> str:
        """Get human-readable backend name"""
        return self.__class__.__name__

    def validate_context(self, context: GenerationContext) -> bool:
        """
        Validate generation context.

        Args:
            context: Context to validate

        Returns:
            True if context is valid

        Raises:
            GeneratorError: If context is invalid
        """
        if not context.task_id:
            raise GeneratorError("task_id is required")

        if not context.specification:
            raise GeneratorError("specification is required")

        if not context.project_context:
            raise GeneratorError("project_context is required")

        return True
