"""
Custom exceptions for Forge
"""


class ForgeError(Exception):
    """Base exception for all Forge errors"""
    pass


class ConfigurationError(ForgeError):
    """Configuration-related errors"""
    pass


class PatternStoreError(ForgeError):
    """Pattern store errors"""
    pass


class GenerationError(ForgeError):
    """Code generation errors"""
    pass


class TestExecutionError(ForgeError):
    """Test execution errors"""
    pass


class StateError(ForgeError):
    """State management errors"""
    pass


class GitError(ForgeError):
    """Git operation errors"""
    pass


class IntegrationError(ForgeError):
    """External integration errors"""
    pass
