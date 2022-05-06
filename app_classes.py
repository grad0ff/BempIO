from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QFont, QIcon
from PyQt5 import QtGui

import app_logger

log = app_logger.get_app_logger(__name__)


class MyButton(QPushButton):
    RED_COLOR = 'rgb(255, 100, 100)'
    GREEN_COLOR = 'rgb(50, 255, 50)'
    BLUE_COLOR = 'rgb(150, 200, 250)'
    GREY_COLOR = 'rgb(250, 250, 250)'

    def __init__(self, *args):
        super().__init__(*args)
        # self.setCheckable(True)
        self._checked = False
        self._checkable = True

    def mousePressEvent(self, event) -> None:
        """ Меняет состояние кнопки при нажатии """
        super().mousePressEvent(event)
        try:
            if self.isCheckable():
                if not self.isChecked():
                    self.setChecked(True)
                else:
                    self.setChecked(False)
                print(self.isChecked())
        except Exception as e:
            log.exception(e)

    def isCheckable(self) -> bool:
        return self._checkable

    def setCheckable(self, a0: bool) -> None:
        self._checked = a0

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, a0: bool) -> None:
        self._checked = a0

    def change_style(self, *args) -> None:
        """ Меняет внешний вид и текст кнопки """
        pass


class ConnectButton(MyButton):
    """ Класс кнопки подключения к устройству"""
    CONNECT_TEXT = 'ПОДКЛЮЧИТЬ'
    DISCONNECT_TEXT = 'ОТКЛЮЧИТЬ'

    # def __init__(self, *args):
    #     super().__init__(*args)
    #
    # def mousePressEvent(self, event) -> None:
    #     super().mousePressEvent(event)

    def change_style(self):
        """ Меняет внешний вид и текст кнопки подключения"""
        if self.isChecked():
            self.setStyleSheet(f'background: {DOButton.GREEN_COLOR}')
            # self.setIcon(QIcon(app_service.resource_path('static/images/connect.svg')))
            self.setText(self.__class__.DISCONNECT_TEXT)
        else:
            self.setStyleSheet(f'background: {DOButton.RED_COLOR}')
            # self.setIcon(QIcon(app_service.resource_path('static/images/disconnect.svg')))
            self.setText(self.__class__.CONNECT_TEXT)
        self.setIconSize(QSize(50, 50))


class DOControl(QPushButton):

    def set_do_control(self, val: bool):
        DOButton.DO_CONTROL = val

    def is_do_control(self):
        return DOButton.DO_CONTROL


class DI0Button(MyButton):
    _VOICING_FLAG = False

    # _CLICKABLE_FLAG = False

    def __init__(self, *args):
        super().__init__(*args)
        self.setCheckable(False)
        self._trigger_state = False
        self.state_is_changed = False
        self.number = 0

    @property
    def triggered(self) -> bool:
        return self._trigger_state

    @triggered.setter
    def triggered(self, flg) -> None:
        if self._trigger_state != flg:
            self._trigger_state = flg
            self.state_is_changed = True
        else:
            self.state_is_changed = False

    # # ВЫСТАВЛЕНИЕ КЛИКАБЕЛЬНОСТИ DI ИЛИ DO
    # def setCheckable(self, val: bool):
    #     super().setCheckable(val)
    #     self.__class__._CLICKABLE_FLAG = val
    #
    # def is_clickable(self):
    #     return self.__class__._CLICKABLE_FLAG

    # def set_triggered(self, val: bool):
    #     self.press()

    # def trigger_state(self):
    #     return self._trigger_state

    def change_style(self, state):
        if self.isChecked():
            self.setStyleSheet(f'background: {DI0Button.BLUE_COLOR}')
        if state:
            self.setStyleSheet(f'background: {DI0Button.GREEN_COLOR}')
            self.setFont(QFont('MS Shell Dlg 2', 10, QFont.Bold))
        else:
            self.setStyleSheet(f'background: {DI0Button.GREY_COLOR}')
            self.setFont(QFont('MS Shell Dlg 2', 9, QFont.Normal))

    def get_triggered_list(self):
        return self.__class__._TRIGGERED_LIST

    def add_to_triggered_dio_list(self, element):
        self.__class__._TRIGGERED_LIST.add(element)

    def del_from_triggered_dio_list(self, element):
        self.__class__._TRIGGERED_LIST.remove(element)

    def get_pressed_flag(self):
        return self.__class__._PRESSED_FLAG

    def press_flag(self, val: bool):
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
