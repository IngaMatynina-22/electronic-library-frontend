#!/usr/bin/env python3
"""Launch the personal electronic library desktop application."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox


def main() -> int:
    from gui.bootstrap import init_app_container
    from gui.ui.themes.theme_manager import apply_theme
    from gui.ui.utils.app_settings import AppSettings

    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Electronic Library")
    qt_app.setOrganizationName("PersonalLibrary")

    settings = AppSettings()
    apply_theme(settings.get_theme())

    try:
        container = init_app_container()
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(
            None,
            "Помилка запуску",
            f"Не вдалося ініціалізувати бекенд:\n{exc}",
        )
        return 1

    from gui.ui.pages.auth_page import AuthPage
    from gui.ui.main_window import MainWindow

    auth_page = AuthPage(container)
    auth_page.setWindowTitle("Персональна електронна бібліотека — Вхід")
    auth_page.setMinimumSize(1000, 650)
    auth_page.resize(1100, 720)

    state: dict = {"main": None}

    def on_auth(user) -> None:
        if state["main"] is None:
            mw = MainWindow(container)
            mw.logout_requested.connect(on_logout)
            state["main"] = mw
        auth_page.hide()
        state["main"].on_user_ready(user)
        state["main"].show()
        state["main"].raise_()

    def on_logout() -> None:
        busy = False
        if state["main"] is not None:
            busy = state["main"].is_busy()
        if busy:
            ans = QMessageBox.question(
                state["main"],
                "Вийти",
                "Виконується фонова операція. Все одно вийти?",
            )
            if ans != QMessageBox.Yes:
                return
        try:
            if state["main"] is not None and state["main"].is_reader_open():
                state["main"].close_reader_safely()
            container.auth.logout()
        except Exception:  # noqa: BLE001
            pass
        if state["main"] is not None:
            state["main"].prepare_logout()
            state["main"].hide()
        auth_page.reset_for_logout()
        auth_page.show()
        auth_page.raise_()

    auth_page.authenticated.connect(on_auth)

    if container.auth.current_user() is not None:
        on_auth(container.auth.current_user())
    else:
        auth_page.show()

    code = qt_app.exec()
    try:
        if state["main"] is not None:
            state["main"].close_reader_safely()
        container.shutdown()
    except Exception:  # noqa: BLE001
        pass
    return code


if __name__ == "__main__":
    raise SystemExit(main())
