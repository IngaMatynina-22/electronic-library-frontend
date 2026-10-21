"""Persist lightweight GUI preferences (theme, view mode) via QSettings."""

from __future__ import annotations

from PySide6.QtCore import QSettings


class AppSettings:
    ORG = "PersonalLibrary"
    APP = "ElectronicLibrary"

    def __init__(self) -> None:
        self._s = QSettings(self.ORG, self.APP)

    def get_theme(self) -> str:
        return str(self._s.value("ui/theme", "light"))

    def set_theme(self, theme: str) -> None:
        self._s.setValue("ui/theme", theme)

    def get_library_view(self) -> str:
        return str(self._s.value("library/view", "grid"))

    def set_library_view(self, view: str) -> None:
        self._s.setValue("library/view", view)

    def get_library_sort(self) -> tuple[str, bool]:
        return (
            str(self._s.value("library/sort_by", "title")),
            self._s.value("library/sort_desc", False, type=bool),
        )

    def set_library_sort(self, sort_by: str, sort_desc: bool) -> None:
        self._s.setValue("library/sort_by", sort_by)
        self._s.setValue("library/sort_desc", sort_desc)

    def sync(self) -> None:
        self._s.sync()
