from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

class GcodeSender(QObject):
    feedback = pyqtSignal(list)
    line_nr = pyqtSignal(int)
    # add position callback

    gcode = []
    current_pos = 0

    def __init__(self, ser, gcode, feedback_interval=0.1):
        self.feedback_interval = feedback_interval
        pass

    def pause_on(self, mask, callback):
        pass

    def run(self):
        pass

    def step(self):
        pass

    def resume(self):
        pass
    
    def odometer(self):
        # TODO: save this in config settings for future analysis if needed
        pass
