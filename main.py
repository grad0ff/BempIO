# pyuic5 BempIO.ui -o BempIO.py
import asyncio
import time, logging
import sys, pygame, threading
import serial.tools.list_ports

from PyQt5 import QtWidgets
from PyQt5.QtGui import QPalette, QIcon
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QMessageBox
from BempIO import Ui_MainWindow
from pymodbus.client.sync import ModbusSerialClient
from pymodbus.exceptions import ConnectionException


# ДЕТАЛИЗАЦИЯ ИСКЛЮЧЕНИЙ
def catch_exception():
    log = logging.getLogger()
    log.exception("Исключение:")


def except_cather(func):
    def wrapper(func):
        try:
            func()
        except Exception as e:
            catch_exception()
    wrapper(func)


# ВЫВОД ОКНА С СООБЩЕНИЕМ
def show_msg(msg, msg_type="Информация"):
    msg_window = QMessageBox()
    msg_icon = QMessageBox.Information
    window_icon = QIcon('static/images/green_LED.png')
    if msg_type == 'Ошибка':
        window_icon = QIcon('static/images/blue_LED.png')
        msg_icon = QMessageBox.Warning
    elif msg_type == 'Проблема':
        window_icon = QIcon('static/images/red_LED.png')
        msg_icon = QMessageBox.Critical
    msg_window.setWindowTitle(msg_type + "!")
    msg_window.setWindowIcon(window_icon)
    msg_window.setIcon(msg_icon)
    msg_window.setText(msg)
    msg_window.exec_()
    if msg_type == 'Проблема':
        sys.exit()


# ОТОБРАЖЕНИЕ АКТУАЛЬНОГО КОЛИЧЕСТВА DI И DO
def show_ied_dio(group_dio, max_dio):
    dio_list = []
    for dio in group_dio.findChildren(QtWidgets.QPushButton):
        dio_list.append(dio)
    dio_list.sort(key=lambda x: int(x.text()))
    for dio in dio_list[max_dio:96]:
        dio.setVisible(False)
    return dio_list[:max_dio]


