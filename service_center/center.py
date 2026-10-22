from models import ( Master, PaidRepair, WarrantyRepair, Diagnostics, Status, Level, ) 
from error import ValidationError, NotFoundError, BusinessRuleError

class ServiceCenter: 
    """Управляет мастерами и заявками сервисного центра."""
    
def __init__(self):
    """Создаёт пустой сервисный центр."""
    self.masters = []
    self.requests = []
    self.next_master_id = 1
    self.next_request_id = 1

def add_master(self, name, phone):
    """Добавляет нового мастера с уникальным телефоном."""
    master = Master(self.next_master_id, name, phone)

    for existing in self.masters:
        phone1 = "".join(filter(str.isdigit, existing.phone))
        phone2 = "".join(filter(str.isdigit, master.phone))

        if phone1 == phone2:
            raise BusinessRuleError("Мастер с таким телефоном уже существует.")

    self.masters.append(master)
    self.next_master_id += 1
    return master

def get_master(self, master_id):
    """Находит мастера по идентификатору."""
    for master in self.masters:
        if master.id == master_id:
            return master

    raise NotFoundError(f"Мастер №{master_id} не найден.")

def get_request(self, request_id):
    """Находит заявку по идентификатору."""
    for request in self.requests:
        if request.id == request_id:
            return request

    raise NotFoundError(f"Заявка №{request_id} не найдена.")

def create_request(
    self, kind, device, urgency=3, cost=None, complexity=None
):
    """Создаёт заявку указанного вида."""
    request_id = self.next_request_id

    if kind == "платный":
        if cost is None:
            raise ValidationError("Укажите стоимость ремонта.")
        request = PaidRepair(request_id, device, cost, urgency)

    elif kind == "гарантийный":
        if complexity is None:
            raise ValidationError("Укажите сложность ремонта.")
        request = WarrantyRepair(request_id, device, complexity, urgency)

    elif kind == "диагностика":
        request = Diagnostics(request_id, device, urgency)

    else:
        raise ValidationError("Неизвестный вид заявки.")

    self.requests.append(request)
    self.next_request_id += 1
    return request

def get_load(self, master):
    """Считает активные заявки мастера."""
    count = 0

    for request in self.requests:
        if (
            request.executor == master
            and request.status in (Status.IN_PROGRESS, Status.REVIEW)
        ):
            count += 1

    return count

def get_limit(self, master):
    """Возвращает лимит заявок для уровня мастера."""
    if master.level == Level.INTERN:
        return 1
    if master.level == Level.MASTER:
        return 2
    return 3

def take_in_repair(self, request_id, master_id):
    """Назначает исполнителя и переводит заявку в ремонт."""
    request = self.get_request(request_id)
    master = self.get_master(master_id)

    if request.status != Status.ACCEPTED:
        raise BusinessRuleError("В ремонт можно взять только принятую заявку.")

    load = self.get_load(master)
    limit = self.get_limit(master)

    if load >= limit:
        raise BusinessRuleError(
            f"У мастера {master.name} уже {load} заявок. Лимит: {limit}."
        )

    if request.dependency is not None:
        if request.dependency.status != Status.READY:
            raise BusinessRuleError("Зависимая заявка ещё не готова.")

    if isinstance(request, PaidRepair) and request.cost > 30000:
        if master.level != Level.SENIOR:
            raise BusinessRuleError(
                "Ремонт дороже 30000 рублей может взять только старший мастер."
            )

    if isinstance(request, WarrantyRepair) and request.complexity == 3:
        if master.level == Level.INTERN:
            raise BusinessRuleError(
                "Гарантийный ремонт сложности 3 доступен только мастеру "
                "или старшему мастеру."
            )

    request.take_in_repair(master)

def submit_for_review(self, request_id):
    """Сдаёт заявку на проверку или завершает диагностику."""
    request = self.get_request(request_id)
    request.submit_for_review()

def accept(self, request_id, reviewer_id):
    """Принимает результат ремонта."""
    request = self.get_request(request_id)
    reviewer = self.get_master(reviewer_id)
    request.accept(reviewer)

def return_for_rework(self, request_id, reviewer_id):
    """Возвращает ремонт на доработку."""
    request = self.get_request(request_id)
    reviewer = self.get_master(reviewer_id)
    request.return_for_rework(reviewer)

