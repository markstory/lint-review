class FixerError(RuntimeError):
    """Base class for all fixer related errors"""
    pass


class ConfigurationError(FixerError):
    """Workflow/fixer configuration error"""
    pass


class WorkflowError(FixerError):
    """Workflow execution error error.
    Will be reported as an issue comment."""
    pass
