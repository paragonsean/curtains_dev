import base64
import ctypes
import os
import pathlib
import sys
import time
from ctypes import wintypes
from functools import wraps
from io import BytesIO

import mss
import mss.windows
import psutil
import win32.lib.win32con as win32con
from win32com.client import Dispatch
import pythoncom
import win32api
import win32gui
import win32ui
from PIL import Image
from pyinjector import inject

mss.windows.CAPTUREBLT = 0

if getattr(sys, 'frozen', False):
    BASEDIR = sys._MEIPASS
else:
    BASEDIR = os.path.dirname(os.path.abspath(__file__))
    BASEDIR = str((pathlib.Path(BASEDIR)).parent.absolute())

enumWindows = ctypes.windll.user32.EnumWindows
enumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.POINTER(ctypes.c_int))
getWindowText = ctypes.windll.user32.GetWindowTextW
getWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f'Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds')
        return result

    return timeit_wrapper


def all_hwnds():
    hwnd_list = []

    def foreach_window(hwnd, lParam):
        if ctypes.windll.user32.IsWindowVisible(hwnd) != 0:
            is_cloaked = ctypes.c_int(0)
            ctypes.WinDLL("dwmapi").DwmGetWindowAttribute(hwnd, 14, ctypes.byref(is_cloaked), ctypes.sizeof(is_cloaked))
            if is_cloaked.value == 0:
                hwnd_list.append(hwnd)

        return True

    enumWindows(enumWindowsProc(foreach_window), 0)

    return hwnd_list


def pid_of_hwnd(hwnd: int):
    lpdw_process_id = ctypes.c_ulong()
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(lpdw_process_id))
    process_id = lpdw_process_id.value

    return process_id


def curtains_exe_path():
    pid = os.getpid()
    p_name = process_name_of_pid(pid)
    exec_path = executable_path(p_name, pid)
    return exec_path


def add_to_autostart() -> None:
    if getattr(sys, 'frozen', False):
        shell = Dispatch('WScript.Shell', pythoncom.CoInitialize())
        path = os.getenv('APPDATA')
        path = path + r'\Microsoft\Windows\Start Menu\Programs\Startup\Curtains.lnk'
        print(path)
        shortcut = shell.CreateShortCut(path)
        print(curtains_exe_path())
        shortcut.Targetpath = curtains_exe_path()
        shortcut.save()
    else:
        print('need to run as .exe to add curtains to autostart')


def del_autostart() -> None:
    if check_if_autostart():
        path = os.getenv('APPDATA')
        file = path + r'\Microsoft\Windows\Start Menu\Programs\Startup\Curtains.lnk'
        os.remove(file)


def check_if_autostart() -> None:
    path = os.getenv('APPDATA')
    path = path + r'\Microsoft\Windows\Start Menu\Programs\Startup\Curtains.lnk'
    if os.path.isfile(path):
        return True
    else:
        return False


def process_name_of_pid(pid: int) -> str:
    procname = psutil.Process(pid).name()
    return procname


def executable_path(name: str, pid: int) -> str:
    try:
        if psutil.Process(pid).name() == name:
            return psutil.Process(pid).exe()
    except Exception as e:
        print(e)
        print(f'ERROR finding process path for PID {pid} \n')


def commandline(pid: int) -> str:
    try:
        return psutil.Process(pid).cmdline()
    except Exception as e:
        print(e)
        return None


def username_of_pid(pid: int) -> str:
    uname = psutil.Process(pid).username()
    return uname


def extract_icon(exefilename: str, hwnd: int) -> Image:
    ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
    try:
        large, small = win32gui.ExtractIconEx(exefilename, 0)
    except Exception:
        return None

    if not large:
        return None
    else:
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(hwnd))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_x)
        hdc = hdc.CreateCompatibleDC()
        hdc.SelectObject(hbmp)
        hdc.DrawIcon((0, 0), large[0])
        bmpstr = hbmp.GetBitmapBits(True)
        img = Image.frombuffer('RGBA', (32, 32), bmpstr, 'raw', 'BGRA', 0, 1)
        win32gui.DestroyIcon(small[0])
        win32gui.DestroyIcon(large[0])
        return img


def image2base64(img: Image) -> str:
    buffered = BytesIO()
    img = img.convert('RGBA')
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue())
    buffered.truncate()
    return img_str.decode("utf-8")


