# coding: UTF-8

import sys, os, time
import serial
from serial.tools import list_ports

def get_line(device):
    rx_buffer = ""
    while True:
        chars = device.read()
        if chars == "\n":
            break
        rx_buffer += chars
    return rx_buffer


# ポート番号を取得する##################################
if sys.platform == "linux" or sys.platform == "linux2":
    matched_ports = list_ports.grep("ttyUSB")
elif sys.platform == "darwin":
    matched_ports = list_ports.grep("cu.usbserial-")
for match_tuple in matched_ports:
    SERIAL_PORT = match_tuple[0]
    break
#####################################################

# COM接続
try:
    device = serial.Serial(SERIAL_PORT, 921600, timeout=1, writeTimeout=20)
except:
    sys.stderr.write('USBへの接続に失敗しました！\n')
    sys.exit(1)

# コマンドモードに変更
device.write(chr(0x13))

# STAモード有効
StrCommand = "P03," + "true" + "\n"
device.write(StrCommand)
strRet = get_line(device)
if strRet == "NG":
    sys.stderr.write('STAモード有効設定失敗\n')
    sys.exit(1)

# STAモードSSID
StrCommand = "P04," + "aviato2.4G" + "\n"
device.write(StrCommand)
strRet = get_line(device)
if strRet == "NG":
    sys.stderr.write('STAモードSSID設定失敗\n')
    sys.exit(1)

# STAモードパスワード
StrCommand = "P05," + "aviato@1234$" + "\n"
device.write(StrCommand)
strRet = get_line(device)
if strRet == "NG":
    sys.stderr.write('TAモードパスワード設定失敗\n')
    sys.exit(1)


# Gコードモードに変更
device.write(chr(0x11))
device.close()

sys.exit(0)