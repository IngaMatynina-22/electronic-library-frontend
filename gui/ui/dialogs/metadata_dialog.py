from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

from gui.ui.utils.formatters import STATUS_LABELS


class MetadataDialog(QDialog):
    def __init__(self, book, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Редагувати метадані")
        self.setMinimumWidth(440)
        self._book = book

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.title_edit = QLineEdit(book.title or "")
        self.authors_edit = QLineEdit(
            ", ".join(a.name for a in (book.authors or []))
        )
        self.genres_edit = QLineEdit(
            ", ".join(g.name for g in (book.genres or []))
        )
        self.status_combo = QComboBox()
        for key, label in STATUS_LABELS.items():
            self.status_combo.addItem(label, key)
        idx = self.status_combo.findData(book.status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
        self.rating_spin = QSpinBox()
        self.rating_spin.setRange(0, 5)
        self.rating_spin.setSpecialValueText("—")
        self.rating_spin.setValue(book.rating or 0)
        self.desc_edit = QTextEdit(book.description or "")
        self.desc_edit.setMinimumHeight(100)

        form.addRow("Назва", self.title_edit)
        form.addRow("Автори", self.authors_edit)
        form.addRow("Жанри", self.genres_edit)
        form.addRow("Статус", self.status_combo)
        form.addRow("Рейтинг", self.rating_spin)
        form.addRow("Опис", self.desc_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        # Ukrainian labels
        buttons.button(QDialogButtonBox.Save).setText("Зберегти")
        buttons.button(QDialogButtonBox.Cancel).setText("Скасувати")
        layout.addWidget(buttons)

    def to_update_dto(self):
        from app.schemas.dtos import BookUpdateDTO

        authors = [a.strip() for a in self.authors_edit.text().split(",") if a.strip()]
        genres = [g.strip() for g in self.genres_edit.text().split(",") if g.strip()]
        rating = self.rating_spin.value() or None
        return BookUpdateDTO(
            title=self.title_edit.text().strip() or self._book.title,
            description=self.desc_edit.toPlainText().strip() or None,
            status=self.status_combo.currentData(),
            rating=rating,
            author_names=authors or None,
            genre_names=genres or None,
        )
