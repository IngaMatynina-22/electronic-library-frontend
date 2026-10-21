from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.ui.dialogs.bulk_edit_dialog import BulkEditDialog
from gui.ui.dialogs.export_dialog import ExportDialog
from gui.ui.utils.errors import user_message


class ToolsPage(QWidget):
    toast = Signal(str, str)

    def __init__(self, container, parent=None) -> None:
        super().__init__(parent)
        self.container = container

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        title = QLabel("Інструменти організації")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        row = QHBoxLayout()
        for text, slot in [
            ("Знайти дублікати", self._find_dups),
            ("Неповні метадані", self._incomplete),
            ("Експорт матеріалів", self._export_knowledge),
            ("Експорт метаданих", self._export_meta),
            ("Імпорт метаданих", self._import_meta),
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            row.addWidget(btn)
        row.addStretch(1)
        root.addLayout(row)

        self.list = QListWidget()
        root.addWidget(self.list, 1)
        self.hint = QLabel("")
        self.hint.setObjectName("MutedLabel")
        root.addWidget(self.hint)

    def reload(self) -> None:
        self.list.clear()
        self.hint.setText("Оберіть інструмент вище.")

    def _find_dups(self) -> None:
        try:
            groups = self.container.library_org.find_duplicates()
            self.list.clear()
            if not groups:
                self.hint.setText("Потенційних дублікатів не знайдено.")
                return
            self.hint.setText(f"Груп: {len(groups)}. Перегляньте записи — автоматичне видалення не виконується.")
            for g in groups:
                header = QListWidgetItem(f"— Група ({g.reason}) —")
                header.setFlags(Qt.NoItemFlags)
                self.list.addItem(header)
                for bid, title in zip(g.book_ids, g.titles or []):
                    self.list.addItem(QListWidgetItem(f"#{bid} {title}"))
                if not g.titles:
                    for bid in g.book_ids:
                        self.list.addItem(QListWidgetItem(f"#{bid}"))
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _incomplete(self) -> None:
        try:
            books = self.container.library_org.incomplete_metadata()
            self.list.clear()
            self.hint.setText(f"Книг з неповними метаданими: {len(books)}")
            for b in books:
                self.list.addItem(QListWidgetItem(f"#{b.id} {b.title}"))
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _export_knowledge(self) -> None:
        try:
            books = self.container.books.list()
        except Exception:
            books = []
        dlg = ExportDialog(books, self)
        if not dlg.exec():
            return
        vals = dlg.values()
        if not vals["destination"]:
            self.toast.emit("Вкажіть шлях до файлу", "error")
            return
        try:
            path = self.container.export.export_knowledge(
                vals["destination"],
                format=vals["format"],
                book_id=vals["book_id"],
                tag=vals["tag"],
            )
            self.toast.emit(f"Експортовано: {path}", "success")
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _export_meta(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Експорт метаданих", str(Path.home() / "library_metadata.json"), "JSON (*.json);;CSV (*.csv)"
        )
        if not path:
            return
        fmt = "csv" if path.lower().endswith(".csv") else "json"
        try:
            out = self.container.library_org.export_metadata(path, format=fmt)
            self.toast.emit(f"Метадані експортовано: {out}", "success")
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _import_meta(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Імпорт метаданих", "", "JSON/CSV (*.json *.csv)"
        )
        if not path:
            return
        try:
            n = self.container.library_org.import_metadata(path)
            self.toast.emit(f"Оновлено записів: {n}", "success")
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")
