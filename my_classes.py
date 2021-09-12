from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QFont


class MyButton(QPushButton):
    def __init__(self, *args):
        super().__init__(*args)
        self.setCheckable(True)

    # НАЖАТИЕ НА КНОПКУ
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if not self.isChecked():
            self.setChecked(True)
        else:
            self.setChecked(False)


class DOControl(QPushButton):

    def set_do_control(self, val: bool):
        DOButton.DO_CONTROL = val

    def is_do_control(self):
        return DOButton.DO_CONTROL


class ConnectButton(MyButton):

    def change_style(self, val: bool):
        if val:
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
                self.set_pressed_flag(True)
            else:
                self.setChecked(False)

    # ВЫСТАВЛЕНИЕ КЛИКАБЕЛЬНОСТИ DI ИЛИ DO
    def setCheckable(self, val: bool):
        super().setCheckable(val)
        self.__class__._CLICKABLE_FLAG = val

    def is_clickable(self):
        return self.__class__._CLICKABLE_FLAG

    def set_button_num(self, num):
        self.num = num

    def set_triggered(self, val: bool):
        self._is_triggered = val

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
            self.setFont(QFont('MS Shell Dlg 2', 10, QFont.Bold))

    def get_triggered_list(self):
        return self.__class__._TRIGGERED_LIST

    def add_to_triggered_dio_list(self, element):
        self.__class__._TRIGGERED_LIST.add(element)

    def del_from_triggered_dio_list(self, element):
        self.__class__._TRIGGERED_LIST.remove(element)

    def get_pressed_flag(self):
        return self.__class__._PRESSED_FLAG

    def set_pressed_flag(self, val: bool):
        self.__class__._PRESSED_FLAG = val

    def get_voicing_flag(self):
        return self.voicing_flag

    def set_voicing_flag(self, val: bool):
        self.voicing_flag = val


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
    DO_CONTROL = False

    def __init__(self, *args):
        super().__init__(*args)
        self.type = 'DO'

    def change_style(self, state):
        super().change_style(state)
        if state == 'controlled':
            self.setStyleSheet('background: rgb(255,85,70)')
