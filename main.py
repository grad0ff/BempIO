# pyuic5 BempIO.ui -o BempIO.py

import functools
import logging
import os
import sys
import threading
import time
import pygame
import serial.tools.list_ports

from BempIO import Ui_MainWindow
from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize, QTimer
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QMessageBox
from pymodbus.client.sync import ModbusSerialClient
from pymodbus.exceptions import ConnectionException
from my_classes import DI0_Button


#  ДЕКОРАТОР ПРОВЕРКИ ВРЕМЕНИ ВЫПОЛНЕНИЯ ФУНКЦИИ
def time_check(func):
    @functools.wraps(func)
    def wrapper(*args):
        t1 = time.time()
        func(*args)
        t2 = time.time()
        print(func.__name__, t2 - t1)

    return wrapper


# ДЕТАЛИЗАЦИЯ ИСКЛЮЧЕНИЙ
def catch_exception():
    log = logging.getLogger()
    log.exception('\n\t НОВОЕ ИСКЛЮЧЕНИЕ: \n')


# ВЫВОД ОКНА С СООБЩЕНИЕМ
def show_msg(msg=f"Непредвиденная ошибка!\n{sys.exc_info()}", msg_type="trouble"):
    msg_window = QMessageBox()
    window_icon = QIcon(resource_path('static/images/critical.ico'))
    msg_icon = QMessageBox.Critical
    if msg_type == 'inform':
        msg_icon = QMessageBox.Information
        window_icon = QIcon(resource_path('static/images/information.ico'))
    elif msg_type == 'error':
        window_icon = QIcon(resource_path('static/images/warning.ico'))
        msg_icon = QMessageBox.Warning
    msg_window.setWindowTitle(msg_type + "!")
    msg_window.setWindowIcon(window_icon)
    msg_window.setIcon(msg_icon)
    msg_window.setText(msg)
    msg_window.exec_()


# ОТОБРАЖЕНИЕ АКТУАЛЬНОГО КОЛИЧЕСТВА DI И DO
def show_ied_dio(group_dio, max_dio):
    dio_buttons_list = []
    for dio in group_dio.findChildren(QtWidgets.QPushButton):
        dio_buttons_list.append(dio)
    dio_buttons_list.sort(key=lambda x: int(x.text()))
    for dio in dio_buttons_list[max_dio:96]:
        dio.setVisible(False)
    return dio_buttons_list[:max_dio]


