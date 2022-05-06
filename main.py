# pyuic5 BempIO_v2.ui -o BempIO_v2.py
"-*- coding: utf-8 -*-"""

import locale
import sys
import threading
import time
import pygame
from pymodbus.exceptions import *
import serial.tools.list_ports

import app_logger
import app_service

from BempIO_v2 import Ui_MainWindow
from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize, QTimer
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QMessageBox
from pymodbus.client.sync import ModbusSerialClient
from pymodbus.exceptions import ConnectionException
from app_classes import *

locale.setlocale(locale.LC_ALL, 'ru-RU')
log = app_logger.get_app_logger(__name__)


class MainWindow(QtWidgets.QMainWindow):
    """Главное окно приложения"""

    def __init__(self):
        """Инициализация главного окна приложения"""
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle('BempIO')
        self.setWindowIcon(QIcon(app_service.resource_path('static/images/BempIO.ico')))
        self.setFixedSize(760, 700)
        self.polling_time = 0

        # Инициализация параметров кнопки подключения
        self.ui.pushButton_connect.change_style()
        self.ui.pushButton_connect.setFocus()  # задать фокус на кнопку

        # Инициализация параметров на вкладке "Параметры подключения"
        self.ui.tabWidget.setTabText(0, 'Подключение')
        self.ui.pushButton_searh_ports.setIcon(QIcon(app_service.resource_path('static/images/find.svg')))
        self.ui.pushButton_searh_ports.setIconSize(QSize(15, 15))
        self.port = None
        self.find_ports()
        self.get_port()  # получить COM-порт
        self.ui.comboBox_speed.addItems(['2400', '4800', '9600', '19200', '38400', '56000', '57600', '115200'])
        self.ui.comboBox_speed.setCurrentIndex(4)  # выставить скорость 38400 бод
        self.speed = None
        self.get_speed()  # получить скорость обмена данными
        self.ui.comboBox_parity.addItems(['N', 'E', 'O'])
        self.parity = None
        self.get_parity()  # получить четность
        self.ui.comboBox_stopbits.addItems(['1', '2'])
        self.stopbits = None
        self.get_stopbits()  # получить количество стоповых бит
        self.address = None
        self.ui.spinBox_ied_address.setValue(1)
        self.ui.spinBox_ied_address.setDisabled(True)
        self.set_ied_address()

        # Инициализация параметров на вкладке "Параметры устройства"
        self.ui.tabWidget.setTabText(1, 'Устройство')
        self.ui.comboBox_ied_type.addItems(['БЭМП', 'Другое'])
        self.ui.comboBox_ied_type.setDisabled(True)
        self.ied_type = None
        self.get_ied()  # получить тип устройства
        self.ui.lineEdit_di_01_address.setPlaceholderText('hex')
        self.ui.lineEdit_do_01_address.setPlaceholderText('hex')
        self.di_start_address = None
        self.do_start_address = None
        self.get_start_addresses()
        self.max_di = self.max_do = self.all_dio = 96
        self.ui.spinBox_ied_address.setRange(1, 247)
        self.ui.spinBox_di_count.setRange(1, self.max_di)
        self.ui.spinBox_do_count.setRange(1, self.max_do)

        # Инициализация параметров на вкладке "Дополнительные функции"
        self.ui.tabWidget.setTabText(2, 'Функции')
        self.ui.comboBox_voice_type.addItems(['Дарья', '2', '3', '4'])
        self.voice_type = None
        self.get_voice()  # получить тип голоса

        # Обработка событий
        self.ui.pushButton_connect.clicked.connect(self.connect_manager)  # подключиться к устройству
        self.ui.comboBox_com_port.activated.connect(self.get_port)  # выбрать COM-порт из выпадающего списка
        self.ui.pushButton_searh_ports.clicked.connect(self.find_ports)  # найти активные COM-порты
        self.ui.comboBox_speed.activated.connect(self.get_speed)  # выбрать скорость из выпадающего списка
        self.ui.comboBox_parity.activated.connect(self.get_parity)  # выставить четность
        self.ui.comboBox_stopbits.activated.connect(self.get_stopbits)  # выставить количество стоповых бит
        self.ui.spinBox_ied_address.valueChanged.connect(self.set_ied_address)
        self.ui.comboBox_ied_type.activated.connect(self.get_ied)  # выбрать устройство из выпадающего списка
        self.ui.lineEdit_di_01_address.textEdited.connect(self.get_start_addresses)
        self.ui.lineEdit_do_01_address.textEdited.connect(self.get_start_addresses)

        self.ui.comboBox_voice_type.activated.connect(self.get_voice)  # выбрать голос из выпадающего списка
        self.ui.pushButton_do_control.clicked.connect(self.do_control)  # включить режим управления реле

        # Служебные данные
        self.client = None
        self.active_di_buttons_list = None
        self.active_do_buttons_list = None
        self.th_polling_dio = None
        self.connect_agent = ModbusSerialClient

        # Служебные функции
        self.all_di_buttons = self.get_dio_buttons_list(self.ui.groupBox_di)
        self.all_do_buttons = self.get_dio_buttons_list(self.ui.groupBox_do)

        # Тест фичи
        # self.ui.pushButton_searh_ports.clicked.connect(self.test)

    @staticmethod
    def show_msg(msg, msg_type):
        """Выводит всплывающее окно с сообщением """
        window_icon = None
        msg_icon = None
        msg_box = QMessageBox()
        if msg_type == 'Error':
            msg_icon = QMessageBox.Critical
            window_icon = QIcon(app_service.resource_path('static/images/critical.ico'))
        elif msg_type == 'Info':
            msg_icon = QMessageBox.Information
            window_icon = QIcon(app_service.resource_path('static/images/information.ico'))
        elif msg_type == 'Warning':
            window_icon = QIcon(app_service.resource_path('static/images/warning.ico'))
            msg_icon = QMessageBox.Warning
        msg_box.setWindowTitle(msg_type + "!")
        msg_box.setWindowIcon(window_icon)
        msg_box.setIcon(msg_icon)
        msg_box.setText(msg)
        msg_box.exec_()

    def test(self):
        """Тестирование фичей"""
        print('Запуск теста... ')
        try:
            print(self.speed)
        except Exception as e:
            log.exception(e)

    # НАСТРОЙКА ПАРАМЕТРОВ УСТРОЙСТВА
    def get_port(self):
        """Выбор COM-порта из выпадающего списка"""
        self.port = self.ui.comboBox_com_port.currentText()
        self.send_to_statusbar(f'Выбран порт:  {self.port}')

    def find_ports(self):
        """ Возвращает список COM-портов или выводит инфо об ошибке поиска"""
        self.send_to_statusbar("Поиск COM-портов...")
        self.ui.comboBox_com_port.clear()  # очистить список COM-портов
        try:
            com_ports = serial.tools.list_ports.comports()  # получить список активных COM-портов
        except Exception as e:
            log.exception(e)
            MainWindow.show_msg('Ошибка поиска COM-порта!', 'Warning')
        else:
            ports = sorted(list(map(lambda port: port.name, com_ports)))
            self.send_to_statusbar(f'Поиск завершен. Найдено COM-портов:  {len(ports)}')
            if len(ports) == 0:
                ports.append('Нет')
            self.ui.comboBox_com_port.addItems(ports)
            return ports

    def get_speed(self):
        """ Возвращает выбранную скорость обмена данными"""
        self.speed = int(self.ui.comboBox_speed.currentText())
        self.send_to_statusbar(f'Выбрана скорость:  {self.speed} бод')

    def get_parity(self):
        """ Возвращает выбранную четность """
        self.parity = self.ui.comboBox_parity.currentText()
        self.send_to_statusbar(f'Выбрана четность:  {self.parity}')

    def get_stopbits(self):
        """ Возвращает текущее количество стоповых битов"""
        self.stopbits = int(self.ui.comboBox_stopbits.currentText())
        self.send_to_statusbar(f'Выбрано количество стоповых бит:  {self.stopbits}')

    def set_ied_address(self):
        self.address = self.ui.spinBox_ied_address.value()
        self.send_to_statusbar(f'Выставлен адрес:  {self.address}')

    def get_ied(self):
        """ Выбирает устройство из выпадающего списка и применяет соответствующие настройки """
        self.ied_type = self.ui.comboBox_ied_type.currentText()
        self.send_to_statusbar(f'Выбрано устройство:  {self.ied_type}')

        def change_ied_params(flag, di_hex, do_hex):
            self.ui.lineEdit_di_01_address.setDisabled(flag)
            self.ui.lineEdit_di_01_address.setText(di_hex)
            self.ui.spinBox_di_count.setValue(96)
            self.ui.spinBox_di_count.setDisabled(flag)

            self.ui.lineEdit_do_01_address.setDisabled(flag)
            self.ui.lineEdit_do_01_address.setText(do_hex)
            self.ui.spinBox_do_count.setValue(96)
            self.ui.spinBox_do_count.setDisabled(flag)

        if self.ied_type == 'БЭМП':
            change_ied_params(True, '0x0500', '0x0700')
        elif self.ied_type == 'Другое':
            change_ied_params(False, '', '')

    def get_voice(self):
        """ Возвращает текущий тип голоса озвучивания"""
        self.voice_type = self.ui.comboBox_voice_type.currentText()

    def do_control(self):
        if self.ui.pushButton_do_control.text() == '':
            DOButton.DO_CONTROL = True
        else:
            DOButton.DO_CONTROL = True

    # ПОДКЛЮЧЕНИЕ К УСТРОЙСТВУ
    def connect_manager(self):
        """ Менеджер подключений """
        print('Запущен connect_manager')
        try:
            if self.client is None:
                self.client = self.get_client()  # получить клиент подключения
                if isinstance(self.client, ModbusSerialClient):
                    self.get_start_addresses()  # задать начальные адреса DI и DO
                    self.get_dio_count()  # задать данные по количеству DI и DO
                    self.show_active_dio()  # показать имеющиеся в устройстве DI и DO
                    self.change_buttons_style(True)  # изменить внешний вид кнопок
                    pygame.init()  # инициализация медиапроигрывателя
                    self.run_threads()
                    self.send_to_statusbar(f'Устройство {self.ied_type} подключено')
            else:
                self.disconnecting()
        except Exception as e:
            MainWindow.show_msg(e)
            log.exception(e)

    def get_client(self) -> ModbusSerialClient:
        """ Проверяет связь с устройством, возвращает клиент """
        self.send_to_statusbar(f'Проверка связи с {self.ied_type}...')
        try:
            client = self.connect_agent(
                method='ASCII',
                port=self.port,
                baudrate=self.speed,
                bytesize=8,
                parity=self.parity,
                stopbits=self.stopbits)
            if client.connect() and client.is_socket_open():
                # os_vesion = client.read_holding_registers(0x0106, unit=self.address).registers[0]
                # assert os_vesion == 121, 'Устройство не является БЭМП'
                return client
            else:
                MainWindow.show_msg('Неправильные параметры подключения или COM-порт занят!', 'Warning')
            # 'Ошибка подключения к устройству'
            # num1 = str(client.read_holding_registers(0x010C, unit=self.address).registers[0])
            # num2 = str(client.read_holding_registers(0x010D, unit=self.address).registers[0])
            # assert num1.isdigit() and num1.isdigit() and 5 < len(num1 + num2) < 9
        except Exception as e:
            log.exception(e)
            MainWindow.show_msg(e)
        # else:
        # self.send_to_statusbar(f'Связь c {self.ied_type} установлена')

    def get_start_addresses(self):
        """ Определяет адреса DI_1 и DO_1 подключенного устройства """
        di_start_address = self.ui.lineEdit_di_01_address.text()
        do_start_address = self.ui.lineEdit_do_01_address.text()
        try:
            assert isinstance(int(di_start_address, 16), int), 'Некорректный адрес DI 1'
            assert isinstance(int(do_start_address, 16), int), 'Некорректный адрес DO 1'
        except AssertionError:
            MainWindow.show_msg('Некорректные параметры DI и DO', 'Error')
        except Exception as e:
            MainWindow.show_msg(e)
            log.exception(e)
            self.client.close()
        else:
            self.send_to_statusbar(f'Адрес DI 1 - {di_start_address}\nАдрес DO 1 - {do_start_address}')
            self.di_start_address = int(di_start_address, 16)
            self.do_start_address = int(do_start_address, 16)

    def get_dio_count(self):
        """Определяет количество DI и DO в подключенном устройстве """
        self.send_to_statusbar(f'Проверка параметров устройства {self.ied_type}...')
        if self.ied_type == 'БЭМП':
            try:
                self.max_di = self.client.read_holding_registers(0x0100, unit=self.address).registers[0]
                self.max_do = self.client.read_holding_registers(0x0101, unit=self.address).registers[0]
            except Exception as e:
                MainWindow.show_msg('Ошибка чтения количества DI и DO БЭМП', 'Error')
                log.exception(e)
        elif self.ied_type == 'Другое':
            self.max_di = int(self.ui.spinBox_di_count.text())
            self.max_do = int(self.ui.spinBox_di_count.text())
        try:
            assert isinstance(self.max_di, int), 'Неправильный адрес DI 1'
            assert isinstance(self.max_do, int), 'Неправильный адрес DO 1'
        except AssertionError:
            MainWindow.show_msg('Некорректные параметры DI и DO.', 'Error')
        except Exception as e:
            MainWindow.show_msg(e)
            log.exception(e)
            self.client.close()
        else:
            self.ui.spinBox_di_count.setValue(self.max_di)
            self.ui.spinBox_do_count.setValue(self.max_do)
            msg = f"Количество DI - {self.max_di}\nКоличество DO - {self.max_do}"
            self.send_to_statusbar(msg)

    def show_active_dio(self):
        """Отображает имеющеся в устройстве DI и DO"""

        def get_active_dio(all_dio_buttons, max_dio):
            try:
                for dio in all_dio_buttons[max_dio:]:
                    dio.setVisible(False)
            except Exception as e:
                log.exception(e)
            else:
                return all_dio_buttons[:max_dio]

        self.active_di_buttons_list = get_active_dio(self.all_di_buttons, self.max_di)
        self.active_do_buttons_list = get_active_dio(self.all_do_buttons, self.max_do)

    def change_buttons_style(self, flag: bool):
        """ Изменение вида кнопок настроек при подключении/отключении """
        self.ui.pushButton_connect.change_style()
        self.ui.groupBox_di.setEnabled(flag)  # активация окна с DI
        self.ui.groupBox_do.setEnabled(flag)  # активация окна с DO
        self.ui.tab1_connect_settings.setDisabled(flag)  # деактивация вкладки с настройками подключения
        self.ui.tab2_dio_settings.setDisabled(flag)  # деактивация вкладки с настройками устройства
        # self.ui.tab3_functions.setEnabled(flag)  # активация вкладки с дополнительными функциями
        self.ui.groupBox_voicing_settings.setEnabled(flag)
        self.ui.groupBox_do_control.setEnabled(flag)

        self.ui.pushButton_do_control.setEnabled(False)
        self.ui.comboBox_voice_type.setEnabled(False)

    def run_threads(self):
        """ Запускает поток опроса DI и DO """
        self.th_polling_dio = threading.Thread(target=self.polling_dio, name='th_polling_dio')
        self.th_polling_dio.run_flag = True
        try:
            self.th_polling_dio.start()
            self.send_to_statusbar('Запущен опрос DI и DO')
        except Exception as e:
            MainWindow.show_msg('Ошибка запуска опроса DI и DO')
            log.exception(e)

    def disconnecting(self) -> None:
        """ Отключает от устройства """
        self.send_to_statusbar('Отключение от устройства...')
        self.ui.radioButton_voicing_off.setChecked(True)
        try:
            if self.th_polling_dio.is_alive():
                self.th_polling_dio.run_flag = False
            while self.th_polling_dio.is_alive():
                pass
        except AttributeError:
            pass
        except Exception as e:
            log.exception(e)
            msg = "Ошибка отключения от устройства"
            MainWindow.show_msg(msg)
        else:
            pygame.quit()
            msg = f"Устройство {self.ied_type} отключено!"
            self.send_to_statusbar(msg)
            self.get_ied()
            self.change_buttons_style(False)
            self.unselect_dio(self.ui.groupBox_di)
            self.unselect_dio(self.ui.groupBox_do)
            self.client.close()
        finally:
            self.client = None

    def unselect_dio(self, group_dio):
        """отображение ранее скрытых DI и DO"""

        for dio in group_dio.findChildren(QtWidgets.QPushButton):
            dio.setChecked(False)
            dio.setVisible(True)
            dio.setStyleSheet('background: #f0f0f0')
            dio.setFont(QFont('MS Shell Dlg 2', 9, QFont.Normal))

    def polling_dio(self):
        """ Опрашивает DI и DO в отдельном потоке """

        def get_request(dio_start_address, max_dio):
            """ Отправляет запрос в устройство и возвращает состояний DI и DO в виде списка """
            try:
                dio_state_list = self.client.read_coils(dio_start_address, max_dio,
                                                        unit=self.address).bits  # считывание регистров
            except Exception as e:
                log.exception(e)
                MainWindow.show_msg('Ошибка опроса DI и DO', 'Error')
            else:
                return dio_state_list

        def processing(dio_start_address, max_dio, dio_buttons_list):
            """ Вспомогательная функция опроса DI и DO """
            dio_list = get_request(dio_start_address, max_dio)  # получить список DI или DO

            try:
                for i in range(max_dio):  # для актуального количества ва DI или DO
                    dio_button = dio_buttons_list[i]
                    dio_button.number += 1  # задает № отдельного DI или DO
                    dio_button.triggered = True if dio_list[i] else False  # если DIO сработал, выставить флаг

                    if self.state_is_changed:
                        self.change_style()
                    self.check_clickable(
                        dio_button)  # сделать кнопки DI и(или) DO кликабельными, если включено их озвучивание
                    # self.check_style(dio_button)
                    self.voice_over_preparing(dio_button)  # подготовка к озвучиванию DIO
                    if dio_button.is_pressed():
                        dio_button.add_to_triggered_dio_list(dio_button.num)
                    elif dio_button.num in dio_button.get_triggered_list():
                        dio_button.del_from_triggered_dio_list(dio_button.num)
                    time.sleep(0.01)
            except Exception as e:
                log.exception(e)

        while self.th_polling_dio.run_flag:
            processing(self.di_start_address, self.max_di, self.active_di_buttons_list)
            processing(self.do_start_address, self.max_do, self.active_do_buttons_list)
            time.sleep(self.polling_time)

    def check_clickable(self, dio_button):
        """Возможность нажатия кнопок DI или DO, если включено озвучивание"""

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

        if dio_button.is_pressed():
            if dio_button.isChecked():  # если нажата кнопка DIO, то при срабатывании
                if isinstance(dio_button, DOButton) and DOButton.DO_CONTROL:
                    dio_button.set_style('controlled')
                else:
                    dio_button.set_style('pressed')  # цвет меняется на синий
            else:
                dio_button.set_style('triggered')  # цвет меняется на зеленый
        else:
            dio_button.set_style('default')  # цвет меняется на исходный

    def voice_over_preparing(self, dio_button):
        """Подготовка к озвучиванию DIO"""

        if dio_button.is_clickable():
            if dio_button.isChecked() or not dio_button.get_pressed_flag():
                if (dio_button.is_pressed() and dio_button.num not in dio_button.get_triggered_list()) or \
                        (not dio_button.is_pressed() and dio_button.num in dio_button.get_triggered_list()):
                    self.voicing(dio_button, )

    def voicing(self, dio_button):
        """Озвучивание DI и DO"""

        try:
            if dio_button.is_pressed() or (not dio_button.is_pressed() and self.ui.VoiceCtrlCheckBox.isChecked()):
                song_dio_type = pygame.mixer.Sound(
                    app_service.resource_path(
                        f'static/voicing/{self.voice_type}/{dio_button.type}/{dio_button.num}.wav'))
                song_time = song_dio_type.get_length() - 0.3
                song_dio_type.play()
                time.sleep(song_time)
                if not dio_button.is_pressed():
                    song_dio_state = pygame.mixer.Sound(
                        app_service.resource_path(f'static/voicing/{self.voice_type}/on-off/отключено.wav'))
                    song_time = song_dio_state.get_length() - 0.1
                    song_dio_state.play()
                    time.sleep(song_time)
        except Exception as e:
            log.exception(e)
            msg = "Ошибка озвучивания DI и DO"
            MainWindow.show_msg(msg, 'Ошибка')

    def do_control(self):
        pass

    def closeEvent(self, event):
        """Завершение работы программы"""
        QTimer.singleShot(0, self.disconnecting)
        event.accept()
        msg = 'Закрытие программы'
        self.send_to_statusbar(msg)

    # СЛУЖЕБНЫЕ ФУНКЦИИ
    def send_to_statusbar(self, msg):
        """Вывод сообщения в консоль и статус-бар"""
        print(msg)
        self.statusBar().showMessage(msg)

    @staticmethod
    def get_dio_buttons_list(group_dio):
        dio_buttons_list = []
        try:
            for dio in group_dio.findChildren(QtWidgets.QPushButton):
                dio_buttons_list.append(dio)
            dio_buttons_list.sort(key=lambda num: int(num.text()))
        except Exception as e:
            log.exception(e)
        else:
            return dio_buttons_list


if __name__ == "__main__":
    try:
        app = QtWidgets.QApplication([])
        app.setStyle('Fusion')
        application = MainWindow()
        application.show()
        sys.exit(app.exec())
    except Exception as e:
        log.exception(e)
