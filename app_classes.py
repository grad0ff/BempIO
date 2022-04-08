from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QFont, QIcon

import app_service


class MyButton(QPushButton):
    RED_COLOR = 'rgb(255, 100, 100)'
    GREEN_COLOR = 'rgb(50, 255, 50)'
    BLUE_COLOR = 'rgb(150, 200, 250)'
    GREY_COLOR = 'rgb(240, 240, 240)'

    def __init__(self, *args):
        super().__init__(*args)
        self.setCheckable(True)
        self.__pressed = False

    def is_pressed(self):
        return self.__pressed

    def change_state(self):
        try:
            if self.is_pressed():
                # если кнопка нажата
                self.setChecked(False)
                self.set_style(False)
                self.__pressed = False
            else:
                self.setChecked(True)
                self.set_style(True)
                self.__pressed = True
        except Exception:
            print(Exception)

    def set_style(self, is_pressed: bool):
        pass


class ConnectButton(MyButton):
    """ Класс кнопки подключения к устройству"""

    def __init__(self, *args):
        super().__init__(*args)
        self.__ied_is_connected = False

    # НАЖАТИЕ НА КНОПКУ
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        # print(f'\n\tmousePressEvent {self} \n')
        # self.change_state()
        if self.is_pressed() and self.__ied_is_connected:
            # если кнопка нажата
            self.setChecked(False)
            self.set_style(False)
            self.__pressed = False
        else:
            self.setChecked(True)
            self.set_style(True)
            self.__pressed = True

    def set_style(self, is_pressed=False):
        """Меняет внешний вид и текст кнопки подключения"""
        if is_pressed:
            self.setStyleSheet(f'background: {DOButton.GREEN_COLOR}')
            # self.setIcon(QIcon(app_service.resource_path('static/images/connect.svg')))
            self.setText('ОТКЛЮЧИТЬ')
        else:
            self.setStyleSheet(f'background: {DOButton.RED_COLOR}')
            # self.setIcon(QIcon(app_service.resource_path('static/images/disconnect.svg')))
            self.setText('ПОДКЛЮЧИТЬ')
        self.setIconSize(QSize(50, 50))


class DOControl(QPushButton):

    def set_do_control(self, val: bool):
        DOButton.DO_CONTROL = val

    def is_do_control(self):
        return DOButton.DO_CONTROL


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
            print(DOButton.DO_CONTROL)

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

    def set_style(self, state):
        if state == 'default':
            self.setStyleSheet(f'background: {DI0Button.BLUE_COLOR}')
            self.setFont(QFont('MS Shell Dlg 2', 9, QFont.Normal))
        else:
            if state == 'triggered':
                self.setStyleSheet(f'background: {DI0Button.GREEN_COLOR}')
            elif state == 'pressed':
                self.setStyleSheet(f'background: {DI0Button.BLUE_COLOR}')
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

    def set_style(self, state):
        super().set_style(state)
        if state == 'controlled':
            self.setStyleSheet(f'background: {DOButton.RED_COLOR}')
