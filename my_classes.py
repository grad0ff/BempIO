from PyQt5.QtWidgets import QPushButton


class DI0_Button(QPushButton):
    PRESSED_BUTTONS = 0

    def mousePressEvent(self, event):
        if not self.isChecked():
            self.setChecked(True)
            DI0_Button.PRESSED_BUTTONS += 1
        else:
            self.setChecked(False)
            DI0_Button.PRESSED_BUTTONS -= 1


class DI_Button(DI0_Button):
    def mousePressEvent(self, event):
        DI0_Button.mousePressEvent(self, event)


class DO_Button(DI0_Button):
    def mousePressEvent(self, event):
        DI0_Button.mousePressEvent(self, event)
