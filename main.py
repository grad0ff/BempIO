# pyuic5 BempIO_v2.ui -o BempIO_v2.py
"-*- coding: utf-8 -*-"""

import locale
import functools
import logging
import os
import sys
import threading
import time
import pygame
import serial.tools.list_ports

from BempIO_v2 import Ui_MainWindow
from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize, QTimer
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QMessageBox
from pymodbus.client.sync import ModbusSerialClient
from pymodbus.exceptions import ConnectionException
from my_classes import *

locale.setlocale(locale.LC_ALL, 'ru-RU')


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
    log.exception(f'\n\t НОВОЕ ИСКЛЮЧЕНИЕ: {sys.exc_info()}\n')


# ВЫВОД ОКНА С СООБЩЕНИЕМ
def show_msg(msg=f"Непредвиденная ошибка!\n{sys.exc_info()}", msg_type="Проблема"):
    msg_window = QMessageBox()
    window_icon = QIcon(resource_path('static/images/critical.ico'))
    msg_icon = QMessageBox.Critical
    if msg_type == 'Информация':
        msg_icon = QMessageBox.Information
        window_icon = QIcon(resource_path('static/images/information.ico'))
    elif msg_type == 'Ошибка':
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
        self.setFixedSize(760, 760)
        self.searh_port = self.ui.pushButton_searh_ports
        self.searh_port.setIcon(QIcon(resource_path('static/images/find.svg')))
        self.searh_port.setIconSize(QSize(15, 15))

        self.msg = QMessageBox()

        # инициализация параметров DI и DO устройства
        self.ui.tabWidget.setTabText(1, 'Параметры устройства')

        self.ui.comboBox_ied_type.addItems(['БЭМП'])
        self.select_ied()

        # инициализация параметров подключения
        self.ui.tabWidget.setTabText(0, 'Параметры подключения')
        self.find_ports()
        self.ui.comboBox_speed.addItems(['2400', '4800', '9600', '19200', '38400', '56000', '57600', '115200'])
        self.ui.comboBox_speed.setCurrentIndex(4)
        self.ui.comboBox_parity.addItems(['N', 'E', 'O'])
        self.ui.comboBox_stopbits.addItems(['1', '2'])
        self.ui.spinBox_ied_address.setMinimum(1)
        self.ui.spinBox_ied_address.setMaximum(247)
        self.ui.pushButton_connect.setStyleSheet('background: rgb(255,85,70)')

        self.ui.pushButton_connect.setFocus()
        self.ui.comboBox_voice_type.addItems(['Дарья', '2', '3', '4'])
        self.polling_time = 0
        self.max_di = 1
        self.max_do = 1
        self.unit = 0x01

        self.ui.tabWidget.setTabText(2, 'Дополнителльные функции')

        # обработка событий
        self.ui.pushButton_searh_ports.clicked.connect(self.find_ports)
        self.ui.pushButton_connect.clicked.connect(self.check_connect)
        self.ui.comboBox_ied_type.activated.connect(self.select_ied)
        self.ui.pushButton_do_control.clicked.connect(self.control_do)

        # тип голоса при запуске
        self.voice_type = self.ui.comboBox_voice_type.currentText()

        # тест фичи
        self.ui.pushButton_do_control.clicked.connect(self.do_control)

    def do_control(self):
        if self.ui.pushButton_do_control.text() == '':
            DOButton.DO_CONTROL = True
        else:
            DOButton.DO_CONTROL = True

    # ТЕСТИРОВАНИЕ ФИЧЕЙ
    def _testing(self):
        try:
            print(DIButton._PRESSED_FLAG)
        except Exception:
            catch_exception()

    # ВЫБОР УСТРОЙСТВА ИЗ ВЫПАДАЮЩЕГО СПИСКА
    def select_ied(self):
        self.ied_type = self.ui.comboBox_ied_type.currentText()
        msg = f"Выбрано устройство: {self.ied_type}"
        self.send_msg(msg)
        self.ui.lineEdit_di_01_address.setDisabled(True)
        self.ui.lineEdit_do_01_address.setDisabled(True)
        self.ui.spinBox_di_count.setDisabled(True)
        self.ui.spinBox_do_count.setDisabled(True)
        if self.ied_type == 'БЭМП':
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
            msg = "Ошибка поиска COM-порта!"
            show_msg(msg, 'Ошибка')
        else:
            ports = sorted(list(map(lambda x: x.name, port_list)))
            self.ui.comboBox_com_port.addItems(ports)
            msg = f"Поиск завершен. Найдено COM-портов:  {len(ports)}"
        finally:
            self.send_msg(msg)

    # ПОДКЛЮЧЕНИЕ К УСТРОЙСТВУ
    def check_connect(self, *args):
        if self.ui.pushButton_connect.text() == "ПОДКЛЮЧИТЬ" or self.ui.pushButton_connect.isChecked():
            self.connecting()
        else:
            self.disconnecting()

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
            msg = "Ошибка проверки связи с устройством!"
            show_msg(msg, 'Ошибка')
        else:
            try:
                assert self.client.connect()
                assert self.client.is_socket_open()
            except AssertionError:
                msg = 'Неправильные параметры подключения или COM-порт занят!'
                self.send_msg(msg)
                show_msg(msg, 'Ошибка')
            except Exception:
                catch_exception()
                show_msg()
            else:
                try:
                    msg = f"Связь c {self.ied_type} установлена!"
                    self.send_msg(msg)
                    self.check_ied_params()  # проверка параметров устройства
                    self.show_dio_buttons()  # отображение актуального числа di и do
                    self.change_buttons_style(True)  # активация/деактивация кнопок управления
                    self.run_threads()
                    pygame.init()  # инициализация медиапроигрывателя
                    msg = f"Устройство {self.ied_type} подключено!"
                    self.send_msg(msg)
                except:
                    catch_exception()

    # ПРОВЕРКА ПАРАМЕТРОВ ПОДКЛЮЧЕННОГО УСТРОЙСТВА
    def check_ied_params(self):
        msg = f"Проверка параметров устройства {self.ied_type}..."
        self.send_msg(msg)
        self.check_max_dio()
        self.check_dio_01_address()

    # ОПРЕДЕЛЕНИЕ КОЛИЧЕСТВА DI И DO В ПОДКЛЮЧЕННОМ УСТРОЙСТВЕ
    def check_max_dio(self):
        try:
            if self.ied_type == 'БЭМП':
                try:
                    self.max_di = self.client.read_holding_registers(0x0100, 1, unit=self.unit).registers[0]
                    self.max_do = self.client.read_holding_registers(0x0101, 1, unit=self.unit).registers[0]
                except Exception:
                    catch_exception()
                    msg = "Ошибка чтения количества DI и DO"
                    show_msg(msg, 'Ошибка')
            elif self.ied_type == 'Прочее':
                self.max_di = int(self.ui.spinBox_di_count.text())
                self.max_do = int(self.ui.spinBox_di_count.text())
            assert isinstance(self.max_di, int), 'Неправильный адрес DI 1'
            assert isinstance(self.max_do, int), 'Неправильный адрес DO 1'
        except AssertionError:
            msg = "Некорректные параметры DI и DO."
            show_msg(msg, 'Ошибка')
            self.send_msg(msg)
        except Exception:
            catch_exception()
            self.client.close()
            show_msg()
        else:
            self.ui.spinBox_di_count.setValue(self.max_di)
            self.ui.spinBox_do_count.setValue(self.max_do)
            msg = f"Количество DI - {self.max_di}\nКоличество DO - {self.max_do}"
            self.send_msg(msg)

    # ОПРЕДЕЛЕНИЕ АДРЕСА DI_1 И DO_1 В ПОДКЛЮЧЕННОМ УСТРОЙСТВЕ
    def check_dio_01_address(self):
        di_01_address = self.ui.lineEdit_di_01_address.text()
        do_01_address = self.ui.lineEdit_do_01_address.text()
        try:
            assert isinstance(int(di_01_address, 16), int), "Неправильный адрес DI 1"
            assert isinstance(int(do_01_address, 16), int), "Неправильный адрес DO 1 "
        except AssertionError:
            msg = "Некорректные параметры DI и DO"
            self.send_msg(msg)
            show_msg(msg, 'Ошибка')
        except Exception:
            catch_exception()
            self.client.close()
            show_msg()
        else:
            msg = f"Адрес DI 1 - {di_01_address}\nАдрес DO 1 - {do_01_address}"
            self.send_msg(msg)
            self.di_start_address = int(di_01_address, 16)
            self.do_start_address = int(do_01_address, 16)

    # ОТОБРАЖЕНИЕ АКТУАЛЬНОГО ЧИСЛА DI И DO
    def show_dio_buttons(self):
        self.di_list = show_ied_dio(self.ui.groupBox_di, self.max_di)
        self.do_list = show_ied_dio(self.ui.groupBox_do, self.max_do)

    # ИНИЦИАЛИЗАЦИЯ ПОТОКА ОПРОСА  DI и DO
    def run_threads(self):
        self.th_polling_dio = threading.Thread(target=self.polling_dio, name='th_polling_dio')
        self.th_polling_dio.run_flag = True
        try:
            self.th_polling_dio.start()
        except Exception:
            catch_exception()
            msg = "Ошибка запуска опроса DI и DO"
            self.send_msg(msg)
            show_msg()
        else:
            msg = "Запущен опрос DI и DO."
            self.send_msg(msg)

    # ИЗМЕНЕНИЕ ВИДА КНОПОК НАСТРОЕК ПРИ ПОДКЛЮЧЕНИИ/ОТКЛЮЧЕНИИ
    def change_buttons_style(self, a0: bool):
        self.ui.tab2_dio_settings.setDisabled(a0)
        self.ui.tab1_connect_settings.setDisabled(a0)
        self.ui.groupBox_voicing_settings.setEnabled(a0)
        self.ui.groupBox_do_control.setEnabled(a0)
        self.ui.groupBox_di.setEnabled(a0)
        self.ui.groupBox_do.setEnabled(a0)
        self.ui.pushButton_connect.change_style(a0)
        self.ui.pushButton_do_control.setEnabled(a0)
        self.ui.comboBox_voice_type.setEnabled(False)

    # ОТКЛЮЧЕНИЕ ОТ УСТРОЙСТВА
    def disconnecting(self):
        msg = "Отключение от устройства..."
        self.send_msg(msg)
        self.ui.radioButton_voicing_off.setChecked(True)
        try:
            if self.th_polling_dio.is_alive():
                self.th_polling_dio.run_flag = False
            while self.th_polling_dio.is_alive():
                pass
        except AttributeError:
            pass
        except Exception:
            catch_exception()
            msg = "Ошибка отключения от устройства"
            show_msg(msg, 'Ошибка')
        else:
            self.client.close()
            msg = f"Устройство {self.ied_type} отключено!"
            self.send_msg(msg)
            self.select_ied()
            self.change_buttons_style(False)
            self.unselect_dio(self.ui.groupBox_di)
            self.unselect_dio(self.ui.groupBox_do)
            pygame.quit()

    # ОТОБРАЖЕНИЕ РАНЕЕ СКРЫТЫХ DI и DO
    def unselect_dio(self, group_dio):
        for dio in group_dio.findChildren(QtWidgets.QPushButton):
            dio.setChecked(False)
            dio.setVisible(True)
            dio.setStyleSheet('background: #f0f0f0')
            dio.setFont(QFont('MS Shell Dlg 2', 9, QFont.Normal))

    # ОПРОС DI и DO
    def polling_dio(self):
        while getattr(self.th_polling_dio, 'run_flag', True):
            time.sleep(self.polling_time)
            self.processing(self.di_start_address, self.max_di, self.di_list)
            self.processing(self.do_start_address, self.max_do, self.do_list)

    # ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ОПРОСА DI и DO
    def processing(self, dio_address, max_dio, dio_buttons_list):
        dio_list = self.get_request(dio_address, max_dio)  # получить список DI или DO
        try:
            for i in range(max_dio):  # для отображаемого кол-ва DI или DO
                dio_button = dio_buttons_list[i]
                dio_button.set_button_num(i + 1)  # задает № отдельного DI или DO
                # изменение статуса DIO
                if dio_list[i]:  # если DIO сработал
                    dio_button.set_triggered(True)
                else:  # если DIO отключился
                    dio_button.set_triggered(False)
                self.check_clickable(
                    dio_button)  # сделать кнопки DI и(или) DO кликабельными, если включено их озвучивание
                self.check_style(dio_button)
                self.voice_over_preparing(dio_button)  # подготовка к озвучиванию DIO
                if dio_button.is_triggered():
                    dio_button.add_to_triggered_dio_list(dio_button.num)
                elif dio_button.num in dio_button.get_triggered_list():
                    dio_button.del_from_triggered_dio_list(dio_button.num)
                time.sleep(0.01)
        except Exception:
            catch_exception()

    # ОТПРАВКА ЗАПРОСА В УСТРОЙСТВО
    def get_request(self, dio_address, max_dio):
        try:
            dio_list = self.client.read_coils(dio_address, max_dio, unit=self.unit).bits  # считывание регистров
        except (AttributeError, ConnectionException):
            # QTimer.singleShot(0, self.ui.pushButton_connect.click)
            sys.exit()
        except Exception:
            catch_exception()
            msg = "Ошибка опроса DI и DO"
            show_msg(msg, 'Ошибка')
        else:
            return dio_list

    # ВОЗМОЖНОСТЬ НАЖАТИЯ КНОПОК DI ИЛИ DO, ЕСЛИ ВКЛЮЧЕНО ОЗВУЧИВАНИЕ
    def check_clickable(self, dio_button):
        # возможность нажатия кнопок DI и(или) DO, если включено озвучивание
        if (isinstance(dio_button, DIButton) and self.ui.radioButton_di_voicing.isChecked()) or \
                (isinstance(dio_button, DOButton) and (self.ui.radioButton_do_voicing.isChecked() or
                                                       DOButton.DO_CONTROL)) or (
        self.ui.radioButton_dio_voicing.isChecked()):  # если озвучивание DI и(или) DO включено
            dio_button.setCheckable(True)  # делает кнопку DI и(или) DO кликабельной
        # dio_button.set_voicing_flag(True)
        else:
            dio_button.setChecked(False)  # сбрасывает нажатую кнопку
            dio_button.setCheckable(False)  # делает кнопку DI и(или) DO некликабельной
            dio_button.set_pressed_flag(False)
        # dio_button.set_voicing_flag(False)

    def check_style(self, dio_button):
        if dio_button.is_triggered():
            if dio_button.isChecked():  # если нажата кнопка DIO, то при срабатывании
                if isinstance(dio_button, DOButton) and DOButton.DO_CONTROL:
                    dio_button.change_style('controlled')
                else:
                    dio_button.change_style('pressed')  # цвет меняется на синий
            else:
                dio_button.change_style('triggered')  # цвет меняется на зеленый
        else:
            dio_button.change_style('default')  # цвет меняется на исходный

    # ПОДГОТОВКА К ОЗВУЧИВАНИЮ DIO
    def voice_over_preparing(self, dio_button):
        if dio_button.is_clickable():
            if dio_button.isChecked() or not dio_button.get_pressed_flag():
                if (dio_button.is_triggered() and dio_button.num not in dio_button.get_triggered_list()) or \
                        (not dio_button.is_triggered() and dio_button.num in dio_button.get_triggered_list()):
                    self.voicing(dio_button)

    # ОЗВУЧИВАНИЕ DI И DO
    def voicing(self, dio_button):
        try:
            song_dio_type = pygame.mixer.Sound(
                resource_path(f'static/voicing/{self.voice_type}/{dio_button.type}/{dio_button.num}.wav'))
            song_time = song_dio_type.get_length() - 0.3
            song_dio_type.play()
            time.sleep(song_time)
            if not dio_button.is_triggered():
                song_dio_state = pygame.mixer.Sound(
                    resource_path(f'static/voicing/{self.voice_type}/on-off/отключено.wav'))
                song_time = song_dio_state.get_length() - 0.1
                song_dio_state.play()
                time.sleep(song_time)
        except Exception:
            catch_exception()
            msg = "Ошибка озвучивания DI и DO"
            show_msg(msg, 'Ошибка')

    def control_do(self):
        pass

    # ЗАВЕРШЕНИЕ РАБОТЫ ПРОГРАММЫ
    def closeEvent(self, event):
        QTimer.singleShot(0, self.disconnecting)
        event.accept()
        msg = 'Закрытие программы'
        self.send_msg(msg)

    # ВЫВОД СООБЩЕНИЯ В КОНСОЛЬ И СТАТУС-БАР
    def send_msg(self, msg):
        self.statusBar().showMessage(msg)
        print(msg)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyle('Fusion')
    application = MyWindow()
    application.show()
    sys.exit(app.exec())
