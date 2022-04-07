# pyuic5 BempIO_v2.ui -o BempIO_v2.py
"-*- coding: utf-8 -*-"""

import locale
import sys
import threading
import time
import pygame
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
from my_classes import *

locale.setlocale(locale.LC_ALL, 'ru-RU')
log = app_logger.get_app_logger(__name__)


class MainWindow(QtWidgets.QMainWindow):
    """Главное окно приложения"""

    def __init__(self):
        """Настройка окна приложения"""
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle('BempIO')
        self.setWindowIcon(QIcon(app_service.resource_path('static/images/BempIO.ico')))
        self.setFixedSize(760, 700)
        self.polling_time = 0

        # Инициализация параметров кнопки подключения
        self.ui.pushButton_connect.setStyleSheet(f'background: {self.ui.pushButton_connect.RED_COLOR}')
        self.ui.pushButton_connect.setFocus()

        # Инициализация параметров на вкладке "Параметры подключения"
        self.ui.tabWidget.setTabText(0, 'Параметры подключения')
        self.port = None
        if len(self.find_ports()) > 0:
            self.get_port()
        self.ui.comboBox_speed.addItems(['2400', '4800', '9600', '19200', '38400', '56000', '57600', '115200'])
        self.ui.comboBox_speed.setCurrentIndex(4)  # выставить скорость по умолчанию 38400
        self.speed = None
        self.get_speed()  # получить сокрость обмена данными
        self.ui.comboBox_parity.addItems(['N', 'E', 'O'])
        self.parity = None
        self.get_parity()  # получить четность
        self.ui.comboBox_stopbits.addItems(['1', '2'])
        self.stopbits = None
        self.get_stopbits()  # получить количество стоповых битов
        self.ui.pushButton_searh_ports.setIcon(QIcon(app_service.resource_path('static/images/find.svg')))
        self.ui.pushButton_searh_ports.setIconSize(QSize(15, 15))

        # Инициализация параметров на вкладке "Параметры устройства"
        self.ui.tabWidget.setTabText(1, 'Параметры устройства')
        self.max_di = 96
        self.max_do = 96
        self.ui.spinBox_ied_address.setMinimum(1)
        self.ui.spinBox_ied_address.setMaximum(247)
        self.unit = 0x01
        self.ui.comboBox_ied_type.addItems(['БЭМП', 'Другое'])
        self.ied_type = None
        self.get_ied()  # получить тип устройства
        self.ui.spinBox_di_count.setMinimum(1)
        self.ui.spinBox_di_count.setMaximum(96)
        self.ui.spinBox_do_count.setMinimum(1)
        self.ui.spinBox_do_count.setMaximum(96)
        # self.max_di = 1
        # self.ui.spinBox_di_count.setValue(96)
        # self.max_do = 1
        # self.unit = 0x01
        # self.ui.spinBox_do_count.setValue(96)

        # Инициализация параметров на вкладке "Дополнительные функции"
        self.ui.tabWidget.setTabText(2, 'Дополнительные функции')
        self.ui.comboBox_voice_type.addItems(['Дарья', '2', '3', '4'])
        self.voice_type = None
        self.get_voice()

        # Инициализация параметров на вкладке "DI"

        # Обработка событий
        self.ui.pushButton_searh_ports.clicked.connect(self.find_ports)
        self.ui.comboBox_com_port.activated.connect(self.get_port)
        self.ui.comboBox_ied_type.activated.connect(self.get_ied)  # выбрать устройство из выпадающего списка
        self.ui.comboBox_parity.activated.connect(self.get_parity)
        self.ui.comboBox_speed.activated.connect(self.get_speed)
        self.ui.comboBox_stopbits.activated.connect(self.get_stopbits)
        self.ui.comboBox_voice_type.activated.connect(self.get_voice)

        self.ui.pushButton_connect.clicked.connect(self.check_connect)  # подключиться к устройству
        self.ui.pushButton_do_control.clicked.connect(self.control_do)  # включить режим управления релейными выходами

        # Тест фичи
        self.ui.pushButton_searh_ports.clicked.connect(self.test)

    def get_voice(self):
        """ Возвращает текущий тип голоса озвучивания"""
        self.voice_type = self.ui.comboBox_voice_type.currentText()

    @staticmethod
    def show_msg(msg, msg_type='Error'):
        """Выводит всплывающее окно с сообщением """
        window_icon = None
        msg_icon = None
        msg_box = QMessageBox()
        if msg_type == 'Error':
            msg += f'Непредвиденная ошибка: ' + msg
            msg_icon = QMessageBox.Critical
            window_icon = QIcon(app_service.resource_path('static/images/critical.ico'))
        if msg_type == 'Info':
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

    @staticmethod
    def show_ied_dio(group_dio, max_dio):
        """Отображает актуальное количество дискретных входов и выходов"""
        dio_buttons_list = []
        for dio in group_dio.findChildren(QtWidgets.QPushButton):
            dio_buttons_list.append(dio)
        dio_buttons_list.sort(key=lambda x: int(x.text()))
        for dio in dio_buttons_list[max_dio:96]:
            dio.setVisible(False)
        return dio_buttons_list[:max_dio]

    def do_control(self):
        if self.ui.pushButton_do_control.text() == '':
            DOButton.DO_CONTROL = True
        else:
            DOButton.DO_CONTROL = True

    def test(self):
        """Тестирование фичей"""
        print('Запуск теста... ')
        try:
            print(self.speed)
        except Exception as e:
            log.exception(e)

    def find_ports(self):
        """ Возвращает список COM-портов или выводит инфо об ошибке поиска"""
        self.ui.comboBox_com_port.clear()  # очистить список COM-портов
        self.send_to_statusbar("Поиск COM-портов...")

        try:
            com_ports = serial.tools.list_ports.comports()  # получить список активных COM-портов
        except Exception as e:
            log.exception(e)
            MainWindow.show_msg('Warning', 'Ошибка поиска COM-порта!')
        else:
            ports = sorted(list(map(lambda x: x.name, com_ports)))
            self.send_to_statusbar(f'Поиск завершен. Найдено COM-портов:  {len(ports)}')
            if len(ports) == 0:
                ports.append('Нет')
            self.ui.comboBox_com_port.addItems(ports)

            return ports

    def get_port(self):
        """Выбор COM-порта из выпадающего списка"""
        self.port = self.ui.comboBox_com_port.currentText()
        msg = f'Выбран порт:  {self.port}'
        self.send_to_statusbar(msg)

    def get_speed(self):
        """ Возвращает текущую скорость обмена данными"""

        self.speed = int(self.ui.comboBox_speed.currentText())

    def get_parity(self):
        """ Возвращает текущую четность"""
        self.parity = self.ui.comboBox_parity.currentText()

    def get_stopbits(self):

        """ Возвращает текущее количество стоповых битов"""
        self.stopbits = int(self.ui.comboBox_stopbits.currentText())

    def get_ied(self):
        """Выбор устройства из выпадающего списка"""
        self.ied_type = self.ui.comboBox_ied_type.currentText()
        self.send_to_statusbar(f'Выбрано устройство:  {self.ied_type}')
        self.set_ied_params()

    def set_ied_params(self):
        """Инициализацтя параметров DI и DO устройства"""
        di_address = self.ui.lineEdit_di_01_address
        do_address = self.ui.lineEdit_do_01_address
        di_count = self.ui.spinBox_di_count
        do_count = self.ui.spinBox_do_count

        def change_params(flag, di_hex, do_hex):
            di_address.setDisabled(flag)
            di_address.setText(di_hex)
            di_count.setDisabled(flag)
            do_address.setDisabled(flag)
            do_address.setText(do_hex)
            do_count.setDisabled(flag)

        if self.ied_type == 'БЭМП':
            change_params(True, '0x0500', '0x0700')
            di_count.setValue(self.max_di)
            do_count.setValue(self.max_do)

        elif self.ied_type == 'Другое':
            change_params(False, '0x', '0x')

    def check_connect(self, *args):
        """Подключение к устройству"""
        if self.ui.pushButton_connect.text() == "ПОДКЛЮЧИТЬ" or self.ui.pushButton_connect.isChecked():
            self.connecting()
        else:
            self.disconnecting()

    def connecting(self):
        """Проверка связи с устройством"""

        msg = "Проверка связи с устройством..."
        self.send_to_statusbar(msg)
        port = self.port
        try:
            self.client = ModbusSerialClient(
                method='ASCII',
                port=port,
                baudrate=self.speed,
                bytesize=8,
                parity=self.parity,
                stopbits=self.stopbits)
        except Exception as e:
            log.exception(e)
            msg = "Ошибка проверки связи с устройством!"
            MainWindow.show_msg(msg, 'Error')
        else:
            try:
                assert self.client.connect()
                assert self.client.is_socket_open()
            except AssertionError:
                msg = 'Неправильные параметры подключения или COM-порт занят!'
                MainWindow.show_msg('Warning', msg)
                self.send_to_statusbar(msg)
            except Exception as e:
                log.exception(e)
                MainWindow.show_msg(e)
            else:
                try:
                    msg = f"Связь c {self.ied_type} установлена!"
                    self.send_to_statusbar(msg)
                    self.check_ied_params()  # проверка параметров устройства
                    self.show_dio_buttons()  # отображение актуального числа di и do
                    self.change_buttons_style(True)  # активация/деактивация кнопок управления
                    self.run_threads()
                    pygame.init()  # инициализация медиапроигрывателя
                    msg = f"Устройство {self.ied_type} подключено!"
                    self.send_to_statusbar(msg)
                except Exception as e:
                    log.exception(e)

    def check_ied_params(self):
        """Проверка параметров подключенного устройства"""
        msg = f"Проверка параметров устройства {self.ied_type}..."
        self.send_to_statusbar(msg)
        self.check_max_dio()
        self.check_dio_01_address()

    def check_max_dio(self):
        """Определение количества DI и DO в подключенном устройстве"""

        try:
            if self.ied_type == 'БЭМП':
                try:
                    self.max_di = self.client.read_holding_registers(0x0100, 1, unit=self.unit).registers[0]
                    self.max_do = self.client.read_holding_registers(0x0101, 1, unit=self.unit).registers[0]
                except Exception as e:
                    log.exception(e)
                    msg = "Ошибка чтения количества DI и DO"
                    MainWindow.show_msg(msg, 'Error')
            elif self.ied_type == 'Прочее':
                self.max_di = int(self.ui.spinBox_di_count.text())
                self.max_do = int(self.ui.spinBox_di_count.text())
            assert isinstance(self.max_di, int), 'Неправильный адрес DI 1'
            assert isinstance(self.max_do, int), 'Неправильный адрес DO 1'
        except AssertionError:
            msg = "Некорректные параметры DI и DO."
            MainWindow.show_msg(msg, 'Error')
            self.send_to_statusbar(msg)
        except Exception as e:
            log.exception(e)
            self.client.close()
            MainWindow.show_msg(e)
        else:
            self.ui.spinBox_di_count.setValue(self.max_di)
            self.ui.spinBox_do_count.setValue(self.max_do)
            msg = f"Количество DI - {self.max_di}\nКоличество DO - {self.max_do}"
            self.send_to_statusbar(msg)

    def check_dio_01_address(self):
        """Определение адреса DI_1 и DO_1 в подключенном устройстве"""

        di_01_address = self.ui.lineEdit_di_01_address.text()
        do_01_address = self.ui.lineEdit_do_01_address.text()
        try:
            assert isinstance(int(di_01_address, 16), int), "Неправильный адрес DI 1"
            assert isinstance(int(do_01_address, 16), int), "Неправильный адрес DO 1 "
        except AssertionError:
            msg = "Некорректные параметры DI и DO"
            self.send_to_statusbar(msg)
            MainWindow.show_msg(msg, 'Error')
        except Exception as e:
            log.exception(e)
            self.client.close()
            MainWindow.show_msg(e)
        else:
            msg = f"Адрес DI 1 - {di_01_address}\nАдрес DO 1 - {do_01_address}"
            self.send_to_statusbar(msg)
            self.di_start_address = int(di_01_address, 16)
            self.do_start_address = int(do_01_address, 16)

    def show_dio_buttons(self):
        """Отображение актуального числа DI и DO"""

        self.di_list = MainWindow.show_ied_dio(self.ui.groupBox_di, self.max_di)
        self.do_list = MainWindow.show_ied_dio(self.ui.groupBox_do, self.max_do)

    def run_threads(self):
        """Инициализация потока опроса  DI и DO"""

        self.th_polling_dio = threading.Thread(target=self.polling_dio, name='th_polling_dio')
        self.th_polling_dio.run_flag = True
        try:
            self.th_polling_dio.start()
        except Exception as e:
            log.exception(e)
            msg = "Ошибка запуска опроса DI и DO"
            self.send_to_statusbar(msg)
            MainWindow.show_msg(e)
        else:
            msg = "Запущен опрос DI и DO."
            self.send_to_statusbar(msg)

    def change_buttons_style(self, a0: bool):
        """Изменение вида кнопок настроек при подключении/отключении"""

        self.ui.tab2_dio_settings.setDisabled(a0)
        self.ui.tab1_connect_settings.setDisabled(a0)
        self.ui.groupBox_voicing_settings.setEnabled(a0)
        self.ui.groupBox_do_control.setEnabled(a0)
        self.ui.groupBox_di.setEnabled(a0)
        self.ui.groupBox_do.setEnabled(a0)
        self.ui.pushButton_connect.change_style(a0)
        self.ui.pushButton_do_control.setEnabled(a0)
        self.ui.comboBox_voice_type.setEnabled(False)

    def disconnecting(self):
        """Отключение от устройства"""

        msg = "Отключение от устройства..."
        self.send_to_statusbar(msg)
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
            self.client.close()
            msg = f"Устройство {self.ied_type} отключено!"
            self.send_to_statusbar(msg)
            self.get_ied()
            self.change_buttons_style(False)
            self.unselect_dio(self.ui.groupBox_di)
            self.unselect_dio(self.ui.groupBox_do)
            pygame.quit()

    def unselect_dio(self, group_dio):
        """отображение ранее скрытых DI и DO"""

        for dio in group_dio.findChildren(QtWidgets.QPushButton):
            dio.setChecked(False)
            dio.setVisible(True)
            dio.setStyleSheet('background: #f0f0f0')
            dio.setFont(QFont('MS Shell Dlg 2', 9, QFont.Normal))

    def polling_dio(self):
        """Опрос DI и DO"""

        while getattr(self.th_polling_dio, 'run_flag', True):
            time.sleep(self.polling_time)
            self.processing(self.di_start_address, self.max_di, self.di_list)
            self.processing(self.do_start_address, self.max_do, self.do_list)

    def processing(self, dio_address, max_dio, dio_buttons_list):
        """Вспомогательная функция опроса DI и DO"""

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
        except Exception as e:
            log.exception(e)

    def get_request(self, dio_address, max_dio):
        """Отправка запроса в устройство"""

        try:
            dio_list = self.client.read_coils(dio_address, max_dio, unit=self.unit).bits  # считывание регистров
        except (AttributeError, ConnectionException):
            # QTimer.singleShot(0, self.ui.pushButton_connect.click)
            sys.exit()
        except Exception as e:
            log.exception(e)
            msg = "Ошибка опроса DI и DO"
            MainWindow.show_msg(msg)
        else:
            return dio_list

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

    def voice_over_preparing(self, dio_button):
        """Подготовка к озвучиванию DIO"""

        if dio_button.is_clickable():
            if dio_button.isChecked() or not dio_button.get_pressed_flag():
                if (dio_button.is_triggered() and dio_button.num not in dio_button.get_triggered_list()) or \
                        (not dio_button.is_triggered() and dio_button.num in dio_button.get_triggered_list()):
                    self.voicing(dio_button, )

    def voicing(self, dio_button):
        """Озвучивание DI и DO"""

        try:
            if dio_button.is_triggered() or (not dio_button.is_triggered() and self.ui.VoiceCtrlCheckBox.isChecked()):
                song_dio_type = pygame.mixer.Sound(
                    app_service.resource_path(
                        f'static/voicing/{self.voice_type}/{dio_button.type}/{dio_button.num}.wav'))
                song_time = song_dio_type.get_length() - 0.3
                song_dio_type.play()
                time.sleep(song_time)
                if not dio_button.is_triggered():
                    song_dio_state = pygame.mixer.Sound(
                        app_service.resource_path(f'static/voicing/{self.voice_type}/on-off/отключено.wav'))
                    song_time = song_dio_state.get_length() - 0.1
                    song_dio_state.play()
                    time.sleep(song_time)
        except Exception as e:
            log.exception(e)
            msg = "Ошибка озвучивания DI и DO"
            MainWindow.show_msg(msg, 'Ошибка')

    def control_do(self):
        pass

    def closeEvent(self, event):
        """Завершение работы программы"""
        QTimer.singleShot(0, self.disconnecting)
        event.accept()
        msg = 'Закрытие программы'
        self.send_to_statusbar(msg)

    def send_to_statusbar(self, msg):
        """Вывод сообщения в консоль и статус-бар"""
        print(msg)
        self.statusBar().showMessage(msg)


if __name__ == "__main__":
    try:
        app = QtWidgets.QApplication([])
        app.setStyle('Fusion')
        application = MainWindow()
        application.show()
        sys.exit(app.exec())
    except Exception as e:
        log.exception(e)
