import re
from enum import StrEnum
from .error import BusinessRuleError, ValidationError


class Level(StrEnum):
    """Уровни мастера"""

    INTERN = "стажер"
    MASTER = "мастер"
    SENIOR = "старший мастер"

class Status(StrEnum):
    """Статус заявки"""

    ACCEPTED = "принята"
    IN_PROGRESS = "в ремонте"
    REVIEW = "на проверке"
    READY = "готово"
    CANCELLED = "отменена"

def normalize_text(value:str) -> str:
    """Удаляет пробелы по краям и сокращает повторяющиеся пробелы"""

    if not isinstance(value, str):
        raise ValidationError("Передается не строка")
    return " ".join(value.split())

def validate_id(value: int, entity: str) -> int:
    """Проверяет id"""

    if type(value) is not int:
        raise ValidationError(f"ID {entity} должно быть числом")
    if value < 1:
        raise ValidationError(f"ID {entity} должно быть положительным числом")
    return value

class Master:
    """Мастер Феликс как из Ральфа"""

    def __init__(self, master_id:int, name:str, phone:str):
        self._id = validate_id(master_id, "мастера")
        self._name = self._validate_name(name)
        self._phone = self._validate_phone(phone)
        self._level = Level.INTERN
        self._accruals = 0


    @staticmethod
    def _validate_name(name:str) -> str:
        """Нормализует имя и проверяет его длину"""

        name = normalize_text(name)
        if not 2 <= len(name) <= 40:
            raise ValidationError("Имя должно быть от 2 до 40 символов")

        return name

    @staticmethod
    def _validate_phone(phone:str):
        """Нормализует телефон и проверяет формат и количество цифр"""

        phone = normalize_text(phone)

        if not re.fullmatch(r"\+?[0-9 ()-]+", phone):
            raise ValidationError("Телефон может содержать цифры, пробелы, дефисы, скобки и плюс только в начале")
        digits = "".join(char for char in phone if char.isdigit())
        if not 10 <= len(digits) <= 15:
            raise ValidationError("Телефон должен содержать от 10 до 15 цифр")

        return phone

    @property
    def id(self) -> int:
        """Возвращает ID мастера"""
        return self._id

    @property
    def name(self) -> str:
        """Возвращает имя мастера"""
        return self._name

    @property
    def phone(self) -> str:
        """Возвращает телефон мастера"""
        return self._phone

    @property
    def level(self) -> Level:
        """Возвращает уровень мастера"""
        return self._level

    @property
    def accruals(self) -> int:
        """Возвращает сумму начислений мастера"""
        return self._accruals

    def __str__(self) -> str:
        """Возвращает текстовое представление мастера"""
        return (
            f"Мастер #{self.id}: {self.name}, "
            f"телефон: {self.phone}, уровень: {self.level.value}, "
            f"начисления: {self.accruals} ₽"
        )


