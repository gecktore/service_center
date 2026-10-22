
"""Сохранение и загрузка данных сервисного центра."""

import json
import os
from pathlib import Path

from .error import StorageError
from .models import (
    Diagnostics,
    Level,
    Master,
    PaidRepair,
    Status,
    WarrantyRepair,
)


class JsonStorage:
    """Хранилище данных в формате JSON."""

    def __init__(self, path="data/service_center.json"):
        """Создаёт хранилище с указанным путём."""
        self.path = Path(path)

    def save(self, center):
        """Атомарно сохраняет мастеров, заявки и счётчики ID."""
        data = {
            "version": 1,
            "next_master_id": center.next_master_id,
            "next_request_id": center.next_request_id,
            "masters": [
                {
                    "id": master.id,
                    "name": master.name,
                    "phone": master.phone,
                    "level": master.level.value,
                    "accruals": master.accruals,
                }
                for master in center.masters
            ],
            "requests": [
                {
                    "id": request.id,
                    "kind": self._get_kind(request),
                    "device": request.device,
                    "urgency": request.urgency,
                    "status": request.status.value,
                    "executor_id": (
                        request.executor.id
                        if request.executor is not None
                        else None
                    ),
                    "reviewer_id": (
                        request.reviewer.id
                        if request.reviewer is not None
                        else None
                    ),
                    "dependency_id": (
                        request.dependency.id
                        if request.dependency is not None
                        else None
                    ),
                    "return_count": request.return_count,
                    "cost": (
                        request.cost
                        if isinstance(request, PaidRepair)
                        else None
                    ),
                    "complexity": (
                        request.complexity
                        if isinstance(request, WarrantyRepair)
                        else None
                    ),
                }
                for request in center.requests
            ],
        }

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(".tmp")

        try:
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
                file.flush()
                os.fsync(file.fileno())

            os.replace(temporary_path, self.path)

        except (OSError, TypeError, ValueError) as exc:
            raise StorageError(
                f"Не удалось сохранить данные: {exc}"
            ) from exc

        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    @staticmethod
    def _get_kind(request):
        """Возвращает название вида заявки."""
        if isinstance(request, PaidRepair):
            return "платный"
        if isinstance(request, WarrantyRepair):
            return "гарантийный"
        if isinstance(request, Diagnostics):
            return "диагностика"

        raise StorageError("Неизвестный вид заявки.")

    def load(self, center_class):
        """Загружает данные или создаёт пустой сервисный центр."""
        if not self.path.exists():
            return center_class()

        try:
            with self.path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            return self._restore(data, center_class)

        except StorageError:
            raise
        except Exception as exc:
            raise StorageError(
                f"Не удалось загрузить данные. Файл повреждён: {exc}"
            ) from exc

    def _restore(self, data, center_class):
        """Проверяет данные и восстанавливает объекты."""
        required_keys = {
            "version",
            "next_master_id",
            "next_request_id",
            "masters",
            "requests",
        }

        if not isinstance(data, dict) or not required_keys.issubset(data):
            raise StorageError("В файле отсутствуют обязательные поля.")

        if type(data["version"]) is not int or data["version"] != 1:
            raise StorageError("Неподдерживаемая версия файла.")

        next_master_id = data["next_master_id"]
        next_request_id = data["next_request_id"]

        if (
            type(next_master_id) is not int
            or next_master_id < 1
            or type(next_request_id) is not int
            or next_request_id < 1
        ):
            raise StorageError("Некорректные счётчики идентификаторов.")

        if (
            not isinstance(data["masters"], list)
            or not isinstance(data["requests"], list)
        ):
            raise StorageError("Список мастеров или заявок повреждён.")

        center = center_class()
        masters_by_id = {}
        requests_by_id = {}

        # Восстанавливаем мастеров.
        for item in data["masters"]:
            if not isinstance(item, dict):
                raise StorageError("Некорректная запись мастера.")

            master = Master(
                item["id"],
                item["name"],
                item["phone"],
            )

            if type(master.id) is not int or master.id < 1:
                raise StorageError("Некорректный ID мастера.")

            if master.id in masters_by_id:
                raise StorageError("Обнаружен повторяющийся ID мастера.")

            phone_digits = "".join(
                character for character in master.phone
                if character.isdigit()
            )

            for existing in center.masters:
                existing_digits = "".join(
                    character for character in existing.phone
                    if character.isdigit()
                )

                if phone_digits == existing_digits:
                    raise StorageError("Обнаружен повторяющийся телефон.")

            level = Level(item["level"])
            accruals = item["accruals"]

            if type(accruals) is not int or accruals < 0:
                raise StorageError("Некорректные начисления мастера.")

            expected_level = (
                Level.SENIOR
                if accruals >= 15000
                else Level.MASTER
                if accruals >= 5000
                else Level.INTERN
            )

            if level != expected_level:
                raise StorageError(
                    "Уровень мастера не соответствует начислениям."
                )

            # Специальное восстановление сохранённого состояния.
            master._level = level
            master._accruals = accruals

            masters_by_id[master.id] = master
            center.masters.append(master)

        # Восстанавливаем заявки.
        for item in data["requests"]:
            if not isinstance(item, dict):
                raise StorageError("Некорректная запись заявки.")

            kind = item["kind"]

            if kind == "платный":
                request = PaidRepair(
                    item["id"],
                    item["device"],
                    item["cost"],
                    item["urgency"],
                )
            elif kind == "гарантийный":
                request = WarrantyRepair(
                    item["id"],
                    item["device"],
                    item["complexity"],
                    item["urgency"],
                )
            elif kind == "диагностика":
                request = Diagnostics(
                    item["id"],
                    item["device"],
                    item["urgency"],
                )
            else:
                raise StorageError("Неизвестный вид заявки.")

            if type(request.id) is not int or request.id < 1:
                raise StorageError("Некорректный ID заявки.")

            if request.id in requests_by_id:
                raise StorageError("Обнаружен повторяющийся ID заявки.")

            requests_by_id[request.id] = request
            center.requests.append(request)

        # Восстанавливаем связи между объектами.
        for item in data["requests"]:
            request = requests_by_id[item["id"]]

            executor_id = item["executor_id"]
            reviewer_id = item["reviewer_id"]
            dependency_id = item["dependency_id"]

            if executor_id is not None and executor_id not in masters_by_id:
                raise StorageError("Исполнитель заявки не найден.")

            if reviewer_id is not None and reviewer_id not in masters_by_id:
                raise StorageError("Проверяющий заявки не найден.")

            if (
                dependency_id is not None
                and dependency_id not in requests_by_id
            ):
                raise StorageError("Зависимая заявка не найдена.")

            request._status = Status(item["status"])
            request._executor = masters_by_id.get(executor_id)
            request._reviewer = masters_by_id.get(reviewer_id)
            request._dependency = requests_by_id.get(dependency_id)
            request._return_count = item["return_count"]

        # Проверяем состояния заявок и циклы зависимостей.
        for request in center.requests:
            self._validate_request(request)

            current = request.dependency
            visited = {request.id}

            while current is not None:
                if current.id in visited:
                    raise StorageError("Обнаружен цикл зависимостей.")

                visited.add(current.id)
                current = current.dependency

        # Проверяем нагрузку мастеров.
        for master in center.masters:
            if center.get_load(master) > center.get_limit(master):
                raise StorageError(
                    f"Превышен лимит нагрузки мастера {master.name}."
                )

        if masters_by_id and next_master_id <= max(masters_by_id):
            raise StorageError("Некорректный счётчик ID мастеров.")

        if requests_by_id and next_request_id <= max(requests_by_id):
            raise StorageError("Некорректный счётчик ID заявок.")

        center.next_master_id = next_master_id
        center.next_request_id = next_request_id

        return center

    @staticmethod
    def _validate_request(request):
        """Проверяет допустимость состояния заявки."""
        if (
            type(request.return_count) is not int
            or request.return_count < 0
        ):
            raise StorageError("Некорректное число возвратов.")

        if (
            isinstance(request, Diagnostics)
            and request.return_count != 0
        ):
            raise StorageError("У диагностики число возвратов должно быть 0.")

        if request.status == Status.ACCEPTED:
            valid = (
                request.executor is None
                and request.reviewer is None
                and request.return_count == 0
            )

        elif request.status == Status.IN_PROGRESS:
            valid = (
                request.executor is not None
                and request.reviewer is None
            )

        elif request.status == Status.REVIEW:
            valid = (
                not isinstance(request, Diagnostics)
                and request.executor is not None
                and request.reviewer is None
            )

        elif request.status == Status.READY:
            if isinstance(request, Diagnostics):
                valid = (
                    request.executor is not None
                    and request.reviewer is None
                )
            else:
                valid = (
                    request.executor is not None
                    and request.reviewer is not None
                    and request.executor.id != request.reviewer.id
                )

        elif request.status == Status.CANCELLED:
            valid = (
                request.executor is None
                and request.reviewer is None
                and request.return_count == 0
            )

        else:
            valid = False

        if not valid:
            raise StorageError(
                f"Недопустимое состояние заявки №{request.id}."
            )
