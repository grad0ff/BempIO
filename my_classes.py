from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QFont


class MyButton(QPushButton):
    def __init__(self, *args):
        super().__init__(*args)
        self.setCheckable(True)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if not self.isChecked():
            self.setChecked(True)
        else:
            self.setChecked(False)


class ConnectButton(MyButton):

    def change_style(self, a0: bool):
        if a0:
            self.setStyleSheet('background: rgb(50,255,50)')
            self.setText('ОТКЛЮЧИТЬ')
        else:
            self.setText('ПОДКЛЮЧИТЬ')
            self.setStyleSheet('background: rgb(255,85,70)')


class DI0Button(MyButton):
    def __init__(self, *args):
        super().__init__(*args)
        self.setCheckable(False)
        self._is_triggered = False
        self.voicing_flag = False

    # НАЖАТИЕ НА КНОПКУ DI ИЛИ DO
    def mousePressEvent(self, event):
        if self.is_clickable():
            # super().mousePressEvent(event)
            if not self.isChecked():
                self.setChecked(True)
                self.set_pressed_flag()
            else:
                self.reset_pressed_flag()

    # ВЫСТАВЛЕНИЕ КЛИКАБЕЛЬНОСТИ DI ИЛИ DO
    def set_clickable(self, a0: bool):
        self.setCheckable(a0)
        self._CLICKABLE_FLAG = a0

    def is_clickable(self):
        return self._CLICKABLE_FLAG

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
        return self.__class__._TRIGGERED_LIST

    def add_to_triggered_dio_list(self, element):
        self.__class__._TRIGGERED_LIST.add(element)

    def del_from_triggered_dio_list(self, element):
        self.__class__._TRIGGERED_LIST.remove(element)

    def get_pressed_flag(self):
        return self.__class__._PRESSED_FLAG

    def set_pressed_flag(self):
        self.__class__._PRESSED_FLAG = True

    def reset_pressed_flag(self):
        self.__class__._PRESSED_FLAG = False

    def set_voicing_flag(self):
        self.voicing_flag = True

    def get_voicing_flag(self):
        return self.voicing_flag


class DIButton(DI0Button):
    _PRESSED_FLAG = False
    _CLICKABLE_FLAG = False
    _TRIGGERED_LIST = set()

    def __init__(self, *args):
        super().__init__(*args)
        self.type = 'DI'


class DOButton(DI0Button):
    _PRESSED_FLAG = False
    _CLICKABLE_FLAG = False
    _TRIGGERED_LIST = set()

    def __init__(self, *args):
        super().__init__(*args)
        self.type = 'DO'
