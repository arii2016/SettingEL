# coding: UTF-8

import sys, os, time
import serial
from serial.tools import list_ports
import convert
import Tkinter
import threading

def get_line(device, time_out=1.0):
    rx_buffer = ""
    start_time = time.time()
    while True:
        if (time.time() - start_time) > time_out:
            return None
        chars = device.read()
        if chars == "\n":
            break
        rx_buffer += chars
    return rx_buffer

def open_usb():
    # ポート番号を取得する
    SERIAL_PORT = ""

    if sys.platform == "linux" or sys.platform == "linux2":
        matched_ports = list_ports.grep("ttyUSB")
    elif sys.platform == "darwin":
        matched_ports = list_ports.grep("cu.usbserial-")

    for match_tuple in matched_ports:
        SERIAL_PORT = match_tuple[0]
        break

    if SERIAL_PORT == "":
        return None

    try:
        device = serial.Serial(SERIAL_PORT, 921600, timeout=1, writeTimeout=30)
    except:
        return None

    # コマンドモードに変更
    device.write(chr(0x13))

    return device

def set_sta_thread():
    Bt_SetSta.config(state="disable")
    Bt_ClearSta.config(state="disable")
    Bt_Update.config(state="disable")

    set_sta()

    lock.release()
    Bt_SetSta.config(state="normal")
    Bt_ClearSta.config(state="normal")
    Bt_Update.config(state="normal")

# STA設定
def set_sta():
    # COM接続
    device = open_usb()
    if device is None:
        sys.stderr.write('USB connect err\n')
        return False

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

    device.close()
    return True

def clear_sta_thread():
    Bt_SetSta.config(state="disable")
    Bt_ClearSta.config(state="disable")
    Bt_Update.config(state="disable")

    clear_sta()

    lock.release()
    Bt_SetSta.config(state="normal")
    Bt_ClearSta.config(state="normal")
    Bt_Update.config(state="normal")

# STAクリア
def clear_sta():
    # COM接続
    device = open_usb()
    if device is None:
        sys.stderr.write('USB connect err\n')
        return False

    # STAモード無効
    StrCommand = "P03," + "false" + "\n"
    device.write(StrCommand)
    strRet = get_line(device)
    if strRet == "NG":
        sys.stderr.write('STA set enable err\n')
        return False

    # STAモードSSID
    StrCommand = "P04," + "null" + "\n"
    device.write(StrCommand)
    strRet = get_line(device)
    if strRet == "NG":
        sys.stderr.write('STA set ssid err\n')
        return False

    # STAモードパスワード
    StrCommand = "P05," + "null" + "\n"
    device.write(StrCommand)
    strRet = get_line(device)
    if strRet == "NG":
        sys.stderr.write('STA set pw err\n')
        return False

    device.close()
    return True

# アップデート
def update_thread():
    Bt_SetSta.config(state="disable")
    Bt_ClearSta.config(state="disable")
    Bt_Update.config(state="disable")

    update_exec()

    lock.release()
    Bt_SetSta.config(state="normal")
    Bt_ClearSta.config(state="normal")
    Bt_Update.config(state="normal")


def update_exec():
    # STMアップデート
    if smt_write() == False:
        return

    # ESPアップデート
    if esp_write() == False:
        return

    # 再起動
    restart()

# STM書き込み
def smt_write():
    mot_path = HOME + "SettingEL/data/EtcherGrbl_v1.1.0.mot"

    # motファイルからデータ抽出
    (addr, data, start_addr) = convert.analyze_mot_file(mot_path)
    # データレコード再構成
    (addr, data) = convert.reconstruct_records(addr, data)
    # 書き込み予定領域のセクター番号を取得
    sectors = convert.make_erase_page_list(addr, data)

    # COM接続
    device = open_usb()
    if device is None:
        sys.stderr.write('USB connect err\n')
        return False

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
    if get_line(device, 15.0) == "NG":
        sys.stderr.write('STM write err 2\n')
        return False

    # ファーム書き込み実行
    device.write("U02\n")
    # 戻り値確認
    if get_line(device, 15.0) == "NG":
        sys.stderr.write('STM write err 3\n')
        return False

    device.close()
    return True

# ESP書き込み
def esp_write():
    bin_path = HOME + "SettingEL/data/etcherlaser_v1.1.0.bin"

    f = open(bin_path, mode='rb')
    data = f.read()
    f.close()

    # COM接続
    device = open_usb()
    if device is None:
        sys.stderr.write('USB connect err\n')
        return False

    # セクタ数、データー数、バージョンを送付
    StrCommand = "U11," + str(len(data)) + "\n"
    device.write(StrCommand)
    # 戻り値確認
    if get_line(device) == "NG":
        sys.stderr.write('ESP write err 1\n')
        return False

    # データ送付
    device.write(data)
    if get_line(device, 15.0) == "NG":
        sys.stderr.write('ESP write err 2\n')
        return False

    # ファーム書き込み実行
    device.write("U12\n")
    # 戻り値確認
    if get_line(device, 15.0) == "NG":
        sys.stderr.write('ESP write err 3\n')
        return False

    device.close()
    return True

# 再起動
def restart():
    # COM接続
    device = open_usb()
    if device is None:
        sys.stderr.write('USB connect err\n')
        return False

    device.write("S01\n")
    device.close()

def set_sta_click():
    if lock.acquire(False):
        th = threading.Thread(target=set_sta_thread)
        th.start()

def clear_sta_click():
    if lock.acquire(False):
        th = threading.Thread(target=clear_sta_thread)
        th.start()

def update_click():
    if lock.acquire(False):
        th = threading.Thread(target=update_thread)
        th.start()


if sys.platform == "linux" or sys.platform == "linux2":
    HOME = "/home/pi/Src/"
elif sys.platform == "darwin":
    HOME = "/Users/yoshiya/Src/workspace/"

lock = threading.Lock()

root = Tkinter.Tk()
root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))

Fr_1 = Tkinter.Frame(root)
Fr_1.pack(side='top', expand=True)

Bt_SetSta = Tkinter.Button(Fr_1, text='Wifi設定', width=5, height=3, font=("", 24), command=set_sta_click, state="normal")
Bt_SetSta.pack(side='left', expand=True)

Bt_ClearSta = Tkinter.Button(Fr_1, text='Wifi削除', width=5, height=3, font=("", 24), command=clear_sta_click, state="normal")
Bt_ClearSta.pack(side='left', expand=True)

Fr_2 = Tkinter.Frame(root)
Fr_2.pack(side='top', expand=True)

Bt_Update = Tkinter.Button(Fr_2, text='アップデート', width=5, height=3, font=("", 24), command=update_click, state="normal")
Bt_Update.pack(side='left', expand=True)

root.mainloop()
