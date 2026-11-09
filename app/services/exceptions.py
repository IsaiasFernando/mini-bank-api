class BankingError(Exception):
    """Base class for expected business-rule errors."""


class InsufficientFunds(BankingError):
    pass


class AccountNotFound(BankingError):
    pass


class SameAccount(BankingError):
    pass


class InvalidAmount(BankingError):
    pass
