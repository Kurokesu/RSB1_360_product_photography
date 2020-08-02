from PyQt5 import QtCore, QtGui, QtWidgets, uic, QtSvg
from PyQt5.QtCore import *
#from PyQt5.QtCore import Qt, QTimer, QThread
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

__generator_version__ = "0.1.2"

import gcode_generator_ui


class CodeGenerator():
    default = {}

    def __init__(self):
        self.dialog = QtWidgets.QDialog()
        self.dialog.ui = gcode_generator_ui.Ui_CodeGenerator()
        self.dialog.ui.setupUi(self.dialog)
        self.dialog.ui.push_generate.clicked.connect(self.push_generate_clicked)
        self.dialog.ui.motor_combo_mode.currentIndexChanged.connect(self.motor_combo_mode_changed)

        self.dialog.ui.motor_steps.valueChanged.connect(self.motor_angle_recalc)
        self.dialog.ui.motor_angle.valueChanged.connect(self.motor_angle_recalc)
        self.dialog.ui.motor_total_angle.valueChanged.connect(self.motor_angle_recalc)

        self.default = self.collect_values()
        self.motor_angle_recalc()
        self.motor_combo_mode_changed(0)

    def motor_angle_recalc(self):
        mode = self.dialog.ui.motor_combo_mode.currentIndex()

        steps = self.dialog.ui.motor_steps.value()
        angle = self.dialog.ui.motor_angle.value()
        total_angle = self.dialog.ui.motor_total_angle.value()

        if mode == 0:
            self.dialog.ui.motor_total_angle.setValue(360)
            self.dialog.ui.motor_angle.setValue(360 / steps)

        if mode == 1:
            self.dialog.ui.motor_angle.setValue(total_angle / steps)

        if mode == 2:
            self.dialog.ui.motor_total_angle.setValue(angle * steps)

    def motor_combo_mode_changed(self, index):
        #print("Changed", index)
        if index == 0:
            self.dialog.ui.motor_start_angle.setEnabled(True)
            self.dialog.ui.motor_speed.setEnabled(True)
            self.dialog.ui.motor_steps.setEnabled(True)
            self.dialog.ui.motor_angle.setEnabled(False)
            self.dialog.ui.motor_total_angle.setEnabled(False)
            self.dialog.ui.motor_check_return.setEnabled(True)

        if index == 1:
            self.dialog.ui.motor_start_angle.setEnabled(True)
            self.dialog.ui.motor_speed.setEnabled(True)
            self.dialog.ui.motor_steps.setEnabled(True)
            self.dialog.ui.motor_angle.setEnabled(False)
            self.dialog.ui.motor_total_angle.setEnabled(True)
            self.dialog.ui.motor_check_return.setEnabled(True)

        if index == 2:
            self.dialog.ui.motor_start_angle.setEnabled(True)
            self.dialog.ui.motor_speed.setEnabled(True)
            self.dialog.ui.motor_steps.setEnabled(True)
            self.dialog.ui.motor_angle.setEnabled(True)
            self.dialog.ui.motor_total_angle.setEnabled(False)
            self.dialog.ui.motor_check_return.setEnabled(True)

    def collect_values(self):
        result = {}

        values = {}
        children = self.dialog.findChildren(QtWidgets.QDoubleSpinBox)
        for c in children:
            values[c.objectName()] = c.value()

        combobox = {}
        children = self.dialog.findChildren(QtWidgets.QComboBox)
        for c in children:
            combobox[c.objectName()] = c.currentIndex()

        check = {}
        children = self.dialog.findChildren(QtWidgets.QCheckBox)
        for c in children:
            check[c.objectName()] = c.isChecked()

        text = {}
        children = self.dialog.findChildren(QtWidgets.QTextEdit)
        for c in children:
            text[c.objectName()] = c.toPlainText()

        #gcode = self.dialog.ui.text_gcode.toPlainText()
        #note = self.dialog.ui.text_note.toPlainText()

        result["version"] = __generator_version__
        result["values"] = values
        result["combobox"] = combobox
        result["check"] = check
        result["text"] = text

        return result

    def populate_values(self, data):
        kind = "values"
        for item in data[kind]:
            value = data[kind][item]
            #print(item, value)
            child = self.dialog.findChild(QtWidgets.QDoubleSpinBox, item)
            child.setValue(value)

        kind = "combobox"
        for item in data[kind]:
            value = data[kind][item]
            #print(item, value)
            child = self.dialog.findChild(QtWidgets.QComboBox, item)
            child.setCurrentIndex(value)

        kind = "check"
        for item in data[kind]:
            value = data[kind][item]
            #print(item, value)
            child = self.dialog.findChild(QtWidgets.QCheckBox, item)
            if value:
                child.setChecked(True)
            else:
                child.setChecked(False)

        kind = "text"
        for item in data[kind]:
            value = data[kind][item]
            child = self.dialog.findChild(QtWidgets.QTextEdit, item)
            child.clear()
            child.insertPlainText(value)

    def show_modal(self):
        ret = self.dialog.exec_()
        return ret

    def show(self):
        self.dialog.show()

    def push_generate_clicked(self):
        values = self.collect_values()
        gcode = []
        axis_list = ["X", "Y", "Z", "A"]

        if values["check"]["motor_reverse_dir"]:
            direction_prefix = -1
        else:
            direction_prefix = 1

        gcode.append("; Generator version: "+__generator_version__)
        gcode.append("; Set relative movement mode")
        gcode.append("G91")
        gcode.append("")

        gcode.append("; Set global speed")
        gcode.append("F"+str(values["values"]["motor_speed"]))
        gcode.append("")

        gcode.append("; Start main movement")

        # TODO: initial move

        if values["combobox"]["motor_combo_mode"] == 0:

            #angle = 360.0 / self.steps
            for a in range(int(values["values"]["motor_steps"])):
                gcode.append("; Moving to pos " + str(a)+"...")
                gcode.append("G1 "+axis_list[values["combobox"]["combo_active_axis"]]+str(direction_prefix * values["values"]["motor_angle"]))

                if values["combobox"]["dslr_mode"] == 0:
                    gcode.append("; Wait till platform is stable")
                    gcode.append("G4 P" + str(values["values"]["dslr_pre_shutter_sleep_time"]))
                    gcode.append("; Trigger shutter")
                    gcode.append("M8")
                    gcode.append("; Capturing...")
                    gcode.append("G4 P" + str(values["values"]["dslr_shutter_pressed_time"]))
                    gcode.append("; Retract shutter")
                    gcode.append("M9")
                    gcode.append("; Wait post trigger")
                    gcode.append("G4 P" + str(values["values"]["dslr_post_shutter_sleep_time"]))
                    gcode.append("")

        gcode.append("")
        gcode.append("; Set absolute movement mode")
        gcode.append("G90")     # set absolute mode

        if values["check"]["motor_check_return"]:
            gcode.append("; Moving home...")
            gcode.append("G1 " + axis_list[values["combobox"]["combo_active_axis"]] + "0")

        gcode.append("; Complete")


        self.dialog.ui.text_gcode.clear()
        for line in gcode:
            self.dialog.ui.text_gcode.append(line)


