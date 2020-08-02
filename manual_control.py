from PyQt5 import QtCore, QtGui, QtWidgets, uic, QtSvg
from PyQt5.QtCore import *
#from PyQt5.QtCore import Qt, QTimer, QThread
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import queue
import manual_control_ui

MAX_TABLE_RECORDS = 500

class ManualControl():
    active_axis = ""
    short_jog = 0.5
    long_jog = 5

    def __init__(self, hw=None):
        self.hw = hw
        self.dialog = QtWidgets.QDialog()
        self.dialog.ui = manual_control_ui.Ui_ManualControl()
        self.dialog.ui.setupUi(self.dialog)
        self.dialog.ui.push_manual_go.clicked.connect(self.push_manual_go_clicked)
        self.dialog.ui.push_gcode_send.clicked.connect(self.push_gcode_send_clicked)

        self.dialog.ui.push_fwd1.clicked.connect(self.push_fwd1_clicked)
        self.dialog.ui.push_fwd2.clicked.connect(self.push_fwd2_clicked)
        self.dialog.ui.push_back1.clicked.connect(self.push_back1_clicked)
        self.dialog.ui.push_back2.clicked.connect(self.push_back2_clicked)

        self.set_active_axis('X')
        self.enable(False)

    def enable(self, status):
        if status:
            self.dialog.setEnabled(True)
        else:
            self.dialog.setEnabled(False)

    def set_active_axis(self, axis):
        self.active_axis = axis
        self.dialog.ui.label_active_axis.setText(axis)

    def show_modal(self):
        ret = self.dialog.exec_()
        return ret

    def show(self):
        self.dialog.show()

    def push_manual_go_clicked(self):
        pos = self.dialog.ui.double_position.value()
        speed = self.dialog.ui.double_speed.value()
        if speed > 0:
            cmd = "G1 "+self.active_axis+str(pos)
            cmd += " F"+str(speed)
        else:
            cmd = "G0 "+self.active_axis+str(pos)

        self.hw.send("G90\n")   # ABS
        self.hw.send(cmd + "\n")

    def push_gcode_send_clicked(self):
        cmd = self.dialog.ui.line_gcode_string.text()
        self.hw.send(cmd+"\n")

    def push_back1_clicked(self):
        self.hw.send("G91\n")  # ABS
        cmd = "G0 " + self.active_axis + "-" + str(self.short_jog)
        self.hw.send(cmd + "\n")

    def push_back2_clicked(self):
        self.hw.send("G91\n")  # ABS
        cmd = "G0 " + self.active_axis + "-" + str(self.long_jog)
        self.hw.send(cmd + "\n")

    def push_fwd1_clicked(self):
        self.hw.send("G91\n")  # ABS
        cmd = "G0 " + self.active_axis + str(self.short_jog)
        self.hw.send(cmd + "\n")

    def push_fwd2_clicked(self):
        self.hw.send("G91\n")  # ABS
        cmd = "G0 " + self.active_axis + str(self.long_jog)
        self.hw.send(cmd + "\n")
