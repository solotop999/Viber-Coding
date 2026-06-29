"""
Full-screen selection overlay.
Displays a frozen screenshot as background, dims it,
and lets the user drag a rectangle to select a region.
"""
from __future__ import annotations

from PIL import Image
from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QImage, QKeyEvent, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QApplication, QPushButton, QWidget

from core.screenshot import grab_all_monitors

_X_POST_RATIOS = (
    ("Ngang 16:9", 16 / 9),
    ("Vuông 1:1", 1.0),
    ("Dọc 4:5", 4 / 5),
)
_X_RATIO_DESCRIPTIONS = {
    "Ngang 16:9": "Hợp ảnh giao diện rộng",
    "Vuông 1:1": "Cân đối, dễ xem",
    "Dọc 4:5": "Nổi bật trên dòng thời gian",
}
_RATIO_SNAP_TOLERANCE = 0.025
_MIN_X_POST_WIDTH = 300


def _closest_x_post_ratio(width: int, height: int) -> tuple[str, bool]:
    if width <= 0 or height <= 0:
        return "", False

    ratio = width / height
    label, target = min(
        _X_POST_RATIOS,
        key=lambda item: abs(ratio - item[1]) / item[1],
    )
    relative_error = abs(ratio - target) / target
    return label, relative_error <= _RATIO_SNAP_TOLERANCE


def _pil_to_qpixmap(img: Image.Image) -> QPixmap:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    raw = img.tobytes("raw", "RGBA")
    qimg = QImage(raw, img.width, img.height, img.width * 4,
                  QImage.Format.Format_RGBA8888).copy()
    return QPixmap.fromImage(qimg)


