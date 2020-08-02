from PyQt5 import QtCore, QtGui, QtWidgets, uic, QtSvg
from PyQt5.QtCore import *
#from PyQt5.QtCore import Qt, QTimer, QThread
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import queue
import monitor_ui

MAX_TABLE_RECORDS = 500


class CommunicationsMonitor():
    def __init__(self):
        self.dialog = QtWidgets.QDialog()
        self.dialog.ui = monitor_ui.Ui_CommunicationsMonitor()
        self.dialog.ui.setupUi(self.dialog)
        self.dialog.ui.push_clear.clicked.connect(self.push_clear_clicked)

        self.table = self.dialog.ui.table_gcode_log
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        #header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.table.verticalHeader().hide()

    def show_modal(self):
        ret = self.dialog.exec_()
        return ret

    def show(self):
        self.dialog.show()

    def add_log_cmd(self, cmd):
        rowPosition = self.table.rowCount()
        if rowPosition > MAX_TABLE_RECORDS:
            self.table.removeRow(0)

        rowPosition = self.table.rowCount()
        self.table.insertRow(rowPosition)
        self.table.setItem(rowPosition, 0, QtWidgets.QTableWidgetItem(cmd))

        self.table.scrollToBottom()

    def add_log_response(self, response):
        rowPosition = self.table.rowCount()-1

        item = QtWidgets.QTableWidgetItem(response)
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(rowPosition, 1, item)

    def push_clear_clicked(self):
        while self.table.rowCount() > 0:
            self.table.removeRow(0)