class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle('BempIO')
        self.setFixedSize(760, 960)
        self.searh_port = self.ui.pushButton_searh_ports
        self.searh_port.setIcon(QIcon('static/images/find.svg'))
        self.searh_port.setIconSize(QSize(15, 15))
        self.msg = QMessageBox()

        # инициализация параметров DI и DO устройства
        self.ui.comboBox_ied_type.addItems(['БЭМП [РУ]'])
        self.select_ied()

        # инициализация параметров подключения
        self.find_ports()
        self.ui.pushButton_searh_ports.clicked.connect(self.find_ports)
        self.ui.comboBox_speed.addItems(['2400', '4800', '9600', '19200', '38400', '56000', '57600', '115200'])
        self.ui.comboBox_speed.setCurrentIndex(4)
        self.ui.comboBox_parity.addItems(['N', 'E', 'O'])
        self.ui.comboBox_stopbits.addItems(['1', '2'])
        self.ui.spinBox_ied_address.setMinimum(1)
        self.ui.spinBox_ied_address.setMaximum(247)
        self.ui.pushButton_disconnect.setStyleSheet('background: rgb(255,85,70)')
        self.ui.pushButton_connect.setFocus()
        self.ui.comboBox_voice_type.addItems(['1', '2', '3', '4'])
        self.polling_time = 0.5
        self.max_di = 1
        self.max_do = 1
        self.triggered_di_list = set()
        self.triggered_do_list = set()

        self.unit = 0x01

        # обработка событий
        self.ui.pushButton_connect.clicked.connect(self.connecting)
        self.ui.pushButton_disconnect.clicked.connect(self.disconnecting)
        self.ui.comboBox_ied_type.activated.connect(self.select_ied)

        self.ui.pushButton_DI_01.clicked.connect(self._testing)

        # self.myclose = False

    # ВЫБОР УСТРОЙСТВА ИЗ ВЫПАДАЮЩЕГО СПИСКА
    def select_ied(self):
        self.ied_type = self.ui.comboBox_ied_type.currentText()
        self.statusBar().showMessage(f"Выбрано устройство: {self.ied_type}")
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
        self.ui.comboBox_com_port.clear()
        try:
            port_list = serial.tools.list_ports.comports()
            ports = sorted(list(map(lambda x: x.name, port_list)))
            self.ui.comboBox_com_port.addItems(ports)
        except Exception as e:
            catch_exception()
            show_msg("Ошибка поиска COM-порта", 'Проблема')

    # ПОДКЛЮЧЕНИЕ К УСТРОЙСТВУ
    def connecting(self):
        try:
            self.client = ModbusSerialClient(
                method='ASCII',
                port=self.ui.comboBox_com_port.currentText(),
                baudrate=int(self.ui.comboBox_speed.currentText()),
                bytesize=8,
                parity=self.ui.comboBox_parity.currentText(),
                stopbits=int(self.ui.comboBox_stopbits.currentText()),
            )
            self.client.connect()
            assert self.client.is_socket_open()
        except AssertionError:
            show_msg('Неправильные параметры подключения или COM-порт занят!', 'Ошибка')
        except Exception as e:
            catch_exception()
            print(e)
            show_msg(e, 'Проблема')
        else:
            self.check_ied_params()
            self.show_dio_buttons()
            self.change_btn_style(True)
            pygame.init()
            self.thread_check_dio()

    # ПРОВЕРКА ПАРАМЕТРОВ ПОДКЛЮЧЕННОГО УСТРОЙСТВА
    def check_ied_params(self):
        self.statusBar().showMessage(f"Проверка параметров устройства {self.ied_type}")
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
            print(f"Количество:\nDI - {self.max_di}\nDO - {self.max_do}")
            di_01_address = self.ui.lineEdit_di_01_address.text()
            do_01_address = self.ui.lineEdit_do_01_address.text()
            # assert isinstance(int(di_01_address, 16), int), "Неправильный адрес DI 1"
            # assert isinstance(int(do_01_address, 16), int), "Неправильный адрес DO 1 "
            self.di_address = int(di_01_address, 16)
            self.do_address = int(do_01_address, 16)
        except AssertionError:
            show_msg("Некорректные параметры DI и DO", 'Ошибка')
        except Exception as e:
            catch_exception()
            self.client.close()
            show_msg(e, 'Проблема')

    # ОТОБРАЖЕНИЕ АКТУАЛЬНОГО ЧИСЛА DI И DO
    def show_dio_buttons(self):
        self.di_list = show_ied_dio(self.ui.groupBox_di, self.max_di)
        self.do_list = show_ied_dio(self.ui.groupBox_do, self.max_do)

    # ЗАПУСК ПОТОКА ОПРОСА DI И DO
    def thread_check_dio(self):
        self.th_check_dio = threading.Thread(target=self.check_dio, name='th_check_dio')
        self.th_check_dio.run_flag = True
        self.th_check_dio.start()

        self.th_voicing_dio = threading.Thread(target=self.voicing_dio, args=(None, None), name='th_voicing_dio')
        self.th_voicing_dio.run_flag = True
        self.th_voicing_dio.start()

    # ИЗМЕНЕНИЕ ВИДА КНОПОК НАСТРОЕК ПРИ ПОДКЛЮЧЕНИИ/ОТКЛЮЧЕНИИ
    def change_btn_style(self, value):
        self.ui.groupBox_dio_settings.setDisabled(value)
        self.ui.groupBox_connect_settings.setDisabled(value)
        self.ui.groupBox_dio_voicing.setEnabled(value)
        self.ui.pushButton_connect.setDisabled(value)
        self.ui.pushButton_disconnect.setEnabled(value)
        self.ui.groupBox_di.setEnabled(value)
        self.ui.groupBox_do.setEnabled(value)
        if value:
            self.ui.pushButton_connect.setStyleSheet('background: rgb(100,250,50)')
            self.ui.pushButton_connect.setText('Подключено')
            self.ui.pushButton_disconnect.setStyleSheet('background: #f0f0f0')
            self.ui.pushButton_disconnect.setText('Отключить')
            self.statusBar().showMessage(f"Устройство {self.ied_type} подключено!")
        else:
            self.ui.pushButton_connect.setStyleSheet('background: #f0f0f0')
            self.ui.pushButton_connect.setText('Подключить')
            self.ui.pushButton_disconnect.setStyleSheet('background: rgb(255,85,70)')
            self.ui.pushButton_disconnect.setText('Отключено')
            self.statusBar().showMessage(f"Устройство {self.ied_type} отключено!")
            self.select_ied()

    # ОТКЛЮЧЕНИЕ ОТ УСТРОЙСТВА
    def disconnecting(self):
        try:
            if self.th_check_dio.is_alive():
                self.th_check_dio.run_flag = False
            while self.th_check_dio.is_alive():
                pass
            if self.th_voicing_dio.is_alive():
                self.th_voicing_dio.run_flag = False
            self.client.close()
            self.select_ied()
            self.change_btn_style(False)
            self.unselect_dio(self.ui.groupBox_di)
            self.unselect_dio(self.ui.groupBox_do)
            pygame.quit()
        except Exception as e:
            catch_exception()
            show_msg(e, 'Проблема!')

    # ОТОБРАЖЕНИЕ РАНЕЕ СКРЫТЫХ КНОПОК
    def unselect_dio(self, group_dio):
        for dio in group_dio.findChildren(QtWidgets.QPushButton):
            dio.setVisible(True)
            dio.setStyleSheet('background: #f0f0f0')

    # ОПРОС DI и DO
    def check_dio(self):
        while getattr(self.th_check_dio, 'run_flag', True):
            try:
                time.sleep(self.polling_time)
                self.checking_dio(self.di_address, self.max_di, self.di_list, self.triggered_di_list, 'DI')
                self.checking_dio(self.do_address, self.max_do, self.do_list, self.triggered_do_list, 'DO')
            except Exception as e:
                catch_exception()
                print(e)

    # ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ОПРОСА DI и DO
    def checking_dio(self, dio_address, max_dio, dio_list, trig_dio_list, dio_type):
        try:
            checked_dio_list = self.client.read_coils(dio_address, max_dio, unit=self.unit).bits
            for i in range(max_dio):
                dio = i + 1
                if checked_dio_list[i]:
                    dio_list[i].setStyleSheet('background: rgb(51,204,51)')
                    if dio not in trig_dio_list and not self.ui.radioButton_voicing_off.isChecked():
                        self.voicing_dio(dio, dio_type)
                    trig_dio_list.add(dio)
                else:
                    if dio in trig_dio_list:
                        trig_dio_list.remove(dio)
                        dio_list[i].setStyleSheet('background: #f0f0f0')
        except ConnectionException:
            print(555)
            self.th_check_dio.run_flag = False
            self.close()
        except Exception as e:
            catch_exception()
            show_msg(e, 'Проблема!')

    def voicing_dio(self, dio, dio_type):
        if self.ui.radioButton_di_voicing.isChecked() and dio_type == 'DI':
            self.voicing(dio, dio_type)
        elif self.ui.radioButton_do_voicing.isChecked() and dio_type == 'DO':
            self.voicing(dio, dio_type)
        elif self.ui.radioButton_dio_voicing.isChecked():
            self.voicing(dio, dio_type)

    def voicing(self, dio, dio_type):
        print(f"voicing {dio_type}{dio}")
        try:
            song = pygame.mixer.Sound(f'static/numbers/{dio_type}/{dio}.wav')
            song_time = song.get_length()
            song.play()
            time.sleep(song_time)
        except Exception as e:
            print(e)

    @except_cather
    def closeEvent(self, event):
        self.disconnecting()
        event.accept()

    def _testing(self):
        print('test!')
        i = 0
        while not self.client.is_socket_open():
            time.sleep(1)
            print(self.client.connect())
            i += 1
            print(i)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    application = MyWindow()
    application.show()
    app.setStyle('Fusion')
    qp = QPalette()
    app.setPalette(qp)
    sys.exit(app.exec())
