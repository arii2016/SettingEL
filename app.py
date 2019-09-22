# coding: UTF-8

import sys, os, time
import serial
from serial.tools import list_ports
import convert
class Color:
    RED       = '\033[1;31m'
    GREEN     = '\033[1;32m'
    END       = '\033[0m'

def get_line(device):
    rx_buffer = ""
    while True:
        chars = device.read()
        if chars == "\n":
            break
        rx_buffer += chars
    return rx_buffer

# STA設定
def set_sta():
    # COM接続
    try:
        device = serial.Serial(SERIAL_PORT, 921600, timeout=1, writeTimeout=20)
    except:
        sys.stderr.write('USB connect err\n')
        return False

    # コマンドモードに変更
    device.write(chr(0x13))

    # STAモード有効
    StrCommand = "P03," + "true" + "\n"
    device.write(StrCommand)
    strRet = get_line(device)
    if strRet == "NG":
        sys.stderr.write('STA set enable err\n')
        return False

    # STAモードSSID
    StrCommand = "P04," + "aviato2.4G" + "\n"
    device.write(StrCommand)
    strRet = get_line(device)
    if strRet == "NG":
        sys.stderr.write('STA set ssid err\n')
        return False

    # STAモードパスワード
    StrCommand = "P05," + "aviato@1234$" + "\n"
    device.write(StrCommand)
    strRet = get_line(device)
    if strRet == "NG":
        sys.stderr.write('STA set pw err\n')
        return False

    # Gコードモードに変更
    device.write(chr(0x11))
    device.close()

    return True


# STM書き込み
def smt_write():
    mot_path = "./data/EtcherGrbl_v1.0.5.mot"

    # motファイルからデータ抽出
    (addr, data, start_addr) = convert.analyze_mot_file(mot_path)
    # データレコード再構成
    (addr, data) = convert.reconstruct_records(addr, data)
    # 書き込み予定領域のセクター番号を取得
    sectors = convert.make_erase_page_list(addr, data)

    # COM接続
    try:
        device = serial.Serial(SERIAL_PORT, 921600, timeout=1, writeTimeout=20)
    except:
        sys.stderr.write('USB connect err\n')
        return False

    # コマンドモードに変更
    device.write(chr(0x13))

    # セクタ数、データー数、バージョンを送付
    StrCommand = "U01," + str(len(sectors)) + "," + str(len(addr)) + ",V110\n"
    device.write(StrCommand)
    # 戻り値確認
    if get_line(device) == "NG":
        sys.stderr.write('STM write err 1\n')
        return False

    # セクタ送付
    for i in range(len(sectors)):
        device.write(str(sectors[i]) + "\n")
    # データー送付
    for i in range(len(addr)):
        StrCommand = str(addr[i]) + "," + str(len(data[i])) + "\n"
        device.write(StrCommand)
        device.write(data[i])
    # 戻り値確認
    if get_line(device) == "NG":
        sys.stderr.write('STM write err 2\n')
        return False

    # ファーム書き込み実行
    device.write("U02\n")
    # 戻り値確認
    if get_line(device) == "NG":
        sys.stderr.write('STM write err 3\n')
        return False

    # Gコードモードに変更
    device.write(chr(0x11))
    device.close()
    return True

# ESP書き込み
def esp_write():
    bin_path = "./data/etcherlaser_v1.0.5.bin"

    f = open(bin_path, mode='rb')
    data = f.read()
    f.close()

    # COM接続
    try:
        device = serial.Serial(SERIAL_PORT, 921600, timeout=1, writeTimeout=20)
    except:
        sys.stderr.write('USB connect err\n')
        return False

    # コマンドモードに変更
    device.write(chr(0x13))

    # セクタ数、データー数、バージョンを送付
    StrCommand = "U11," + str(len(data)) + "\n"
    device.write(StrCommand)
    # 戻り値確認
    if get_line(device) == "NG":
        sys.stderr.write('ESP write err 1\n')
        return False

    # データ送付
    device.write(data)
    if get_line(device) == "NG":
        sys.stderr.write('ESP write err 2\n')
        return False

    # ファーム書き込み実行
    device.write("U12\n")
    # 戻り値確認
    if get_line(device) == "NG":
        sys.stderr.write('ESP write err 3\n')
        return False

    # Gコードモードに変更
    device.write(chr(0x11))
    device.close()
    return True

# 再起動
def restart():
    device = serial.Serial(SERIAL_PORT, 921600, timeout=1, writeTimeout=1)
    # コマンドモードに変更
    device.write(chr(0x13))

    device.write("S01\n")
    device.close()


# ポート番号を取得する##################################
if os.name == 'nt':
    matched_ports = list_ports.grep("USB Serial Port ")
elif os.name == 'posix':
    if sys.platform == "linux" or sys.platform == "linux2":
        matched_ports = list_ports.grep("ttyUSB")
    elif sys.platform == "darwin":
        matched_ports = list_ports.grep("cu.usbserial-")
for match_tuple in matched_ports:
    SERIAL_PORT = match_tuple[0]
    break
#####################################################

# STA設定
sys.stdout.write('STA setting\n')
if set_sta() == False:
    sys.stderr.write(Color.RED + "NG" + Color.END + "\n")
    sys.exit(1)

# STMアップデート
sys.stdout.write('STM update\n')
if smt_write() == False:
    sys.stderr.write(Color.RED + "NG" + Color.END + "\n")
    sys.exit(1)

# ESPアップデート
sys.stdout.write('ESP update\n')
if esp_write() == False:
    sys.stderr.write(Color.RED + "NG" + Color.END + "\n")
    sys.exit(1)

# 再起動
restart()

sys.stdout.write(Color.GREEN + "OK" + Color.END + "\n")
sys.exit(0)
