from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NavItem:
    key: str
    label: str
    section: str
    icon: str


NAV_SECTIONS: list[tuple[str, list[NavItem]]] = [
    (
        "Бібліотека",
        [
            NavItem("library_all", "Усі книги", "library", "books"),
            NavItem("library_continue", "Продовжити читання", "library", "continue"),
            NavItem("library_planned", "Ще не прочитані", "library", "planned"),
            NavItem("library_reading", "Читаю зараз", "library", "reading"),
            NavItem("library_completed", "Прочитані", "library", "completed"),
            NavItem("library_favorites", "Вибране", "library", "favorite"),
        ],
    ),
    (
        "Організація",
        [
            NavItem("collections", "Колекції", "org", "collections"),
            NavItem("genres", "Жанри", "org", "genres"),
            NavItem("authors", "Автори", "org", "authors"),
            NavItem("tags", "Теги", "org", "tags"),
        ],
    ),
    (
        "Особисті матеріали",
        [
            NavItem("quotes", "Цитати", "materials", "quotes"),
            NavItem("notes", "Нотатки", "materials", "notes"),
            NavItem("bookmarks", "Закладки", "materials", "bookmarks"),
        ],
    ),
    (
        "Аналітика",
        [
            NavItem("stats", "Статистика читання", "analytics", "stats"),
            NavItem("calendar", "Календар активності", "analytics", "calendar"),
            NavItem("goals", "Цілі читання", "analytics", "goals"),
        ],
    ),
    (
        "Службові",
        [
            NavItem("import", "Імпорт книг", "service", "import"),
            NavItem("tools", "Інструменти організації", "service", "tools"),
            NavItem("settings", "Налаштування", "service", "settings"),
        ],
    ),
]
