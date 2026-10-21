"""Simple painted navigation icons (no external SVG dependency)."""

from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap


def _pix(size: int, color: str, draw) -> QPixmap:
    pix = QPixmap(size, size)
    pix.fill(QColor(0, 0, 0, 0))
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(1.6)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    draw(p, size)
    p.end()
    return pix


def load_icon(name: str, color: str = "#3D5A40", size: int = 20) -> QIcon:
    drawers = {
        "books": _draw_books,
        "continue": _draw_play,
        "planned": _draw_inbox,
        "reading": _draw_book_open,
        "completed": _draw_check,
        "favorite": _draw_star,
        "collections": _draw_folder,
        "genres": _draw_tag_grid,
        "authors": _draw_user,
        "tags": _draw_tag,
        "quotes": _draw_quote,
        "notes": _draw_note,
        "bookmarks": _draw_bookmark,
        "stats": _draw_chart,
        "calendar": _draw_calendar,
        "goals": _draw_target,
        "import": _draw_import,
        "tools": _draw_wrench,
        "settings": _draw_gear,
        "theme_sun": _draw_sun,
        "theme_moon": _draw_moon,
    }
    fn = drawers.get(name, _draw_books)
    return QIcon(_pix(size, color, fn))


def icon_size() -> QSize:
    return QSize(20, 20)


def _draw_books(p: QPainter, s: int) -> None:
    m = s * 0.2
    p.drawRoundedRect(QRectF(m, m, s * 0.28, s * 0.6), 2, 2)
    p.drawRoundedRect(QRectF(m + s * 0.32, m * 1.1, s * 0.28, s * 0.55), 2, 2)


def _draw_play(p: QPainter, s: int) -> None:
    from PySide6.QtGui import QPolygonF
    from PySide6.QtCore import QPointF

    poly = QPolygonF(
        [
            QPointF(s * 0.32, s * 0.22),
            QPointF(s * 0.78, s * 0.5),
            QPointF(s * 0.32, s * 0.78),
        ]
    )
    p.setBrush(QColor(p.pen().color()))
    p.drawPolygon(poly)


def _draw_inbox(p: QPainter, s: int) -> None:
    p.drawRoundedRect(QRectF(s * 0.2, s * 0.28, s * 0.6, s * 0.48), 2, 2)
    p.drawLine(int(s * 0.2), int(s * 0.48), int(s * 0.8), int(s * 0.48))


def _draw_book_open(p: QPainter, s: int) -> None:
    p.drawLine(int(s * 0.5), int(s * 0.22), int(s * 0.5), int(s * 0.78))
    p.drawArc(int(s * 0.18), int(s * 0.22), int(s * 0.34), int(s * 0.56), 90 * 16, 180 * 16)
    p.drawArc(int(s * 0.48), int(s * 0.22), int(s * 0.34), int(s * 0.56), -90 * 16, 180 * 16)


def _draw_check(p: QPainter, s: int) -> None:
    p.drawEllipse(QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64))
    p.drawLine(int(s * 0.32), int(s * 0.52), int(s * 0.45), int(s * 0.66))
    p.drawLine(int(s * 0.45), int(s * 0.66), int(s * 0.7), int(s * 0.36))


