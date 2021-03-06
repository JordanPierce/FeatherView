#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets, QtCore, QtGui
from qlabelextended import QLabelExtended
import os
import json
import sip
import sys


sip.setapi("QVariant", 2)


class FeatherView(QtWidgets.QMainWindow):
    draw_image = QtCore.pyqtSignal()

    def __init__(self, file_name, directory, sep):
        super(FeatherView, self).__init__()

        self.sep = sep
        self.directory = directory
        self.file_name = file_name

        self.main_layout = None
        self.view = None
        self.qpixmap = None
        self.initUI()
        self.draw_image.connect(self.open_file, type=QtCore.Qt.QueuedConnection)
        self.draw_image.emit()
        self.controls = dict()

        home = os.path.expanduser("~")
        if not os.path.isdir(home + sep + ".config"):
            os.mkdir(home + sep + ".config")
        if not os.path.isdir(home + sep + ".config" + sep + "FeatherView"):
            os.mkdir(home + sep + ".config" + sep + "FeatherView")
        self.home = home + sep + ".config" + sep + "FeatherView" + sep
        with open(self.home + "config", 'r', 1) as file:
            try:
                self.controls = json.load(file)
            except json.JSONDecodeError:
                pass

        try:
            self.setGeometry(0, 0, self.controls['size'][0], self.controls['size'][1])
        except KeyError:
            pass

        try:
            if self.controls['maximized']:
                self.showMaximized()
        except KeyError:
            pass

    def mouseMoveEvent(self, event):
        if self.view is not None:
            self.view.mouseMoveEvent(event)

    def initUI(self):
        self.view = QLabelExtended(self)
        self.view.setMouseTracking(True)
        self.setCentralWidget(self.view)

    def open_file(self):
        qimage = QtGui.QImage()
        qimage.load(self.file_name)
        size = qimage.size()
        self.qpixmap = QtGui.QPixmap(size.width(), size.height())
        self.qpixmap.convertFromImage(qimage)
        self.view.initialize(self.qpixmap)

    def keyPressEvent(self, event):
        self.view.keyPressEvent(event)

    def resizeEvent(self, event):
        super(FeatherView, self).resizeEvent(event)
        if self.view is not None:
            self.view.resetView()

    def closeEvent(self, closeEvent):
        size = self.size()
        self.controls['size'] = [size.width(), size.height()]
        self.controls['maximized'] = self.isMaximized()
        with open(self.home + "config", 'w') as file:
            json.dump(self.controls, file, indent=2, sort_keys=True)

        closeEvent.accept()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("No file do open")
    elif not os.path.isfile(sys.argv[1]):
        print("Cannot open file")
    else:
        app = QtWidgets.QApplication(sys.argv)
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, on=QtCore.Qt.Checked)

        directory = os.path.dirname(__file__)
        if os.name == 'nt':
            sep = '\\'
        else:
            sep = '/'

        name = sys.argv[1]
        main_app = FeatherView(name, directory=directory, sep=sep)
        app_icon = QtGui.QIcon()
        app_icon.addFile(sep.join([directory, "feather.svg"]))
        main_app.setWindowIcon(app_icon)
        main_app.setWindowTitle(name[name.rfind(sep) + 1:])
        main_app.show()
        sys.exit(app.exec_())
