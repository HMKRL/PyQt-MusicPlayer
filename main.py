#!/usr/bin/python3

import sys
from mainwindow import MainWindow

from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':

    app = QApplication(sys.argv)

    w = MainWindow()
    w.show()

    sys.exit(app.exec_())
