from __future__ import annotations

STATUS_LABELS = {
    "planned": "Ще не прочитана",
    "reading": "Читаю",
    "completed": "Прочитана",
    "paused": "Пауза",
    "abandoned": "Відкладена",
}


def status_label(status: str | None) -> str:
    if not status:
        return "—"
    return STATUS_LABELS.get(status, status)


def format_authors(authors) -> str:
    if not authors:
        return "Автор невідомий"
    names = []
    for a in authors:
        name = getattr(a, "name", None) or str(a)
        if name:
            names.append(name)
    return ", ".join(names) if names else "Автор невідомий"


def format_progress(progress) -> str:
    if progress is None:
        return "0%"
    pct = getattr(progress, "progress_percent", None)
    if pct is None:
        return "0%"
    return f"{int(round(float(pct)))}%"


def format_duration(seconds: int | float | None) -> str:
    if not seconds:
        return "0 хв"
    total = int(seconds)
    hours, rem = divmod(total, 3600)
    minutes = rem // 60
    if hours:
        return f"{hours} год {minutes} хв"
    return f"{minutes} хв"
