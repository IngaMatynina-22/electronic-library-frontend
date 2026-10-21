"""Map backend exceptions to user-facing Ukrainian messages."""

from __future__ import annotations


def user_message(exc: BaseException) -> str:
    code = getattr(exc, "code", None)
    message = getattr(exc, "message", None) or str(exc) or "Сталася помилка"
    mapping = {
        "not_found": "Запис не знайдено.",
        "validation_error": message,
        "file_access_error": "Файл книги недоступний або відсутній.",
        "unsupported_format": "Формат файлу не підтримується. Доступні PDF і EPUB.",
        "corrupted_file": "Файл пошкоджений або не читається.",
        "encrypted_file": "Файл захищений паролем.",
        "duplicate_book": "Ця книга вже є в бібліотеці.",
        "disk_space_error": "Недостатньо місця на диску.",
        "transaction_error": "Не вдалося зберегти зміни. Спробуйте ще раз.",
        "backup_error": "Помилка резервного копіювання або відновлення.",
        "authentication_error": "Невірне імʼя користувача або пароль.",
        "unauthorized": "Спочатку увійдіть у свій акаунт.",
        "user_exists": "Користувач із таким іменем уже існує.",
    }
    if code in mapping:
        return mapping[code]
    lower = message.lower()
    if "sql" in lower or "traceback" in lower or "sqlite" in lower:
        return "Помилка бази даних. Деталі записано в журнал."
    return message
