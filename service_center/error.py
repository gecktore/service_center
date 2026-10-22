class ValidationError(ValueError):... 
"""Ошибка проверки входных данных"""

class NotFoundError(LookupError):
    """Запрашиваемый объект не найден."""


class BusinessRuleError(Exception):
    """Нарушение бизнес-правил приложения."""

class StorageError(Exception):
    """Ошибка чтения, записи или проверки файла данных."""