@timeit
def hide_windows(pid: int) -> None:
    try:
        inject(pid, (BASEDIR + r"/assets/Hide.dll"))
    except Exception as e:
        pass

    try:
        inject(pid, (BASEDIR + r"/assets/Hide_32bit.dll"))
    except Exception as e:
        pass


@timeit
def unhide_windows(pid: int) -> None:
    try:
        inject(pid, (BASEDIR + r"\assets\Unhide.dll"))
    except Exception as e:
        pass

    try:
        inject(pid, (BASEDIR + r"\assets\Unhide_32bit.dll"))
    except Exception as e:
        pass


def minimize_window(hwnd: int):
    ctypes.windll.user32.CloseWindow(hwnd)


def window_position(hwnd: int):
    rect = wintypes.RECT()
    ff = ctypes.windll.user32.GetWindowRect(hwnd, ctypes.pointer(rect))
    return rect.left, rect.top, rect.right, rect.bottom


def window_to_foreground(hwnd: int, e=None):
    ctypes.windll.user32.ShowWindow(hwnd, 2)
    ctypes.windll.user32.CloseWindow(hwnd)
    ctypes.windll.user32.BringWindowToTop(hwnd)
    ctypes.windll.user32.SwitchToThisWindow(hwnd, True)


def window_minimize(hwnd: int, e=None):
    ctypes.windll.user32.CloseWindow(hwnd)


def window_close(hwnd: int, e=None):
    ctypes.windll.user32.PostMessageA(hwnd, 0x10, 0, 0)


def window_title(hwnd: int) -> str:
    text_len_in_characters = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
    string_buffer = ctypes.create_unicode_buffer(text_len_in_characters + 1)
    ctypes.windll.user32.GetWindowTextW(hwnd, string_buffer, text_len_in_characters + 1)
    result = string_buffer.value
    return result


def rename_window_title(hwnd: int, title: str = "") -> None:
    try:
        ctypes.windll.user32.SetWindowTextW(hwnd, title)
    except Exception as e:
        print(e)
        pass


def check_priviliges(hwnd: int):
    orig_title = window_title(hwnd)
    dummy_title = ''
    if orig_title == '':
        dummy_title = '#123'
    rename_window_title(hwnd, dummy_title)
    if window_title(hwnd) == orig_title:
        return True
    if window_title(hwnd) == dummy_title:
        rename_window_title(hwnd, orig_title)
        return False


def return_screensize() -> (int, int):
    ctypes.windll.user32.SetProcessDPIAware()
    width = ctypes.windll.user32.GetSystemMetrics(0)
    height = ctypes.windll.user32.GetSystemMetrics(1)
    return width, height


def take_screenshot(fraction):
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[-1]
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            width, height = img.size
            img.resize((width // fraction, height // fraction))
            return [img, (width, height)]
    except Exception as e:
        print(e)


def is_black(img: Image):
    return not img.getbbox()


def getFileProperties(fname):
    propNames = ('Comments', 'InternalName', 'ProductName',
                 'CompanyName', 'LegalCopyright', 'ProductVersion',
                 'FileDescription', 'LegalTrademarks', 'PrivateBuild',
                 'FileVersion', 'OriginalFilename', 'SpecialBuild')

    props = {'FixedFileInfo': None, 'StringFileInfo': None, 'FileVersion': None}

    try:
        fixedInfo = win32api.GetFileVersionInfo(fname, '\\')
        props['FixedFileInfo'] = fixedInfo
        props['FileVersion'] = "%d.%d.%d.%d" % (fixedInfo['FileVersionMS'] / 65536,
                                                fixedInfo['FileVersionMS'] % 65536,
                                                fixedInfo['FileVersionLS'] / 65536,
                                                fixedInfo['FileVersionLS'] % 65536)

        lang, codepage = win32api.GetFileVersionInfo(fname, '\\VarFileInfo\\Translation')[0]

        strInfo = {}
        for propName in propNames:
            strInfoPath = u'\\StringFileInfo\\%04X%04X\\%s' % (lang, codepage, propName)
            strInfo[propName] = win32api.GetFileVersionInfo(fname, strInfoPath)

        props['StringFileInfo'] = strInfo
    except:
        pass

    return props