def _draw_star(p: QPainter, s: int) -> None:
    from PySide6.QtGui import QPolygonF
    from PySide6.QtCore import QPointF
    import math

    cx, cy, r = s / 2, s / 2, s * 0.34
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append(QPointF(cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    p.setBrush(Qt.NoBrush)
    p.drawPolygon(QPolygonF(pts))


def _draw_folder(p: QPainter, s: int) -> None:
    p.drawRoundedRect(QRectF(s * 0.18, s * 0.34, s * 0.64, s * 0.42), 2, 2)
    p.drawRoundedRect(QRectF(s * 0.18, s * 0.26, s * 0.28, s * 0.14), 2, 2)


def _draw_tag_grid(p: QPainter, s: int) -> None:
    for x, y in ((0.22, 0.22), (0.54, 0.22), (0.22, 0.54), (0.54, 0.54)):
        p.drawRoundedRect(QRectF(s * x, s * y, s * 0.24, s * 0.24), 2, 2)


def _draw_user(p: QPainter, s: int) -> None:
    p.drawEllipse(QRectF(s * 0.35, s * 0.18, s * 0.3, s * 0.3))
    p.drawArc(int(s * 0.22), int(s * 0.48), int(s * 0.56), int(s * 0.42), 0, 180 * 16)


def _draw_tag(p: QPainter, s: int) -> None:
    from PySide6.QtGui import QPolygonF
    from PySide6.QtCore import QPointF

    poly = QPolygonF(
        [
            QPointF(s * 0.22, s * 0.28),
            QPointF(s * 0.55, s * 0.28),
            QPointF(s * 0.78, s * 0.5),
            QPointF(s * 0.55, s * 0.72),
            QPointF(s * 0.22, s * 0.72),
        ]
    )
    p.drawPolygon(poly)
    p.drawEllipse(QRectF(s * 0.32, s * 0.42, s * 0.1, s * 0.1))


def _draw_quote(p: QPainter, s: int) -> None:
    p.drawText(QRectF(0, 0, s, s), Qt.AlignCenter, "“”")


def _draw_note(p: QPainter, s: int) -> None:
    p.drawRoundedRect(QRectF(s * 0.26, s * 0.18, s * 0.48, s * 0.64), 2, 2)
    p.drawLine(int(s * 0.34), int(s * 0.36), int(s * 0.66), int(s * 0.36))
    p.drawLine(int(s * 0.34), int(s * 0.5), int(s * 0.66), int(s * 0.5))
    p.drawLine(int(s * 0.34), int(s * 0.64), int(s * 0.58), int(s * 0.64))


def _draw_bookmark(p: QPainter, s: int) -> None:
    from PySide6.QtGui import QPolygonF
    from PySide6.QtCore import QPointF

    poly = QPolygonF(
        [
            QPointF(s * 0.3, s * 0.18),
            QPointF(s * 0.7, s * 0.18),
            QPointF(s * 0.7, s * 0.82),
            QPointF(s * 0.5, s * 0.66),
            QPointF(s * 0.3, s * 0.82),
        ]
    )
    p.drawPolygon(poly)


def _draw_chart(p: QPainter, s: int) -> None:
    p.drawLine(int(s * 0.22), int(s * 0.78), int(s * 0.78), int(s * 0.78))
    p.drawRect(int(s * 0.28), int(s * 0.48), int(s * 0.12), int(s * 0.3))
    p.drawRect(int(s * 0.44), int(s * 0.34), int(s * 0.12), int(s * 0.44))
    p.drawRect(int(s * 0.6), int(s * 0.42), int(s * 0.12), int(s * 0.36))


def _draw_calendar(p: QPainter, s: int) -> None:
    p.drawRoundedRect(QRectF(s * 0.22, s * 0.28, s * 0.56, s * 0.5), 2, 2)
    p.drawLine(int(s * 0.22), int(s * 0.42), int(s * 0.78), int(s * 0.42))
    p.drawLine(int(s * 0.34), int(s * 0.2), int(s * 0.34), int(s * 0.34))
    p.drawLine(int(s * 0.66), int(s * 0.2), int(s * 0.66), int(s * 0.34))


def _draw_target(p: QPainter, s: int) -> None:
    p.drawEllipse(QRectF(s * 0.22, s * 0.22, s * 0.56, s * 0.56))
    p.drawEllipse(QRectF(s * 0.34, s * 0.34, s * 0.32, s * 0.32))
    p.drawEllipse(QRectF(s * 0.44, s * 0.44, s * 0.12, s * 0.12))


def _draw_import(p: QPainter, s: int) -> None:
    p.drawLine(int(s * 0.5), int(s * 0.2), int(s * 0.5), int(s * 0.58))
    p.drawLine(int(s * 0.5), int(s * 0.58), int(s * 0.34), int(s * 0.42))
    p.drawLine(int(s * 0.5), int(s * 0.58), int(s * 0.66), int(s * 0.42))
    p.drawLine(int(s * 0.26), int(s * 0.7), int(s * 0.74), int(s * 0.7))


def _draw_wrench(p: QPainter, s: int) -> None:
    p.drawEllipse(QRectF(s * 0.22, s * 0.22, s * 0.28, s * 0.28))
    p.drawLine(int(s * 0.42), int(s * 0.42), int(s * 0.74), int(s * 0.74))


def _draw_gear(p: QPainter, s: int) -> None:
    p.drawEllipse(QRectF(s * 0.32, s * 0.32, s * 0.36, s * 0.36))
    for i in range(8):
        import math

        a = i * math.pi / 4
        x1 = s / 2 + math.cos(a) * s * 0.22
        y1 = s / 2 + math.sin(a) * s * 0.22
        x2 = s / 2 + math.cos(a) * s * 0.38
        y2 = s / 2 + math.sin(a) * s * 0.38
        p.drawLine(int(x1), int(y1), int(x2), int(y2))


def _draw_sun(p: QPainter, s: int) -> None:
    import math

    p.drawEllipse(QRectF(s * 0.34, s * 0.34, s * 0.32, s * 0.32))
    cx = cy = s / 2
    for i in range(8):
        a = i * math.pi / 4
        p.drawLine(
            int(cx + math.cos(a) * s * 0.28),
            int(cy + math.sin(a) * s * 0.28),
            int(cx + math.cos(a) * s * 0.42),
            int(cy + math.sin(a) * s * 0.42),
        )


def _draw_moon(p: QPainter, s: int) -> None:
    from PySide6.QtGui import QPainterPath

    path = QPainterPath()
    path.addEllipse(QRectF(s * 0.28, s * 0.22, s * 0.5, s * 0.56))
    cut = QPainterPath()
    cut.addEllipse(QRectF(s * 0.42, s * 0.18, s * 0.48, s * 0.52))
    crescent = path.subtracted(cut)
    p.setBrush(QColor(p.pen().color()))
    p.setPen(Qt.NoPen)
    p.drawPath(crescent)