# ОПРЕДЕЛЕНИЕ ПУТИ ДЛЯ ФАЙЛОВ, ДОБАВЛЯЕМЫХ В *.exe
def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle('BempIO')
        self.setWindowIcon(QIcon(resource_path('static/images/BempIO.ico')))
        self.setFixedSize(760, 960)
        self.searh_port = self.ui.pushButton_searh_ports
        self.searh_port.setIcon(QIcon(resource_path('static/images/find.svg')))
        self.searh_port.setIconSize(QSize(15, 15))
        self.msg = QMessageBox()

        # инициализация параметров DI и DO устройства
        self.ui.comboBox_ied_type.addItems(['БЭМП [РУ]'])
        self.select_ied()

        # инициализация параметров подключения
        self.find_ports()
        self.ui.comboBox_speed.addItems(['2400', '4800', '9600', '19200', '38400', '56000', '57600', '115200'])
        self.ui.comboBox_speed.setCurrentIndex(4)
        self.ui.comboBox_parity.addItems(['N', 'E', 'O'])
        self.ui.comboBox_stopbits.addItems(['1', '2'])
        self.ui.spinBox_ied_address.setMinimum(1)
        self.ui.spinBox_ied_address.setMaximum(247)
        self.ui.pushButton_disconnect.setStyleSheet('background: rgb(255,85,70)')
        self.ui.pushButton_connect.setFocus()
        self.ui.comboBox_voice_type.addItems(['Дарья', '2', '3', '4'])
        self.polling_time = 0.25
        self.max_di = 1
        self.max_do = 1
        self.enabled_di_list = set()
        self.enabled_do_list = set()
        self.unit = 0x01

        # обработка событий
        self.ui.pushButton_searh_ports.clicked.connect(self.find_ports)
        self.ui.pushButton_connect.clicked.connect(self.connecting)
        self.ui.pushButton_disconnect.clicked.connect(self.disconnecting)
        self.ui.comboBox_ied_type.activated.connect(self.select_ied)

        # тип голоса при запуске
        self.voice_type = self.ui.comboBox_voice_type.currentText()

        # тест фичи

    # ТЕСТИРОВАНИЕ ФИЧЕЙ
    def _testing(self):
        pass

    # ВЫБОР УСТРОЙСТВА ИЗ ВЫПАДАЮЩЕГО СПИСКА
    def select_ied(self):
        self.ied_type = self.ui.comboBox_ied_type.currentText()
        msg = f"Выбрано устройство: {self.ied_type}"
        self.send_msg(msg)
        self.ui.lineEdit_di_01_address.setDisabled(True)
        self.ui.lineEdit_do_01_address.setDisabled(True)
        self.ui.spinBox_di_count.setDisabled(True)
        self.ui.spinBox_do_count.setDisabled(True)
        if self.ied_type == 'БЭМП [РУ]':
            self.ui.lineEdit_di_01_address.setText('0x0500')
            self.ui.lineEdit_do_01_address.setText('0x0700')
        elif self.ied_type == 'Прочее':
            self.ui.lineEdit_di_01_address.setText('0x')
            self.ui.lineEdit_di_01_address.setEnabled(True)
            self.ui.spinBox_di_count.setMinimum(1)
            self.ui.spinBox_di_count.setMaximum(96)
            self.ui.spinBox_di_count.setEnabled(True)
            self.ui.lineEdit_do_01_address.setText('0x')
            self.ui.lineEdit_do_01_address.setEnabled(True)
            self.ui.spinBox_do_count.setMinimum(1)
            self.ui.spinBox_do_count.setMaximum(96)
            self.ui.spinBox_do_count.setEnabled(True)
        self.ui.spinBox_di_count.setValue(96)
        self.ui.spinBox_do_count.setValue(96)

    # ПОИСК COM-ПОРТОВ
    def find_ports(self):
        msg = "Поиск COM-портов..."
        self.send_msg(msg)
        self.ui.comboBox_com_port.clear()
        try:
            port_list = serial.tools.list_ports.comports()
        except Exception:
            catch_exception()
            msg = "Ошибка поиска COM-порта"
            show_msg(msg, 'error')
        else:
            ports = sorted(list(map(lambda x: x.name, port_list)))
            self.ui.comboBox_com_port.addItems(ports)
            msg = f"Поиск завершен. Найдено COM-портов:  {len(ports)}"
        finally:
            self.send_msg(msg)

    # ПОДКЛЮЧЕНИЕ К УСТРОЙСТВУ
    def connecting(self):
        msg = "Проверка связи с устройством..."
        self.send_msg(msg)
        port = self.ui.comboBox_com_port.currentText()
        try:
            self.client = ModbusSerialClient(
                method='ASCII',
                port=port,
                baudrate=int(self.ui.comboBox_speed.currentText()),
                bytesize=8,
                parity=self.ui.comboBox_parity.currentText(),
                stopbits=int(self.ui.comboBox_stopbits.currentText()),
            )
        except Exception:
            catch_exception()
            show_msg()
        else:
            try:
                assert self.client.connect()
                assert self.client.is_socket_open()
            except AssertionError:
                msg = 'Неправильные параметры подключения или COM-порт занят!'
                show_msg(msg, 'error')
            except Exception:
                catch_exception()
                show_msg()
            else:
                msg = f"Связь установлена!"
                self.send_msg(msg)
                self.check_ied_params()  # проверка параметров устройства
                self.show_dio_buttons()  # отображение актуального числа di и do
                self.change_btns_style(True)  # активация/деактивация кнопок управления
                self.run_threads()
                pygame.init()  # инициализация медиапроигрывателя
                msg = f"Устройство {self.ied_type} подключено!"
                self.send_msg(msg)

    # ПРОВЕРКА ПАРАМЕТРОВ ПОДКЛЮЧЕННОГО УСТРОЙСТВА
    def check_ied_params(self):
        msg = f"Проверка параметров устройства {self.ied_type}..."
        self.send_msg(msg)
        try:
            # определение количества DI и DO в подключенном устройстве
            if self.ied_type == 'БЭМП [РУ]':
                self.max_di = self.client.read_holding_registers(0x0100, 1, unit=self.unit).registers[0]
                self.max_do = self.client.read_holding_registers(0x0101, 1, unit=self.unit).registers[0]
                assert isinstance(self.max_di, int), 'Неправильный адрес DI 1 БЭМП [РУ]'
                assert isinstance(self.max_do, int), 'Неправильный адрес DO 1 БЭМП [РУ]'
            elif self.ied_type == 'Прочее':
                self.max_di = int(self.ui.spinBox_di_count.text())
                self.max_do = int(self.ui.spinBox_di_count.text())
            self.ui.spinBox_di_count.setValue(self.max_di)
            self.ui.spinBox_do_count.setValue(self.max_do)
            msg = f"Количество DI - {self.max_di}\nКоличество DO - {self.max_do}"
            di_01_address = self.ui.lineEdit_di_01_address.text()
            do_01_address = self.ui.lineEdit_do_01_address.text()
            # assert isinstance(int(di_01_address, 16), int), "Неправильный адрес DI 1"
            # assert isinstance(int(do_01_address, 16), int), "Неправильный адрес DO 1 "
            self.di_address = int(di_01_address, 16)
            self.do_address = int(do_01_address, 16)
        # except AssertionError:
        #     msg = "Некорректные параметры DI и DO"
        #     print(msg)
        #     show_msg(msg, 'error')
        except Exception:
            catch_exception()
            self.client.close()
            show_msg()
        finally:
            self.send_msg(msg)

    # ОТОБРАЖЕНИЕ АКТУАЛЬНОГО ЧИСЛА DI И DO
    def show_dio_buttons(self):
        self.di_list = show_ied_dio(self.ui.groupBox_di, self.max_di)
        self.do_list = show_ied_dio(self.ui.groupBox_do, self.max_do)

    # ИНИЦИАЛИЗАЦИЯ ПОТОКА ОПРОСА  DI и DO
    def run_threads(self):
        self.th_check_dio = threading.Thread(target=self.check_dio, name='th_check_dio')
        self.th_check_dio.run_flag = True
        try:
            self.th_check_dio.start()
        except Exception:
            catch_exception()
            show_msg()
        else:
            msg = "Запущен опрос DI и DO"
            self.send_msg(msg)

    # ИЗМЕНЕНИЕ ВИДА КНОПОК НАСТРОЕК ПРИ ПОДКЛЮЧЕНИИ/ОТКЛЮЧЕНИИ
    def change_btns_style(self, value):
        self.ui.groupBox_dio_settings.setDisabled(value)
        self.ui.groupBox_connect_settings.setDisabled(value)
        self.ui.groupBox_dio_voicing.setEnabled(value)
        self.ui.pushButton_connect.setDisabled(value)
        self.ui.pushButton_disconnect.setEnabled(value)
        self.ui.groupBox_di.setEnabled(value)
        self.ui.groupBox_do.setEnabled(value)
        # self.ui.groupBox_voice_type.setEnabled(value)
        if value:
            self.ui.pushButton_connect.setStyleSheet('background: rgb(100,250,50)')
            self.ui.pushButton_connect.setText('Подключено')
            self.ui.pushButton_disconnect.setStyleSheet('background: #f0f0f0')
            self.ui.pushButton_disconnect.setText('Отключить')
        else:
            self.ui.pushButton_connect.setStyleSheet('background: #f0f0f0')
            self.ui.pushButton_connect.setText('Подключить')
            self.ui.pushButton_disconnect.setStyleSheet('background: rgb(255,85,70)')
            self.ui.pushButton_disconnect.setText('Отключено')

    # ОТКЛЮЧЕНИЕ ОТ УСТРОЙСТВА
    def disconnecting(self):
        self.ui.radioButton_voicing_off.setChecked(True)
        try:
            if self.th_check_dio.is_alive():
                self.th_check_dio.run_flag = False
            while self.th_check_dio.is_alive():
                pass
        except AttributeError:
            pass
        except Exception as e:
            catch_exception()
            show_msg()
        else:
            self.client.close()
            self.select_ied()
            self.change_btns_style(False)
            self.unselect_dio(self.ui.groupBox_di)
            self.unselect_dio(self.ui.groupBox_do)
            pygame.quit()
            msg = f"Устройство {self.ied_type} отключено!"
            self.send_msg(msg)

    # ОТОБРАЖЕНИЕ РАНЕЕ СКРЫТЫХ DI и DO
    def unselect_dio(self, group_dio):
        for dio in group_dio.findChildren(QtWidgets.QPushButton):
            dio.setChecked(False)
            dio.setVisible(True)
            dio.setStyleSheet('background: #f0f0f0')
            dio.setFont(QFont('MS Shell Dlg 2', 9, QFont.Normal))

    # ОПРОС DI и DO
    def check_dio(self):
        i = 0
        while getattr(self.th_check_dio, 'run_flag', True):
            time.sleep(self.polling_time)
            self.checking_dio(self.di_address, self.max_di, self.di_list)
            self.checking_dio(self.do_address, self.max_do, self.do_list)

    # ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ОПРОСА DI и DO
    def checking_dio(self, dio_address, max_dio, dio_buttons_list):
        try:
            dio_list_request = self.client.read_coils(dio_address, max_dio, unit=self.unit).bits  # считывание регистров
        except (AttributeError, ConnectionException):
            QTimer.singleShot(0, self.ui.pushButton_disconnect.click)
            sys.exit()
        except Exception:
            catch_exception()
            show_msg()
        else:
            try:
                for i in range(max_dio):  # для отображаемого кол-ва DIO
                    dio_button = dio_buttons_list[i]
                    dio_button.set_btn_num(i + 1)  # № отдельного DIO

                    # изменение статуса DIO
                    if dio_list_request[i]:  # если DIO сработал
                        dio_button.setTriggered(True)
                    else:  # если DIO отключился
                        dio_button.setTriggered(False)
                    self.voice_over_preparing(dio_button)  # подготовка к озвучиванию DIO

                    # возможность нажатия кнопок определенного типа, если включено озвучивание
                    if (self.ui.radioButton_di_voicing.isChecked() and dio_button.TYPE == 'DI') or \
                            (self.ui.radioButton_do_voicing.isChecked() and dio_button.TYPE == 'DO') or \
                            (self.ui.radioButton_dio_voicing.isChecked()):  # если озвучивание DIO включено
                        dio_button.setCheckable(True)  # возможность выбора DIO для озвучиванию нажатием кнопки
                    else:
                        dio_button.setCheckable(False)
                        dio_button.setChecked(False)
                        DI0_Button.BUTTONS_IS_PRESSED = False
                    self.voice_over_preparing(dio_button)  # подготовка к озвучиванию DIO
            except Exception:
                catch_exception()
                show_msg()

    # ПОДГОТОВКА К ОЗВУЧИВАНИЮ DI И DO
    def voice_over_preparing(self, dio_button):
        try:
            if dio_button.isTriggered():
                if dio_button.num not in dio_button.TRIGGERED_LIST and not self.ui.radioButton_voicing_off.isChecked():  # если DIO не
                    # в списке сработавших и включено озвучивание DIO
                    if dio_button.isChecked() or dio_button.BUTTONS_IS_PRESSED == False:  # если хоть одна кнопка нажата,
                        # то озвучивается только соответствующий DIO
                        self.voicing_dio(dio_button)
                dio_button.TRIGGERED_LIST.add(dio_button.num)  # DIO добавляется в список сработавших
            else:  # если DIO отключился
                if dio_button.num in dio_button.TRIGGERED_LIST:  # если DIO находится в списке сработавших
                    dio_button.TRIGGERED_LIST.remove(dio_button.num)  # DIO удаляется из списка сработавших
                    if not self.ui.radioButton_voicing_off.isChecked():  # если включено озвучивание DIO
                        if dio_button.isChecked() or dio_button.BUTTONS_IS_PRESSED == False:  # если хоть одна кнопка нажата,
                            # то озвучивается только соответствующий DIO
                            self.voicing_dio(dio_button)
                time.sleep(0.005)
        except Exception:
            catch_exception()
            show_msg()

    # enabled_dio_list = None
    # dio_type = None
    # if isinstance(dio_button, DI_Button):
    #     dio_type = 'DI'
    #     enabled_dio_list = self.enabled_di_list
    # elif isinstance(dio_button, DO_Button):
    #     dio_type = 'DO'
    #     enabled_dio_list = self.enabled_do_list

    # if dio_button.isChecked() or not dio_button.BUTTONS_IS_PRESSED:  # если кнопка нажата или нажатых кнопок нет,
    #     # то озвучивается либо выбранный DIO, либо все
    #     if dio_button.isTriggered():  # если DIO сработал
    #         if dio_button.num not in dio_button.TRIGGERED_LIST and not self.ui.radioButton_voicing_off.isChecked():  # если DIO не находится в списке сработавших
    #             self.voicing_dio(dio_button)
    #     # else:  # если DIO находитсяв списке сработавших
    #     #     if not dio_button.isTriggered():  # если DIO отключился
    #     #         dio_button.TRIGGERED_LIST.remove(dio_button.num)  # DIO удаляется из списка
    #     #         self.voicing_dio(dio_button)
    #     dio_button.TRIGGERED_LIST.add(dio_button.num)  # DIO добавляется в список сработавших
    #     time.sleep(0.005)
    #     # time.sleep(1)
    # print(dio_button.TRIGGERED_LIST)

    # ОЗВУЧИВАНИЕ DI И DO
    def voicing_dio(self, dio_button):
        print('voicing_dio')
        if (self.ui.radioButton_di_voicing.isChecked() and dio_button.TYPE == 'DI') or \
                (self.ui.radioButton_do_voicing.isChecked() and dio_button.TYPE == 'DO') or \
                self.ui.radioButton_dio_voicing.isChecked():
            try:
                song_dio_type = pygame.mixer.Sound(
                    resource_path(f'static/voicing/{self.voice_type}/{dio_button.TYPE}/{dio_button.num}.wav'))
                song_time = song_dio_type.get_length() - 0.275
                song_dio_type.play()
                time.sleep(song_time)
                if not dio_button.isTriggered():
                    song_dio_state = pygame.mixer.Sound(
                        resource_path(f'static/voicing/{self.voice_type}/on-off/отключено.wav'))
                    song_time = song_dio_state.get_length() - 0.1
                    song_dio_state.play()
                    time.sleep(song_time)
            except Exception:
                catch_exception()
                show_msg()

    # ЗАВЕРШЕНИЕ РАБОТЫ ПРОГРАММЫ
    def closeEvent(self, event):
        self.disconnecting()
        event.accept()

    def send_msg(self, msg):
        self.statusBar().showMessage(msg)
        print(msg)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyle('Fusion')
    application = MyWindow()
    application.show()
    sys.exit(app.exec())