class SelectionOverlay(QWidget):
    """
    Frameless full-screen overlay for selecting a screen region.
    Emits `region_selected(x, y, w, h)` with absolute screen coordinates.
    Emits `cancelled()` on Escape.
    """

    region_selected = pyqtSignal(int, int, int, int)
    cancelled = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        self._pil_img, (self._vx, self._vy) = grab_all_monitors()
        self._bg = _pil_to_qpixmap(self._pil_img)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        virtual = QApplication.primaryScreen().virtualGeometry()
        for screen in QApplication.screens():
            virtual = virtual.united(screen.geometry())
        self.setGeometry(virtual)

        self._origin: QPoint | None = None
        self._current: QPoint | None = None
        self._selecting = False
        self._finalized = False
        self._drag_action: str | None = None
        self._drag_start = QPoint()
        self._drag_start_rect = QRect()

        self._confirm_button = QPushButton("Xác nhận", self)
        self._confirm_button.setFixedSize(104, 36)
        self._confirm_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._confirm_button.setStyleSheet("""
            QPushButton {
                background: #16A34A;
                color: white;
                border: 1px solid #0F7A37;
                border-radius: 7px;
                font: 700 10pt "Segoe UI";
            }
            QPushButton:hover { background: #15803D; }
            QPushButton:pressed { background: #126B34; }
        """)
        self._confirm_button.clicked.connect(self._confirm_selection)
        self._confirm_button.hide()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._bg)

        dim = QColor(0, 0, 0, 140)
        width, height = self.width(), self.height()

        if (self._selecting or self._finalized) and self._origin and self._current:
            selection = self._selection_rect()

            painter.fillRect(0, 0, width, selection.top(), dim)
            painter.fillRect(0, selection.bottom() + 1, width, height - selection.bottom() - 1, dim)
            painter.fillRect(0, selection.top(), selection.left(), selection.height(), dim)
            painter.fillRect(
                selection.right() + 1,
                selection.top(),
                width - selection.right() - 1,
                selection.height(),
                dim,
            )

            if self._selecting and self._drag_action == "select":
                for guide, guide_label, highlighted in self._ratio_guide_rects():
                    self._draw_ratio_guide(painter, guide, guide_label, highlighted)

            if selection.width() > 4 and selection.height() > 4:
                ratio_label, ratio_matches = _closest_x_post_ratio(
                    selection.width(),
                    selection.height(),
                )
                if selection.width() < _MIN_X_POST_WIDTH:
                    border_color = QColor(235, 64, 52, 245)
                elif ratio_matches:
                    border_color = QColor(25, 200, 91, 245)
                else:
                    border_color = QColor(255, 255, 255, 220)
                painter.setPen(QPen(border_color, 1, Qt.PenStyle.SolidLine))
                painter.drawRect(selection)

                self._draw_composition_grid(painter, selection)
                self._draw_selection_badge(painter, selection, ratio_label, ratio_matches)
                if self._finalized:
                    self._draw_resize_handles(painter, selection)
        else:
            painter.fillRect(self.rect(), dim)

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return

        if self._finalized:
            selection = self._selection_rect()
            action = self._hit_test_selection(event.pos(), selection)
            if action:
                self._drag_action = action
                self._drag_start = event.pos()
                self._drag_start_rect = QRect(selection)
                self._selecting = True
                self._confirm_button.hide()
                return

        self._origin = event.pos()
        self._current = event.pos()
        self._drag_action = "select"
        self._selecting = True
        self._finalized = False
        self._confirm_button.hide()
        self.update()

    def mouseMoveEvent(self, event) -> None:
        if self._selecting and self._drag_action == "select":
            self._current = event.pos()
            self.update()
            return

        if self._selecting and self._drag_action == "move":
            rect = QRect(self._drag_start_rect)
            rect.translate(event.pos() - self._drag_start)
            self._constrain_rect_to_overlay(rect)
            self._set_selection_rect(rect)
            self.update()
            return

        if self._selecting and self._drag_action:
            rect = self._resized_rect(self._drag_start_rect, event.pos(), self._drag_action)
            self._set_selection_rect(rect)
            self.update()
            return

        if self._finalized:
            action = self._hit_test_selection(event.pos(), self._selection_rect())
            self.setCursor(QCursor(self._cursor_for_action(action)))

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton or not self._selecting:
            return

        self._selecting = False
        self._drag_action = None
        selection = self._selection_rect()
        if selection.width() > 4 and selection.height() > 4:
            self._finalized = True
            self._position_confirm_button(selection)
            self._confirm_button.show()
            self._confirm_button.raise_()
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        else:
            self._finalized = False
            self._origin = None
            self._current = None
            self._confirm_button.hide()
        self.update()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            self.cancelled.emit()
        elif event.key() in {Qt.Key.Key_Enter, Qt.Key.Key_Return}:
            self._confirm_selection()

    def _confirm_selection(self) -> None:
        if not self._finalized:
            return

        selection = self._selection_rect()
        if selection.width() <= 4 or selection.height() <= 4:
            return

        # The selection is local to an overlay that covers the complete virtual
        # desktop. MSS already supplies the desktop's absolute origin.
        x = self._vx + selection.x()
        y = self._vy + selection.y()
        self.hide()
        self.region_selected.emit(x, y, selection.width(), selection.height())

    def _selection_rect(self) -> QRect:
        if self._origin is None or self._current is None:
            return QRect()
        return QRect(self._origin, self._current).normalized()

    def _set_selection_rect(self, rect: QRect) -> None:
        normalized = rect.normalized().intersected(self.rect())
        self._origin = normalized.topLeft()
        self._current = normalized.bottomRight()

    def _constrain_rect_to_overlay(self, rect: QRect) -> None:
        bounds = self.rect()
        if rect.left() < bounds.left():
            rect.translate(bounds.left() - rect.left(), 0)
        if rect.right() > bounds.right():
            rect.translate(bounds.right() - rect.right(), 0)
        if rect.top() < bounds.top():
            rect.translate(0, bounds.top() - rect.top())
        if rect.bottom() > bounds.bottom():
            rect.translate(0, bounds.bottom() - rect.bottom())

    @staticmethod
    def _hit_test_selection(pos: QPoint, rect: QRect) -> str | None:
        margin = 9
        near_left = abs(pos.x() - rect.left()) <= margin
        near_right = abs(pos.x() - rect.right()) <= margin
        near_top = abs(pos.y() - rect.top()) <= margin
        near_bottom = abs(pos.y() - rect.bottom()) <= margin
        within_x = rect.left() - margin <= pos.x() <= rect.right() + margin
        within_y = rect.top() - margin <= pos.y() <= rect.bottom() + margin

        if near_left and near_top:
            return "top_left"
        if near_right and near_top:
            return "top_right"
        if near_left and near_bottom:
            return "bottom_left"
        if near_right and near_bottom:
            return "bottom_right"
        if near_left and within_y:
            return "left"
        if near_right and within_y:
            return "right"
        if near_top and within_x:
            return "top"
        if near_bottom and within_x:
            return "bottom"
        if rect.contains(pos):
            return "move"
        return None

    def _resized_rect(self, start: QRect, pos: QPoint, action: str) -> QRect:
        bounds = self.rect()
        x = max(bounds.left(), min(pos.x(), bounds.right()))
        y = max(bounds.top(), min(pos.y(), bounds.bottom()))
        rect = QRect(start)

        if "left" in action:
            rect.setLeft(x)
        if "right" in action:
            rect.setRight(x)
        if "top" in action:
            rect.setTop(y)
        if "bottom" in action:
            rect.setBottom(y)
        return rect.normalized().intersected(bounds)

    @staticmethod
    def _cursor_for_action(action: str | None) -> Qt.CursorShape:
        if action in {"top_left", "bottom_right"}:
            return Qt.CursorShape.SizeFDiagCursor
        if action in {"top_right", "bottom_left"}:
            return Qt.CursorShape.SizeBDiagCursor
        if action in {"left", "right"}:
            return Qt.CursorShape.SizeHorCursor
        if action in {"top", "bottom"}:
            return Qt.CursorShape.SizeVerCursor
        if action == "move":
            return Qt.CursorShape.SizeAllCursor
        return Qt.CursorShape.ArrowCursor

    def _position_confirm_button(self, selection: QRect) -> None:
        button = self._confirm_button
        x = selection.center().x() - button.width() // 2
        x = max(8, min(x, self.width() - button.width() - 8))
        y = selection.bottom() + 12
        if y + button.height() > self.height() - 8:
            y = selection.top() - button.height() - 12
        y = max(8, min(y, self.height() - button.height() - 8))
        button.move(x, y)

    @staticmethod
    def _draw_resize_handles(painter: QPainter, selection: QRect) -> None:
        points = (
            selection.topLeft(),
            QPoint(selection.center().x(), selection.top()),
            selection.topRight(),
            QPoint(selection.left(), selection.center().y()),
            QPoint(selection.right(), selection.center().y()),
            selection.bottomLeft(),
            QPoint(selection.center().x(), selection.bottom()),
            selection.bottomRight(),
        )
        painter.save()
        painter.setPen(QPen(QColor(30, 110, 170), 1))
        painter.setBrush(QColor(235, 248, 255))
        for point in points:
            painter.drawRect(QRect(point.x() - 3, point.y() - 3, 7, 7))
        painter.restore()

    def _ratio_guide_rects(self) -> list[tuple[QRect, str, bool]]:
        if self._origin is None or self._current is None:
            return []

        dx = self._current.x() - self._origin.x()
        dy = self._current.y() - self._origin.y()
        raw_width = abs(dx)
        raw_height = abs(dy)
        is_initial_point = raw_width < 4 and raw_height < 4

        if is_initial_point:
            base_width = min(320, max(120, self.width() // 4))
            sign_x = 1 if self.width() - self._origin.x() >= base_width else -1
            tallest_height = round(base_width / _X_POST_RATIOS[-1][1])
            sign_y = 1 if self.height() - self._origin.y() >= tallest_height else -1
            closest_label = ""
        else:
            closest_label, _ = min(
                _X_POST_RATIOS,
                key=lambda item: abs((raw_width / max(1, raw_height)) - item[1]) / item[1],
            )
            sign_x = 1 if dx >= 0 else -1
            sign_y = 1 if dy >= 0 else -1

        guides: list[tuple[QRect, str, bool]] = []
        for label, target in _X_POST_RATIOS:
            if is_initial_point:
                guide_width = base_width
                guide_height = round(base_width / target)
            else:
                height_from_width = max(1, round(raw_width / target))
                width_from_height = max(1, round(raw_height * target))
                if abs(height_from_width - raw_height) <= abs(width_from_height - raw_width):
                    guide_width = max(1, raw_width)
                    guide_height = height_from_width
                else:
                    guide_width = width_from_height
                    guide_height = max(1, raw_height)

            end = QPoint(
                self._origin.x() + sign_x * guide_width,
                self._origin.y() + sign_y * guide_height,
            )
            guides.append((QRect(self._origin, end).normalized(), label, label == closest_label))

        return guides

    @staticmethod
    def _draw_ratio_guide(
        painter: QPainter,
        guide: QRect,
        label: str,
        highlighted: bool,
    ) -> None:
        if guide.isNull() or not label:
            return

        painter.save()
        color = QColor(70, 210, 255, 245) if highlighted else QColor(170, 220, 245, 150)
        painter.setPen(QPen(color, 2 if highlighted else 1, Qt.PenStyle.DashLine))
        painter.drawRect(guide)
        painter.restore()

    @staticmethod
    def _draw_composition_grid(painter: QPainter, selection: QRect) -> None:
        if selection.width() < 36 or selection.height() < 36:
            return

        painter.save()
        painter.setClipRect(selection)
        painter.setPen(QPen(QColor(255, 255, 255, 105), 1, Qt.PenStyle.DashLine))
        for part in (1, 2):
            x = selection.left() + round(selection.width() * part / 3)
            y = selection.top() + round(selection.height() * part / 3)
            painter.drawLine(x, selection.top(), x, selection.bottom())
            painter.drawLine(selection.left(), y, selection.right(), y)
        painter.restore()

    @staticmethod
    def _draw_selection_badge(
        painter: QPainter,
        selection: QRect,
        ratio_label: str,
        ratio_matches: bool,
    ) -> None:
        ratio_status = (
            f"Chuẩn {ratio_label.lower()}"
            if ratio_matches
            else f"Gần tỷ lệ {ratio_label.lower()}"
        )
        description = _X_RATIO_DESCRIPTIONS.get(ratio_label, "")
        status = f"{ratio_status}  •  {description}" if description else ratio_status
        too_small = selection.width() < _MIN_X_POST_WIDTH
        if too_small:
            status = "Cảnh báo: ảnh rộng dưới 300 px, đăng X có thể bị mờ"
        text = f"{selection.width()} × {selection.height()}  •  {status}"
        metrics = painter.fontMetrics()
        text_rect = metrics.boundingRect(text).adjusted(-8, -4, 8, 4)

        x = selection.left()
        y = selection.top() - text_rect.height() - 6
        if y < 4:
            y = selection.top() + 6
        badge = QRect(x, y, text_rect.width(), text_rect.height())

        if too_small:
            badge_color = QColor(190, 42, 42, 235)
        elif ratio_matches:
            badge_color = QColor(15, 125, 62, 225)
        else:
            badge_color = QColor(20, 24, 32, 210)
        painter.fillRect(badge, badge_color)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(badge, Qt.AlignmentFlag.AlignCenter, text)