class RepairRequest:
    """Базовый класс заявки сервисного центра"""

    KIND = "заявка"

    def __init__(
        self,
        request_id: int,
        device: str,
        urgency: int = 3,
    ) -> None:
        self._id = validate_id(request_id, "заявки")
        self._device = self._validate_device(device)
        self._urgency = self._validate_urgency(urgency)
        self._status = Status.ACCEPTED
        self._executor: Master | None = None
        self._reviewer: Master | None = None
        self._dependency: RepairRequest | None = None
        self._return_count = 0

    @staticmethod
    def _validate_device(device: str) -> str:
        """Нормализует описание устройства и проверяет его длину"""

        device = normalize_text(device)
        if not 1 <= len(device) <= 80:
            raise ValidationError(
                "Описание устройства должно содержать от 1 до 80 символов"
            )
        return device

    @staticmethod
    def _validate_urgency(urgency: int) -> int:
        """Проверяет срочность от 1 до 5."""

        if type(urgency) is not int or not 1 <= urgency <= 5:
            raise ValidationError("Срочность должна быть целым числом от 1 до 5")
        return urgency

    @property
    def id(self) -> int:
        """Возвращает ID заявки"""
        return self._id

    @property
    def device(self) -> str:
        """Возвращает описание устройства"""
        return self._device

    @property
    def urgency(self) -> int:
        """Возвращает срочность заявки"""
        return self._urgency

    @property
    def status(self) -> Status:
        """Возвращает статус заявки"""
        return self._status

    @property
    def executor(self) -> Master | None:
        """Возвращает исполнителя заявки"""
        return self._executor

    @property
    def reviewer(self) -> Master | None:
        """Возвращает проверяющего заявку"""
        return self._reviewer

    @property
    def dependency(self) -> "RepairRequest | None":
        """Возвращает зависимую заявку"""
        return self._dependency

    @property
    def return_count(self) -> int:
        """Возвращает число возвратов на доработку"""
        return self._return_count

    @property
    def kind(self) -> str:
        """Возвращает название вида заявки"""
        return self.KIND

    def __str__(self) -> str:
        """Возвращает текстовое представление заявки."""
        return (
            f"Заявка #{self.id}: {self.device}, "
            f"вид: {self.kind}, статус: {self.status.value}, "
            f"срочность: {self.urgency}"
        )


    def take_in_repair(self, master: Master) -> None:
        """Назначает мастера и переводит заявку в ремонт."""
        if self._status != Status.ACCEPTED:
            raise BusinessRuleError(
                "В ремонт можно взять только принятую заявку."
            )
        self._executor = master
        self._status = Status.IN_PROGRESS

    def submit_for_review(self) -> None:
        """Передаёт ремонт на проверку или завершает диагностику."""
        if self._status != Status.IN_PROGRESS:
            raise BusinessRuleError(
                "На проверку можно передать только заявку в ремонте."
            )

        if isinstance(self, Diagnostics):
            self._status = Status.READY
        else:
            self._status = Status.REVIEW

    def accept(self, reviewer: Master) -> None:
        """Принимает результат ремонта."""
        if self._status != Status.REVIEW:
            raise BusinessRuleError(
                "Принять можно только заявку на проверке."
            )
        if reviewer == self._executor:
            raise BusinessRuleError(
                "Исполнитель не может проверять собственную работу."
            )

        self._reviewer = reviewer
        self._status = Status.READY

    def return_for_rework(self, reviewer: Master) -> None:
        """Возвращает ремонт на доработку."""
        if self._status != Status.REVIEW:
            raise BusinessRuleError(
                "На доработку можно вернуть только заявку на проверке."
            )
        if reviewer == self._executor:
            raise BusinessRuleError(
                "Исполнитель не может проверять собственную работу."
            )

        self._reviewer = None
        self._return_count += 1
        self._status = Status.IN_PROGRESS

    def cancel(self) -> None:
        """Отменяет заявку."""
        if self._status not in (Status.ACCEPTED,):
            raise BusinessRuleError(
                "Отменить можно только принятую заявку."
            )
        self._status = Status.CANCELLED

    def update_device(self, device: str) -> None:
        """Изменяет описание устройства."""
        self._device = self._validate_device(device)

    def update_urgency(self, urgency: int) -> None:
        """Изменяет срочность заявки."""
        self._urgency = self._validate_urgency(urgency)



class PaidRepair(RepairRequest):
    """Заявка на платный ремонт"""

    KIND = "платный ремонт"

    def __init__(
        self,
        request_id: int,
        device: str,
        cost: int,
        urgency: int = 3,
    ) -> None:
        self._cost = self._validate_cost(cost)
        super().__init__(request_id, device, urgency)

    @staticmethod
    def _validate_cost(cost: int) -> int:
        """Проверяет стоимость от 500 до 100000 рублей."""
        if type(cost) is not int or not 500 <= cost <= 100_000:
            raise ValidationError(
                "Стоимость должна быть целым числом от 500 до 100000 ₽."
            )
        return cost

    @property
    def cost(self) -> int:
        """Возвращает стоимость ремонта"""
        return self._cost

    def __str__(self) -> str:
        """Возвращает текстовое представление платного ремонта"""
        return f"{super().__str__()}, стоимость: {self.cost} ₽"

    def update_cost(self, cost: int) -> None:
        """Изменяет стоимость платного ремонта."""
        self._cost = self._validate_cost(cost) 


class WarrantyRepair(RepairRequest):
    """Заявка на гарантийный ремонт"""

    KIND = "гарантийный ремонт"

    def __init__(
        self,
        request_id: int,
        device: str,
        complexity: int,
        urgency: int = 3,
    ) -> None:
        self._complexity = self._validate_complexity(complexity)
        super().__init__(request_id, device, urgency)

    @staticmethod
    def _validate_complexity(complexity: int) -> int:
        """Проверяет сложность от 1 до 3."""
        if type(complexity) is not int or not 1 <= complexity <= 3:
            raise ValidationError("Сложность должна быть целым числом от 1 до 3.")
        return complexity

    @property
    def complexity(self) -> int:
        """Возвращает сложность ремонта"""
        return self._complexity

    def update_complexity(self, complexity: int) -> None:
        """Изменяет сложность гарантийного ремонта."""
        self._complexity = self._validate_complexity(complexity)

    def __str__(self) -> str:
        """Возвращает текстовое представление гарантийного ремонта"""
        return f"{super().__str__()}, сложность: {self.complexity}"


class Diagnostics(RepairRequest):
    """Заявка на диагностику"""

    KIND = "диагностика"