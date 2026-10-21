from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gui.ui.utils.errors import user_message
from gui.ui.workers.base import run_in_thread


class ImportPage(QWidget):
    import_finished = Signal()
    toast = Signal(str, str)
    busy = Signal(bool, str)

    def __init__(self, container, parent=None) -> None:
        super().__init__(parent)
        self.container = container
        self.setAcceptDrops(True)
        self._paths: list[Path] = []
        self._running = False

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QLabel("Імпорт книг")
        title.setObjectName("PageTitle")
        root.addWidget(title)
        hint = QLabel("Перетягніть PDF або EPUB сюди, або виберіть файли. Підтримуються кілька файлів одночасно.")
        hint.setObjectName("MutedLabel")
        hint.setWordWrap(True)
        root.addWidget(hint)

        row = QHBoxLayout()
        pick = QPushButton("Вибрати файли…")
        pick.setObjectName("PrimaryButton")
        pick.clicked.connect(self.pick_files)
        start = QPushButton("Почати імпорт")
        start.clicked.connect(self.start_import)
        clear = QPushButton("Очистити список")
        clear.clicked.connect(self._clear)
        row.addWidget(pick)
        row.addWidget(start)
        row.addWidget(clear)
        row.addStretch(1)
        root.addLayout(row)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Файл", "Формат", "Стан", "Повідомлення"])
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table, 1)

        self.summary = QLabel("")
        self.summary.setObjectName("MutedLabel")
        root.addWidget(self.summary)

    def pick_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Вибрати книги",
            "",
            "Книги (*.pdf *.epub);;PDF (*.pdf);;EPUB (*.epub)",
        )
        if files:
            self.add_paths(files)

    def add_paths(self, paths: list[str] | list[Path]) -> None:
        for p in paths:
            path = Path(p)
            ext = path.suffix.lower()
            if ext not in {".pdf", ".epub"}:
                self.toast.emit(f"Пропущено (формат): {path.name}", "error")
                continue
            if path in self._paths:
                continue
            self._paths.append(path)
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(path.name))
            self.table.setItem(row, 1, QTableWidgetItem(ext[1:].upper()))
            self.table.setItem(row, 2, QTableWidgetItem("Очікує"))
            self.table.setItem(row, 3, QTableWidgetItem(""))

    def _clear(self) -> None:
        if self._running:
            return
        self._paths.clear()
        self.table.setRowCount(0)
        self.summary.setText("")

    def start_import(self) -> None:
        if self._running or not self._paths:
            return
        paths = list(self._paths)
        self._running = True
        self.busy.emit(True, "Імпорт книг…")

        def work():
            return self.container.imports.import_files(paths)

        run_in_thread(work, on_finished=self._on_done, on_error=self._on_error)

    def _on_done(self, results) -> None:
        self._running = False
        self.busy.emit(False, "")
        ok = skipped = errors = 0
        for i, result in enumerate(results):
            if i >= self.table.rowCount():
                break
            if result.is_duplicate:
                skipped += 1
                self.table.setItem(i, 2, QTableWidgetItem("Дублікат"))
                self.table.setItem(i, 3, QTableWidgetItem("Уже в бібліотеці"))
            elif result.success:
                ok += 1
                title = result.book.title if result.book else "OK"
                self.table.setItem(i, 2, QTableWidgetItem("Імпортовано"))
                self.table.setItem(i, 3, QTableWidgetItem(title))
            else:
                errors += 1
                self.table.setItem(i, 2, QTableWidgetItem("Помилка"))
                self.table.setItem(i, 3, QTableWidgetItem(result.error_message or "Помилка"))
        self.summary.setText(
            f"Готово: імпортовано {ok}, дублікатів {skipped}, помилок {errors}."
        )
        self.toast.emit(f"Імпорт завершено: {ok} успішно", "success" if ok else "info")
        self.import_finished.emit()

    def _on_error(self, exc) -> None:
        self._running = False
        self.busy.emit(False, "")
        self.toast.emit(user_message(exc), "error")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        self.add_paths(paths)
        event.acceptProposedAction()
