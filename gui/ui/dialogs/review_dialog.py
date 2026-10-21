from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)


class ReviewDialog(QDialog):
    def __init__(self, book_title: str, review=None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Відгук — {book_title}")
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.title_edit = QLineEdit(getattr(review, "title", None) or "")
        self.rating = QSpinBox()
        self.rating.setRange(0, 5)
        self.rating.setSpecialValueText("—")
        self.rating.setValue(getattr(review, "rating", None) or 0)
        self.content = QTextEdit(getattr(review, "content", None) or "")
        self.content.setMinimumHeight(140)
        form.addRow("Заголовок", self.title_edit)
        form.addRow("Оцінка", self.rating)
        form.addRow("Текст", self.content)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Зберегти")
        buttons.button(QDialogButtonBox.Cancel).setText("Скасувати")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> dict:
        return {
            "title": self.title_edit.text().strip() or None,
            "rating": self.rating.value() or None,
            "content": self.content.toPlainText().strip(),
        }
