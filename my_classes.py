from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QFont


class DI0_Button(QPushButton):
    PRESSED_BUTTONS = 0

    def mousePressEvent(self, event):
        if not self.isChecked():
            self.setChecked(True)
            DI0_Button.PRESSED_BUTTONS += 1
        else:
            self.setChecked(False)
            DI0_Button.PRESSED_BUTTONS -= 1


class DIO_Button_Style(QPushButton):

    def change_style(self, state):
        if state == 'default':
            self.setStyleSheet('background:  #f0f0f0')
            self.setFont(QFont('MS Shell Dlg 2', 9, QFont.Normal))
        else:
            if state == 'triggered':
                self.setStyleSheet('background: rgb(50,255,50)')
            elif state == 'checked':
                self.setStyleSheet('background: rgb(150,200,250)')
            self.setFont(QFont('MS Shell Dlg 2', 9, QFont.Bold))


class DI_Button(DI0_Button, DIO_Button_Style):

    def mousePressEvent(self, event):
        DI0_Button.mousePressEvent(self, event)


class DO_Button(DI0_Button, DIO_Button_Style):

    def mousePressEvent(self, event):
        DI0_Button.mousePressEvent(self, event)
