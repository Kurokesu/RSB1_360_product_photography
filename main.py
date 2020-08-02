import logs
import version
import json
import sys
from pathlib import Path
from PyQt5 import QtCore, QtGui, QtWidgets, uic, QtSvg
from PyQt5.QtCore import *
#from PyQt5.QtCore import Qt, QTimer, QThread
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import numpy as np
import queue
import utils
import motion
import pkg_resources.py2_warn   # fix pyinstaller error

import main_ui
import gcode_generator
import monitor
import manual_control
import settings_ui
import about_ui

import logging
LOGGER = logging.getLogger(__name__)
LOGGER.info('start')

COLOR_GREEN = '#33cc33'
COLOR_YELLOW = '#E5B500'
COLOR_RED = '#A0150E'
SETTINGS_FILE = 'settings.json'

if sys.platform == 'win32':
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)


class VLine(QFrame):
    def __init__(self):
        super(VLine, self).__init__()
        self.setFrameShape(self.VLine|self.Sunken)

class MyWindowClass(QtWidgets.QMainWindow, main_ui.Ui_MainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)

        self.current_motion_profile = None
        self.current_motion_filename = None
        self.hw_connected = False
        self.source_filename = ""

        # load settings from json
        self.config = {}
        self.config = utils.json_boot_routine(SETTINGS_FILE)

        self.setupUi(self)
        self.original_window_name = self.windowTitle()
        self.setWindowTitle(self.original_window_name + " (" + version.__version__ + ")")

        # Status Bar
        self.s_status = QtWidgets.QLabel("--")
        self.s_status.setToolTip("Motor status")
        self.s_position = QtWidgets.QLabel("--")
        self.s_position.setToolTip("Active motor position")
        self.s_controller_fw = QtWidgets.QLabel("--")
        self.s_controller_fw.setToolTip("Controller firmware")
        self.s_script = QtWidgets.QLabel("--")
        self.s_script.setToolTip("Loaded script name")

        self.statusBar.addPermanentWidget(self.s_status)
        self.statusBar.addPermanentWidget(VLine())
        self.statusBar.addPermanentWidget(self.s_position)
        self.statusBar.addPermanentWidget(VLine())
        self.statusBar.addPermanentWidget(self.s_controller_fw)

        # Menu buttons
        self.action_about.triggered.connect(self.action_about_clicked)
        self.action_settings.triggered.connect(self.action_settings_clicked)
        self.action_manual_control.triggered.connect(self.action_manual_control_clicked)
        self.action_monitor.triggered.connect(self.action_monitor_clicked)
        self.action_edit_motion_script.triggered.connect(self.action_edit_motion_script_clicked)
        self.action_save_script.triggered.connect(self.action_save_script_clicked)
        self.action_save_as_script.triggered.connect(self.action_save_as_script_clicked)
        self.action_load_script.triggered.connect(self.action_load_script_clicked)

        # all other buttons
        self.button_connect.clicked.connect(self.btn_connect_clicked)
        self.button_disconnect.clicked.connect(self.btn_disconnect_clicked)
        self.button_com_refresh.clicked.connect(self.button_com_refresh_clicked)
        self.push_run.clicked.connect(self.push_run_clicked)

        # more UI tweaking
        self.button_connect.setStyleSheet("background-color: " + COLOR_GREEN)
        children = self.findChildren(QtWidgets.QPushButton)
        for c in children:
            c.setEnabled(False)
        self.button_connect.setEnabled(True)
        self.button_com_refresh.setEnabled(True)

        # prepare serial communications
        self.hw = motion.SerialComm()
        self.thread_serial = QtCore.QThread()
        self.hw.strStatus.connect(self.serStatus)
        self.hw.serReceive.connect(self.controller_read)
        self.hw.current_line_feedback.connect(self.current_line_feedback)
        self.hw.strVersion.connect(self.serVersion)
        self.hw.strError.connect(self.strError)
        self.hw.serFeedback.connect(self.serFeedback)
        self.hw.moveToThread(self.thread_serial)
        self.thread_serial.started.connect(self.hw.serial_worker)
        self.thread_serial.start()
        self.button_com_refresh_clicked()

        # initialize gcode generator and manual control windows
        self.gcode_generator = gcode_generator.CodeGenerator()
        self.manual_control = manual_control.ManualControl(self.hw)
        self.monitor = monitor.CommunicationsMonitor()
        self.hw.log_tx.connect(self.monitor.add_log_cmd)
        self.hw.log_rx.connect(self.monitor.add_log_response)

    def push_run_clicked(self):
        line_count = 0
        for line in self.current_motion_profile["text"]["text_gcode"].splitlines():
            self.hw.send(line+"\n")
            line_count += 1

        self.progress_program.setMaximum(line_count)
        self.progress_program.setValue(line_count)

        self.update_enabled_elements()

    def btn_connect_clicked(self):
        self.config["port"] = self.combo_comports.currentText()
        self.hw.connect(self.config["port"], self.config["com_baud"], self.config["com_timeout"])

    def btn_disconnect_clicked(self):
        self.hw.disconnect()

    def controller_read(self, data):
        pass

    def update_enabled_elements(self):

        if not self.hw.commands.empty():
            self.push_run.setEnabled(False)

        if self.hw_connected:
            self.combo_comports.setEnabled(False)
            self.button_connect.setEnabled(False)
            self.button_com_refresh.setEnabled(False)
            self.button_disconnect.setEnabled(True)
            self.button_connect.setStyleSheet("")
            self.manual_control.enable(True)
            if self.current_motion_profile:
                if self.hw.commands.empty():
                    self.push_run.setEnabled(True)

        else:
            self.combo_comports.setEnabled(True)
            self.button_connect.setEnabled(True)
            self.button_com_refresh.setEnabled(True)
            self.button_disconnect.setEnabled(False)
            self.manual_control.enable(False)
            self.s_position.setText("0°")
            self.button_connect.setStyleSheet("background-color: " + COLOR_GREEN)
            self.push_run.setEnabled(False)

    def serStatus(self, text):
        self.s_status.setText(text)
        self.combo_comports.setEnabled(False)
        self.button_connect.setEnabled(False)
        self.button_disconnect.setEnabled(False)
        
        if text == "Connected":
            self.hw_connected = True
            self.hw.action_recipe.put("status1")
            self.hw.action_recipe.put("version")
            self.hw.action_recipe.put("get_param_list")

        if text == "Disconnected":
            self.hw_connected = False

        self.update_enabled_elements()

    def button_com_refresh_clicked(self):
        self.combo_comports.clear()
        com_ports = sorted(self.hw.get_compot_list())
        for port, desc in com_ports:
            self.combo_comports.addItem(port.strip())
        self.combo_comports.setCurrentIndex(self.combo_comports.findText(self.config["port"]))

    def strError(self, text):
        LOGGER.error(text)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(text)
        msg.setWindowTitle("Error")
        msg.exec_()

    def serVersion(self, text):
        self.s_controller_fw.setText(text)

    def serFeedback(self, text):
        status = {}

        if len(text) < 5:
            return None

        if text[0] != "<":
            return None

        if not ((text[0] == "<") and (text[-1] == ">")):
            raise Exception("Bad format 1")

        text = text[1:-1]
        feedback_split = text.split("|")

        status["STATUS"] = feedback_split[0]

        if feedback_split[1].find("MPos") < 0:
            raise Exception("Bad format 2")

        positions = feedback_split[1].split(":")
        if len(positions) != 2:
            raise Exception("Bad format 3")

        positions = positions[1]
        positions = positions.split(",")
        if len(positions) != 4:
            raise Exception("Bad format 4")

        status["MPOS_X"] = float(positions[0])
        status["MPOS_Y"] = float(positions[1])
        status["MPOS_Z"] = float(positions[2])
        status["MPOS_A"] = float(positions[3])

        positions = feedback_split[2].split(":")
        if len(positions) != 2:
            raise Exception("Bad format 5")

        positions = positions[1]
        positions = positions.split(",")
        if len(positions) != 2:
            raise Exception("Bad format 6")

        status["BUFFERS"] = int(positions[0])

        active_axis = self.gcode_generator.dialog.ui.combo_active_axis.currentText()
        mpos_x = float(status["MPOS_"+active_axis])
        self.s_position.setText("{:.2f}°".format(mpos_x))

        commands_in_buffer = self.hw.commands.qsize()
        self.progress_program.setValue(self.progress_program.maximum() - int(commands_in_buffer))
        self.s_status.setText(status["STATUS"])
        self.update_enabled_elements()

    def action_about_clicked(self):
        dialog = QtWidgets.QDialog()
        dialog.ui = about_ui.Ui_About()
        dialog.ui.setupUi(dialog)
        dialog.exec_()

    def action_settings_clicked(self):
        dialog = QtWidgets.QDialog()
        dialog.ui = settings_ui.Ui_Settings()
        dialog.ui.setupUi(dialog)

        dialog.ui.check_remember_last_loaded_profile.setChecked(self.config["remember_last_loaded_profile"])
        dialog.ui.check_remember_last_com_port.setChecked(self.config["remember_last_com_port"])
        dialog.ui.check_auto_connect_after_restart.setChecked(self.config["auto_connect_after_restart"])
        dialog.ui.check_beep_when_done.setChecked(self.config["beep_when_done"])
        dialog.ui.check_flash_when_done.setChecked(self.config["flash_when_done"])
        dialog.ui.check_start_compact.setChecked(self.config["start_compact"])

        ret = dialog.exec_()
        if ret:
            self.config["remember_last_loaded_profile"] = dialog.ui.check_remember_last_loaded_profile.isChecked()
            self.config["remember_last_com_port"] = dialog.ui.check_remember_last_com_port.isChecked()
            self.config["auto_connect_after_restart"] = dialog.ui.check_auto_connect_after_restart.isChecked()
            self.config["beep_when_done"] = dialog.ui.check_beep_when_done.isChecked()
            self.config["flash_when_done"] = dialog.ui.check_flash_when_done.isChecked()
            self.config["start_compact"] = dialog.ui.check_start_compact.isChecked()

    def action_edit_motion_script_clicked(self):
        ret = self.gcode_generator.show_modal()
        if ret:
            self.gcode_generator.push_generate_clicked()
            active_axis = self.gcode_generator.dialog.ui.combo_active_axis.currentText()
            self.manual_control.set_active_axis(active_axis)

            values = self.gcode_generator.collect_values()
            self.current_motion_profile = values
            self.action_save_script.setEnabled(True)

        self.update_enabled_elements()

    def action_manual_control_clicked(self):
        self.manual_control.show()

    def action_monitor_clicked(self):
        self.monitor.show()

    def current_line_feedback(self, text):
        if len(text)>2:
            if text[0] == ";":
                text_ = text[1:].strip()
                self.label_gcode_comment.setText(text_)

    def action_save_script_clicked(self):
        with open(self.source_filename, 'w') as outfile:
            json.dump(self.current_motion_profile, outfile)

    def action_save_as_script_clicked(self):
        fileName, _ = QFileDialog.getSaveFileName(self, "Save motion script as...", "", "Motion script (*.profile)")
        if fileName:
            with open(fileName, 'w') as outfile:
                json.dump(self.current_motion_profile, outfile)


    def action_load_script_clicked(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open motion script...", "", "Motion script (*.profile)")
        if fileName:
            with open(fileName) as json_file:
                self.current_motion_profile = json.load(json_file)
                self.gcode_generator.populate_values(self.current_motion_profile)

                script_name = Path(fileName).stem
                self.s_script.setText(script_name)
                self.update_enabled_elements()
                self.action_save_script.setEnabled(True)
                self.action_save_as_script.setEnabled(True)
                self.source_filename = fileName

    def closeEvent(self, event):
        global config
        global running
        utils.json_exit_routine(SETTINGS_FILE, self.config)
        running = False
        app.quit()


app = QtWidgets.QApplication(sys.argv)
app.setStyle('Fusion')
myWindow = MyWindowClass(None)
myWindow.show()
app.exec_()

