from PyQt5.QtWidgets import QPushButton


class DI0_Button(QPushButton):
    PRESSED_BUTTONS = 0

    def mousePressEvent(self, event):
        if not self.isChecked():
            self.setCheckable(True)
            self.setChecked(True)
            DI0_Button.PRESSED_BUTTONS += 1
        else:
            self.setChecked(False)
            DI0_Button.PRESSED_BUTTONS -= 1


class DI_Button(DI0_Button):
    def mousePressEvent(self, event):
        DI0_Button.mousePressEvent(self, event)
        if self.isChecked():
            print(f'DI{self.text()} pressed')
        else:
            print(f'DI{self.text()} unpressed')


class DO_Button(DI0_Button):
    def mousePressEvent(self, event):
        DI0_Button.mousePressEvent(self, event)
        if self.isChecked():
            print(f'DO{self.text()} pressed')
        else:
            print(f'DO{self.text()} unpressed')
