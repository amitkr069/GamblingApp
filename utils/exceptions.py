class ValidationException(Exception):
    """Base exception for all validation errors."""
    def __init__(self, message: str, error_type: str = "SYSTEM_ERROR", field_name: str = None, attempted_value: str = None):
        super().__init__(message)
        self.error_type = error_type
        self.field_name = field_name
        self.attempted_value = attempted_value

class StakeValidationException(ValidationException):
    """Specific to stake-related errors (e.g., negative stakes)."""
    def __init__(self, message: str, field_name: str = "stake", attempted_value: str = None):
        super().__init__(message, error_type="STAKE_ERROR", field_name=field_name, attempted_value=attempted_value)

class BetValidationException(ValidationException):
    """Specific to bet amount errors (e.g., exceeding current balance)."""
    def __init__(self, message: str, field_name: str = "bet_amount", attempted_value: str = None):
        super().__init__(message, error_type="BET_ERROR", field_name=field_name, attempted_value=attempted_value)

class LimitValidationException(ValidationException):
    """Specific to limit boundary issues (e.g., lower limit > upper limit)."""
    def __init__(self, message: str, field_name: str = "limits", attempted_value: str = None):
        super().__init__(message, error_type="LIMIT_ERROR", field_name=field_name, attempted_value=attempted_value)