class FixerError(RuntimeError):
    """Base class for all fixer related errors"""
    pass


class StrategyError(FixerError):
    """Strategy configuration error"""
    pass
