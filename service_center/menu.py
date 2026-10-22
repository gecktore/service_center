"""Консольное меню сервисного центра."""

from .center import ServiceCenter
from .error import (
    BusinessRuleError,
    NotFoundError,
    StorageError,
    ValidationError,
)
from .storage import JsonStorage


def read_int(prompt):
    """Запрашивает целое число."""
    while True:
        value = input(prompt).strip()
        try:
            return int(value)
        except ValueError:
            print("Ошибка: введите целое число.")


def show_menu():
    """Выводит главное меню."""
    print("\n=== Сервисный центр ===")
    print("1. Мастера")
    print("2. Заявки")
    print("3. Поиск заявок")
    print("4. Сводка")
    print("5. Рейтинг мастеров")
    print("0. Выход")


def show_masters(center):
    """Показывает список мастеров."""
    print("\n=== Мастера ===")

    if not center.masters:
        print("Мастеров пока нет.")
        return

    for master in center.masters:
        print(master)


def show_requests(center):
    """Показывает список заявок."""
    print("\n=== Заявки ===")

    if not center.requests:
        print("Заявок пока нет.")
        return

    for request in center.requests:
        print(request)


def add_master_menu(center):
    """Добавляет мастера."""
    print("\n=== Добавление мастера ===")
    name = input("Имя мастера: ").strip()
    phone = input("Телефон: ").strip()

    master = center.add_master(name, phone)
    print(f"Мастер добавлен: {master}")


def create_request_menu(center):
    """Создаёт заявку."""
    print("\n=== Создание заявки ===")
    print("1. Платный ремонт")
    print("2. Гарантийный ремонт")
    print("3. Диагностика")

    choice = input("Вид заявки: ").strip()

    kinds = {
        "1": "платный",
        "2": "гарантийный",
        "3": "диагностика",
    }

    if choice not in kinds:
        print("Неизвестный вид заявки.")
        return

    device = input("Описание устройства: ").strip()
    urgency = read_int("Срочность (1–5, по умолчанию 3): ")

    if kinds[choice] == "платный":
        cost = read_int("Стоимость ремонта: ")
        request = center.create_request(
            "платный",
            device,
            urgency=urgency,
            cost=cost,
        )
    elif kinds[choice] == "гарантийный":
        complexity = read_int("Сложность ремонта (1–3): ")
        request = center.create_request(
            "гарантийный",
            device,
            urgency=urgency,
            complexity=complexity,
        )
    else:
        request = center.create_request(
            "диагностика",
            device,
            urgency=urgency,
        )

    print(f"Заявка создана: {request}")


def show_summary(center):
    """Выводит сводку сервисного центра."""
    summary = center.summary()

    print("\n=== Сводка ===")
    print("Заявки по статусам:")

    for status, count in summary["by_status"].items():
        print(f"  {status}: {count}")

    print("\nЗаявки по видам:")

    for kind, count in summary["by_kind"].items():
        print(f"  {kind}: {count}")

    print(
        f"\nОжидаемая выручка: "
        f"{summary['expected_revenue']} ₽"
    )


def show_rating(center):
    """Выводит рейтинг мастеров."""
    rating = center.rating()

    print("\n=== Рейтинг мастеров ===")

    if not rating:
        print("Мастеров пока нет.")
        return

    for position, item in enumerate(rating, start=1):
        master = item["master"]
        print(
            f"{position}. {master.name} | "
            f"Начисления: {item['accruals']} ₽ | "
            f"Уровень: {item['level'].value} | "
            f"Нагрузка: {item['load']}"
        )


def search_requests_menu(center):
    """Ищет заявки по описанию."""
    query = input("Введите текст для поиска: ").strip()
    requests = center.search_requests(text=query or None)

    if not requests:
        print("Заявки не найдены.")
        return

    for request in requests:
        print(request)


def run():
    """Запускает консольное приложение."""
    storage = JsonStorage()

    try:
        center = storage.load(ServiceCenter)
    except StorageError as exc:
        print(f"Ошибка загрузки данных: {exc}")
        return

    print("Добро пожаловать в сервисный центр!")

    while True:
        show_menu()
        choice = input("Выберите пункт: ").strip()

        try:
            if choice == "1":
                show_masters(center)
                print("\n1. Добавить мастера")
                print("0. Назад")

                action = input("Выберите действие: ").strip()

                if action == "1":
                    add_master_menu(center)
                    storage.save(center)

            elif choice == "2":
                show_requests(center)
                print("\n1. Создать заявку")
                print("0. Назад")

                action = input("Выберите действие: ").strip()

                if action == "1":
                    create_request_menu(center)
                    storage.save(center)

            elif choice == "3":
                search_requests_menu(center)

            elif choice == "4":
                show_summary(center)

            elif choice == "5":
                show_rating(center)

            elif choice == "0":
                storage.save(center)
                print("Данные сохранены. До свидания!")
                break

            else:
                print("Неизвестный пункт меню.")

        except (ValidationError, NotFoundError, BusinessRuleError) as exc:
            print(f"Ошибка: {exc}")

        except StorageError as exc:
            print(f"Ошибка сохранения данных: {exc}")

        except (ValueError, EOFError, KeyboardInterrupt):
            print("\nВвод прерван или содержит некорректные данные.")


if __name__ == "__main__":
    run()