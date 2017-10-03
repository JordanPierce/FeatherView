# -*- coding: utf-8 -*-
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import QRectF
import weakref


def sign(x):
    if x < 0:
        return -1
    return 1


class QLabelExtended(QtWidgets.QLabel):
    """
    Extends QLabel to allow for ease of qpixmap loading and manipulating (translating and zooming)
    """

    def __init__(self, name="", parent=None):
        super(QLabelExtended, self).__init__(parent)
        self.parent = parent
        self.qpixmap = None
        self.qpixmap_ref = lambda: None
        self.draw_qpixmap = False

        self.size = [self.geometry().width(),
                     self.geometry().height()]

        self.old_panning_point = [None, None]
        self.panning_mode = False
        self.initialized = False
        self.qpixmap_size = None
        self.old_qpixmap_size = [0, 0]
        self.panning_scale = 0
        self.painter = QtGui.QPainter()

        self.center_x = 0
        self.center_y = 0
        self.ratio = [1, 1]
        self.Half_width = 1
        self._half_width = 1
        self.Center = None
        self.first_resize = False
        self.cursor_drag = False

        self.pinch_center = None
        self.full_screen = False

        self.mouse_hidden = False
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.hide_mouse)
        self.timer.setSingleShot(True)
        self.just_switched = False

        # self.mili_now = 0

        self.init_gestures()

    def init_gestures(self):
        self.grabGesture(QtCore.Qt.PinchGesture)

    @QtCore.pyqtSlot(QtCore.QObject)
    def event(self, event):
        if self.qpixmap_ref is None:
            return False
        if event.type() == QtCore.QEvent.Gesture:
            return self.gesture_handler(event)
        return super(QLabelExtended, self).event(event)

    @QtCore.pyqtSlot(QtCore.QObject)
    def gesture_handler(self, event):
        gesture = event.gesture(QtCore.Qt.PinchGesture)
        if gesture.state() == QtCore.Qt.GestureFinished:
            self.pinch_center = None
        else:
            if self.pinch_center is None:
                self.pinch_center = QtCore.QPoint(gesture.centerPoint().x(), gesture.centerPoint().y())
            zero = self.mapToGlobal(QtCore.QPoint(0, 0))
            self.zoom(gesture.scaleFactor(), self.pinch_center - zero)
        return True

    def setText(self, text):
        pass

    def view(self, qpixmap):
        self.initialize(qpixmap)
        self.update()

    def initialize(self, qpixmap):
        if qpixmap is None:
            def _():
                pass

            self.qpixmap = weakref.proxy(_)
            self.qpixmap_ref = weakref.ref(_)
            return
        self.qpixmap = weakref.proxy(qpixmap)
        self.qpixmap_ref = weakref.ref(qpixmap)
        self.draw_qpixmap = True
        self.qpixmap_size = [self.qpixmap.size().width(), self.qpixmap.size().height()]

        if self.qpixmap_size != self.old_qpixmap_size:
            self.old_qpixmap_size = self.qpixmap_size
            self.initialized = False

        if self.initialized is False:
            self.size = [self.geometry().width(), self.geometry().height()]

            if float(self.size[0]) / float(self.size[1]) < float(self.qpixmap_size[0]) / float(self.qpixmap_size[1]):
                self.half_width = self.qpixmap_size[0] / 2.
            else:
                self.half_width = self.qpixmap_size[1] / 2.

            self.center_x = float(self.qpixmap_size[0]) / 2.
            self.center_y = float(self.qpixmap_size[1]) / 2.
            self.initialized = True
            self.Half_width = self.half_width
            self.Center = [self.center_x, self.center_y]

            self.calculate_ratio()

        if self.qpixmap_size[0] < self.size[0] or self.qpixmap_size[1] < self.size[1]:
            self.set_magnification(1)

        self.update()

    def return_qpixmap(self):
        if self.qpixmap_ref() is None:
            return None
        return self.qpixmap

    def check_bounds(self):
        x = self.half_width * self.ratio[0]
        y = self.half_width * self.ratio[1]
        x_extent = 2 * x
        y_extent = 2 * y
        if x_extent > self.qpixmap_size[0] and y_extent > self.qpixmap_size[1]:
            if self.qpixmap_size[0] > self.size[0] or self.qpixmap_size[1] > self.size[1]:
                self.resetView()
                return
            else:
                if self.get_magnification() < 1:
                    self.set_magnification(1)
                self.center_x = self.Center[0]
                self.center_y = self.Center[1]
                return
        if x_extent >= self.qpixmap_size[0]:
            self.center_x = self.Center[0]
        else:
            if self.center_x - x < 0:
                self.center_x = x
            if self.center_x + x > self.qpixmap_size[0]:
                self.center_x = self.qpixmap_size[0] - x
        if y_extent >= self.qpixmap_size[1]:
            self.center_y = self.Center[1]
        else:
            if self.center_y - y < 0:
                self.center_y = y
            if self.center_y + y > self.qpixmap_size[1]:
                self.center_y = self.qpixmap_size[1] - y

    def cycle_timer(self):
        if self.timer:
            self.timer.stop()

        self.timer.start(1000)

    def hide_mouse(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.BlankCursor)
        self.mouse_hidden = True

    def show_mouse(self):
        QtWidgets.QApplication.restoreOverrideCursor()
        self.mouse_hidden = False

    @QtCore.pyqtSlot(QtCore.QObject)
    def wheelEvent(self, event):
        """
        This overloaded method handles events caused by scrolling the middle mouse wheel over the label area
        :param event:
        :return:
        """
        if self.qpixmap_ref() is None:
            return

        if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
            scale = sign(event.angleDelta().y())
            Scale = event.angleDelta().y() / 120 / scale
            self.zoom((1 + 0.1 * Scale ) ** scale, QtCore.QPoint(event.x(), event.y()))
        else:
            scale = self.half_width / 100 * (event.angleDelta().y() / 40)
            self.center_y += scale
            scale = self.half_width / 100 * (event.angleDelta().x() / 40)
            self.center_x += scale
            self.update()

    def zoom(self, factor, center):
        half_width = self.half_width

        self.set_magnification((self.get_magnification() * factor) ** -1)

        width = self.size[0]
        height = self.size[1]

        min_size = min(self.size)

        if width < height:
            d_width = 1 + (float(center.x() - min_size)) / float(min_size)
            d_height = 1 + (float(center.y() - (height - width) / 2.0 - min_size)) / float(min_size)
        else:
            d_width = 1 + (float(center.x() - (width - height) / 2.0 - min_size)) / float(min_size)
            d_height = 1 + (float(center.y() - min_size)) / float(min_size)

        mouse_x = 2 * half_width * d_width + self.center_x - half_width
        mouse_y = 2 * half_width * d_height + self.center_y - half_width

        x_r = (center.x() - float(width / 2.0))
        y_r = (center.y() - float(height / 2.0))

        self.center_x = mouse_x - 2 * self.half_width / min_size * x_r
        self.center_y = mouse_y - 2 * self.half_width / min_size * y_r

        self.update()

    def calculate_ratio(self):
        half_width = self.half_width

        self.size = [self.geometry().width(),
                     self.geometry().height()]
        self.ratio = [1.0, 1.0]

        if float(self.size[0]) / float(self.size[1]) > float(self.qpixmap_size[0]) / float(self.qpixmap_size[1]):
            self.ratio[0] = float(self.size[0]) / float(self.size[1])
            half_width = self.qpixmap_size[1] / 2.
        if float(self.size[0]) / float(self.size[1]) <= float(self.qpixmap_size[0]) / float(self.qpixmap_size[1]):
            self.ratio[1] = float(self.size[1]) / float(self.size[0])
            half_width = self.qpixmap_size[0] / 2.

        self.Half_width = half_width

    @QtCore.pyqtSlot(QtCore.QObject)
    def resizeEvent(self, event):
        if self.qpixmap_ref() is None:
            return
        mag = self.get_magnification()
        self.calculate_ratio()
        if self.first_resize:
            self.first_resize = False
            return

        self.set_magnification(mag ** -1)

    @QtCore.pyqtSlot(QtCore.QObject)
    def paintEvent(self, event):
        """
        This overloaded method handles how to draw the scene for QLabelExtended.  This will draw a section of
        self.qpixmap dependent on self.half_width and self.center_x,y
        :param event:
        :return:
        """
        if self.qpixmap_ref() is None:
            return

        self.check_bounds()

        size = self.size
        half_width = self.half_width
        ratio_x = self.ratio[0] * half_width
        ratio_y = self.ratio[1] * half_width

        target = QRectF(
            0.0,
            0.0,
            size[0],
            size[1])

        source = QRectF(self.center_x - ratio_x,
                        self.center_y - ratio_y,
                        2 * ratio_x,
                        2 * ratio_y)

        painter = self.painter
        painter.begin(self)
        if self.center_x - ratio_x != 0:
            if size[0] / ratio_x < 4:
                painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
                painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
        painter.drawPixmap(target, self.qpixmap_ref(), source)
        painter.end()

    @QtCore.pyqtSlot(QtCore.QObject)
    def point(self, pt):
        point = QtCore.QPoint()

        rpc = (self.size[0]) / (2 * self.half_width * self.ratio[0])

        point.setX((pt[0] - self.center_x + self.half_width) * rpc +
                   (self.ratio[0] - 1) / 2.0 * self.size[1])

        point.setY((pt[1] - self.center_y + self.half_width) * rpc +
                   (self.ratio[1] - 1) / 2.0 * self.size[0])

        return point

    @QtCore.pyqtSlot(QtCore.QObject)
    def convert(self, pt):
        point = [0, 0]

        rpc = (self.size[0]) / (2 * self.half_width * self.ratio[0])

        point[0] = ((pt[0] - (self.ratio[0] - 1) / 2.0 * self.size[1]) / rpc +
                    self.center_x - self.half_width)

        point[1] = ((pt[1] - (self.ratio[1] - 1) / 2.0 * self.size[0]) / rpc +
                    self.center_y - self.half_width)

        return point

    def resetView(self):
        if self.qpixmap_ref() is None:
            return
        self.center_x = self.Center[0]
        self.center_y = self.Center[1]
        self.half_width = self.Half_width
        self.draw_line = False
        self.update()

    @QtCore.pyqtSlot(QtCore.QObject)
    def mouseDoubleClickEvent(self, event):
        if self.qpixmap_ref() is None:
            return
        self.toggle_fullscreen()

    @QtCore.pyqtSlot(QtCore.QObject)
    def mousePressEvent(self, event):
        if self.qpixmap_ref() is None:
            return

        self.panning_scale = self.geometry().width()

        if event.button() == 1:
            self.old_panning_point = [event.x(), event.y()]
            self.panning_mode = True

    @QtCore.pyqtSlot(QtCore.QObject)
    def mouseReleaseEvent(self, event):
        if self.qpixmap_ref() is None:
            return

        self.panning_scale = self.geometry().width()

        if event.button() == 1 and self.panning_mode:
            self.panning_mode = False
            self.old_panning_point = [None, None]
            QtWidgets.QApplication.restoreOverrideCursor()
            self.cursor_drag = False

        self.cycle_timer()

    def check_mouse_bounds(self):
        mouse_position = QtGui.QCursor.pos()
        upper_left = self.mapToGlobal(QtCore.QPoint(0, 0))
        lower_right = self.mapToGlobal(QtCore.QPoint(self.size[0], self.size[1]))
        bounds = [upper_left.x(), upper_left.y(), lower_right.x(), lower_right.y()]
        mouse_position = [mouse_position.x(), mouse_position.y()]
        position = mouse_position.copy()
        if mouse_position[0] <= bounds[0] + 2:
            position[0] = bounds[2] - 3 + (bounds[0] - mouse_position[0])
        elif mouse_position[0] >= bounds[2] - 2:
            position[0] = bounds[0] + 3 - (bounds[2] - mouse_position[0])
        elif mouse_position[1] <= bounds[1] + 2:
            position[1] = bounds[3] - 3 + (bounds[1] - mouse_position[1])
        elif mouse_position[1] >= bounds[3] - 2:
            position[1] = bounds[1] + 3 - (bounds[3] - mouse_position[1])

        if position != mouse_position:
            point = self.mapFromGlobal(QtCore.QPoint(position[0], position[1]))
            self.just_switched = True
            self.old_panning_point = [point.x(), point.y()]
            QtGui.QCursor.setPos(position[0], position[1])
            return False
        return True

    @QtCore.pyqtSlot(QtCore.QObject)
    def mouseMoveEvent(self, event):
        if self.qpixmap_ref() is None:
            return
        if self.just_switched is True:
            self.just_switched = False
            return

        if self.mouse_hidden:
            self.show_mouse()

        if self.panning_mode is not True:
            self.cycle_timer()

        if self.old_panning_point[0] is None or self.old_panning_point[1] is None:
            return

        if self.panning_mode:
            if self.cursor_drag is False:
                QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.DragMoveCursor)
                self.timer.stop()
                self.cursor_drag = True

            if self.check_mouse_bounds():

                [delta_x, delta_y] = [event.x() - self.old_panning_point[0],
                                      event.y() - self.old_panning_point[1]]

                self.center_x -= 2 * self.half_width / self.panning_scale * delta_x * self.ratio[0]
                self.center_y -= 2 * self.half_width / self.panning_scale * delta_y * self.ratio[0]

                self.old_panning_point = [event.x(), event.y()]

        event.accept()

        self.update()

    @QtCore.pyqtSlot(list)
    def set_viewscope(self, coords):
        if self.isVisible() is False:
            self.set_magnification(coords[0] ** -1)
            self.center_x = coords[1]
            self.center_y = coords[2]
            self.update()

    def toggle_fullscreen(self):
        if self.full_screen is False:
            self.setWindowFlags(QtCore.Qt.Window)
            self.setGeometry(QtWidgets.QApplication.desktop().screenGeometry(self))
            self.showFullScreen()
            self.calculate_ratio()
            self.full_screen = True
        else:
            self.full_screen = False
            self.setWindowFlags(QtCore.Qt.Widget)
            self.show()
            self.calculate_ratio()

    @QtCore.pyqtSlot(QtCore.QObject)
    def keyPressEvent(self, event):
        if self.qpixmap_ref() is None:
            return

        if event.key() == QtCore.Qt.Key_F11:
            self.toggle_fullscreen()

        if event.key() == QtCore.Qt.Key_Escape:
            self.full_screen = False
            self.setWindowFlags(QtCore.Qt.Widget)
            self.show()
            self.calculate_ratio()

        if event.key() == QtCore.Qt.Key_F:
            if self.get_magnification() == 1:
                self.resetView()
            else:
                self.set_magnification(1)

        if event.key() == QtCore.Qt.Key_Right:
            self.center_x += self.half_width / 10
        if event.key() == QtCore.Qt.Key_Left:
            self.center_x -= self.half_width / 10
        if event.key() == QtCore.Qt.Key_Up:
            self.center_y += self.half_width / 10
        if event.key() == QtCore.Qt.Key_Down:
            self.center_y -= self.half_width / 10

        self.update()

    @QtCore.pyqtSlot(QtCore.QObject)
    def keyReleaseEvent(self, event):
        if self.qpixmap_ref() is None:
            return

    def set_magnification(self, mag):
        self.half_width = mag * self.size[0] / 2 / self.ratio[0] * self.window().devicePixelRatio()

    def get_magnification(self):
        return (2 * self.ratio[0] * self.half_width / self.size[0]) ** -1 * self.window().devicePixelRatio()

    def return_viewport(self):
        return (self.center_x - self.half_width * self.ratio[0], self.center_y - self.half_width * self.ratio[1],
                2 * self.half_width * self.ratio[0], 2 * self.half_width * self.ratio[1])

    @property
    def half_width(self):
        return self._half_width

    @half_width.setter
    def half_width(self, value):
        self._half_width = value
