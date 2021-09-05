from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QFont


class DI0_Button(QPushButton):

    def __init__(self, *args):
        super().__init__()
        self._is_triggered = False

    # НАЖАТИЕ НА КНОПКУ DI ИЛИ DO
    def mousePressEvent(self, event):
        if self.is_clickable():
            if not self.isChecked():
                self.setChecked(True)
                if isinstance(self, DI_Button):
                    self._BUTTONS_IS_PRESSED = True
                elif isinstance(self, DO_Button):
                    self._BUTTONS_IS_PRESSED = True
            else:
                self.setChecked(False)

    # ВЫСТАВЛЕНИЕ КЛИКАБЕЛЬНОСТИ DI ИЛИ DO
    def set_clickable(self, a0: bool):
        self.setCheckable(a0)
        self._BUTTONS_IS_CLICKABLE = a0

    def is_clickable(self):
        return self._BUTTONS_IS_CLICKABLE

    def set_button_num(self, num):
        self.num = num

    def set_triggered(self, a0: bool):
        self._is_triggered = a0

    def is_triggered(self):
        return self._is_triggered

    def change_style(self, state):
        if state == 'default':
            self.setStyleSheet('background:  #f0f0f0')
            self.setFont(QFont('MS Shell Dlg 2', 9, QFont.Normal))
        else:
            if state == 'triggered':
                self.setStyleSheet('background: rgb(50,255,50)')
            elif state == 'pressed':
                self.setStyleSheet('background: rgb(150,200,250)')
            self.setFont(QFont('MS Shell Dlg 2', 9, QFont.Bold))

    def get_triggered_list(self):
        return self._TRIGGERED_LIST

    def add_to_triggered_dio_list(self, element):
        self._TRIGGERED_LIST.add(element)

    def del_from_triggered_dio_list(self, element):
        self._TRIGGERED_LIST.remove(element)

    def get_type(self):
        return self._TYPE

    def get_pressed_flag(self):
        return self._BUTTONS_IS_PRESSED

    def reset_pressed_flag(self):
        self._BUTTONS_IS_PRESSED = False


class DI_Button(DI0_Button):
    _TYPE = 'DI'
    _BUTTONS_IS_PRESSED = False
    _BUTTONS_IS_CLICKABLE = False
    _TRIGGERED_LIST = set()


class DO_Button(DI0_Button):
    _TYPE = 'DO'
    _BUTTONS_IS_PRESSED = False
    _BUTTONS_IS_CLICKABLE = False
    _TRIGGERED_LIST = set()