def set_dependency(self, request_id, dependency_id):
    """Устанавливает зависимость между заявками."""
    request = self.get_request(request_id)
    dependency = self.get_request(dependency_id)

    if request.status != Status.ACCEPTED:
        raise BusinessRuleError(
            "Зависимость можно менять только у принятой заявки."
        )

    if request.id == dependency.id:
        raise BusinessRuleError("Заявка не может зависеть от самой себя.")

    if dependency.status == Status.CANCELLED:
        raise BusinessRuleError("Нельзя зависеть от отменённой заявки.")

    current = dependency

    while current is not None:
        if current.id == request.id:
            raise BusinessRuleError("Нельзя создавать цикл зависимостей.")
        current = current.dependency

    request._dependency = dependency

def remove_dependency(self, request_id):
    """Удаляет зависимость заявки."""
    request = self.get_request(request_id)

    if request.status != Status.ACCEPTED:
        raise BusinessRuleError(
            "Зависимость можно менять только у принятой заявки."
        )

    request._dependency = None

def cancel_request(self, request_id):
    """Отменяет заявку, если от неё не зависят другие активные заявки."""
    request = self.get_request(request_id)

    for other in self.requests:
        if (
            other.dependency == request
            and other.status != Status.CANCELLED
        ):
            raise BusinessRuleError(
                "Нельзя отменить заявку: от неё зависит другая заявка."
            )

    request.cancel()

def update_device(self, request_id, device):
    """Изменяет описание устройства."""
    self.get_request(request_id).update_device(device)

def update_urgency(self, request_id, urgency):
    """Изменяет срочность заявки."""
    self.get_request(request_id).update_urgency(urgency)

def update_cost(self, request_id, cost):
    """Изменяет стоимость платного ремонта."""
    request = self.get_request(request_id)

    if not isinstance(request, PaidRepair):
        raise BusinessRuleError("Это не платный ремонт.")

    request.update_cost(cost)

def update_complexity(self, request_id, complexity):
    """Изменяет сложность гарантийного ремонта."""
    request = self.get_request(request_id)

    if not isinstance(request, WarrantyRepair):
        raise BusinessRuleError("Это не гарантийный ремонт.")

    request.update_complexity(complexity)

def delete_request(self, request_id):
    """Удаляет принятую заявку, от которой никто не зависит."""
    request = self.get_request(request_id)

    if request.status != Status.ACCEPTED:
        raise BusinessRuleError("Удалить можно только принятую заявку.")

    for other in self.requests:
        if other.dependency == request:
            raise BusinessRuleError(
                "Нельзя удалить заявку, от которой кто-то зависит."
            )

    self.requests.remove(request)

def search_requests(self, text=None, status=None, kind=None):
    """Ищет заявки по описанию, статусу и виду."""
    result = []

    for request in self.requests:
        if text and text.casefold() not in request.device.casefold():
            continue

        if status is not None and request.status != Status(status):
            continue

        if kind == "платный" and not isinstance(request, PaidRepair):
            continue
        if kind == "гарантийный" and not isinstance(request, WarrantyRepair):
            continue
        if kind == "диагностика" and not isinstance(request, Diagnostics):
            continue

        if kind not in (None, "платный", "гарантийный", "диагностика"):
            raise ValidationError("Неизвестный вид заявки.")

        result.append(request)

    return result

def summary(self):
    """Формирует сводку по статусам, видам и ожидаемой выручке."""
    by_status = {status.value: 0 for status in Status}
    by_kind = {
        "платный": 0,
        "гарантийный": 0,
        "диагностика": 0,
    }
    revenue = 0

    for request in self.requests:
        by_status[request.status.value] += 1

        if isinstance(request, PaidRepair):
            by_kind["платный"] += 1

            if request.status not in (Status.READY, Status.CANCELLED):
                revenue += request.cost

        elif isinstance(request, WarrantyRepair):
            by_kind["гарантийный"] += 1

        else:
            by_kind["диагностика"] += 1

    return {
        "by_status": by_status,
        "by_kind": by_kind,
        "expected_revenue": revenue,
    }

def rating(self):
    """Формирует рейтинг мастеров по начислениям."""
    result = sorted(
        self.masters,
        key=lambda master: -master.accruals,
    )

    rating = []

    for master in result:
        rating.append({
            "master": master,
            "accruals": master.accruals,
            "level": master.level,
            "load": f"{self.get_load(master)} из {self.get_limit(master)}",
        })

    return rating
