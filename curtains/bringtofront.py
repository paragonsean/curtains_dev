import time
import psutil
import os
import pygetwindow as gw

waitTime = 15  # Time before activating
appName = "Helium"  # Application to bring to front

def get_helium_windows():
    # Get all windows with the title containing the application name
    return [window for window in gw.getWindowsWithTitle(appName) if appName.lower() in window.title.lower()]

def bring_to_front(windows):
    for window in windows:
        window.minimize()
        time.sleep(1)
        window.restore()
        print(f"{window.title} was brought to the front!")

if __name__ == '__main__':
    windows = get_helium_windows()
    window_count = len(windows)

    if not windows:
        print(appName + " not running")
        print("Open " + appName + "? Y / N")
        inp = input()[0].lower()
        if inp == 'y':
            inp2 = input("How many instances?")
            print("Opening " + appName)
            for _ in range(int(inp2)):
                os.system(f"start {appName}.exe")
            time.sleep(0.5)
            windows = get_helium_windows()  # Recheck windows
            window_count = len(windows)
        else:
            print("Okay, closing...")
            time.sleep(1)
            exit()

    print(appName + " found!")
    print("Windows count: " + str(window_count))

    print("You have " + str(waitTime) + " seconds")
    for i in reversed(range(waitTime)):
        time.sleep(1)
        print(str(i) + "...")

    bring_to_front(windows)

    while True:
        time.sleep(120)
        new_windows = get_helium_windows()
        if len(new_windows) != window_count:
            for _ in range(len(new_windows) - window_count):
                os.system(f"start {appName}.exe")
            window_count = len(new_windows)
            print(f"Opened {appName} again")
            bring_to_front(new_windows)

    print("DONE")
