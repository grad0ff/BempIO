from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QFont


class DI0_Button(QPushButton):
    BUTTONS_IS_PRESSED = False

    def __init__(self, *args):
        super().__init__()
        self.__isTriggered = False

    def mousePressEvent(self, event):
        if self.isCheckable():
            if not self.isChecked():
                self.setChecked(True)
            else:
                self.setChecked(False)
            DI0_Button.BUTTONS_IS_PRESSED = True

    def set_btn_num(self, num):
        self.num = num

    def setTriggered(self, val):
        self.__isTriggered = val
        self.change_triggered_style()

    def isTriggered(self):
        return self.__isTriggered

    def change_triggered_style(self):
        if self.isTriggered():
            if self.isChecked():  # если нажата кнопка DIO, то при срабатывании
                self.change_style('checked')  # цвет меняется на синий
            else:
                self.change_style('triggered')  # цвет меняется на зеленый
        else:
            self.change_style('default')  # цвет меняется на исходный

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


class DI_Button(DI0_Button):
    TYPE = 'DI'
    TRIGGERED_LIST = set()

# def mousePressEvent(self, event):
#     DI0_Button.mousePressEvent(self, event)


class DO_Button(DI0_Button):
    TYPE = 'DO'
    TRIGGERED_LIST = set()

# def mousePressEvent(self, event):
#     DI0_Button.mousePressEvent(self, event)
