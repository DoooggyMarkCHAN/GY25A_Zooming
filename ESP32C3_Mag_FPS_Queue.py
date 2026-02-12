import time
import queue
import win_magnification as mag
import win32api
from ctypes import windll
import keyboard
import pystray
from PIL import Image, ImageDraw
import threading

isIconClosed = False
k_mag = 2


# Function to create a simple icon image
def create_image():
    # Create a blank image
    image = Image.new('RGB', (64, 64), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    # Draw a blue circle
    draw.ellipse((16, 16, 48, 48), fill=(0, 0, 255))
    return image


# Action when clicking "Quit"
def on_quit(icon, item):
    global isIconClosed
    icon.stop()
    isIconClosed = True


def set_value(icon, item):
    global k_mag
    if item.text == "Set 1.5X":
        k_mag = 1.5
    elif item.text == "Set 2.0X":
        k_mag = 2.0
    elif item.text == "Set 3.0X":
        k_mag = 3.0
    elif item.text == "Set 4.0X":
        k_mag = 4.0


# Create the tray icon
icon = pystray.Icon(
    "test_icon",
    create_image(),
    "Magniflow",
    menu=pystray.Menu(
        pystray.MenuItem("Set 1.5X", set_value),
        pystray.MenuItem("Set 2.0X", set_value),
        pystray.MenuItem("Set 3.0X", set_value),
        pystray.MenuItem("Set 4.0X", set_value),
        pystray.MenuItem("Quit", on_quit),
    )
)


def func_magniflow():
    # Make program aware of DPI scaling
    user32 = windll.user32
    user32.SetProcessDPIAware()

    x_screen = win32api.GetSystemMetrics(0)
    y_screen = win32api.GetSystemMetrics(1)

    mag.initialize()

    # --- Queue for commands ---
    command_queue = queue.Queue()

    # --- Hotkey callbacks (only enqueue commands) ---
    def request_zoom_in():
        command_queue.put("zoom_in")

    def request_zoom_out():
        command_queue.put("zoom_out")

    keyboard.add_hotkey('ctrl+alt+shift+up', request_zoom_in)
    keyboard.add_hotkey('ctrl+alt+shift+down', request_zoom_out)

    def zoom_in():
        while mag.get_fullscreen_transform()[0] < k_mag:
            w_widget = x_screen / (mag.get_fullscreen_transform()[0] + 0.1)
            h_widget = y_screen / (mag.get_fullscreen_transform()[0] + 0.1)
            mag.set_fullscreen_transform(round(mag.get_fullscreen_transform()[0] + 0.1, 1),
                                         (round(x_screen / 2 - w_widget / 2), round(y_screen / 2 - h_widget / 2)))
            time.sleep(0.01)

    def zoom_out():
        while mag.get_fullscreen_transform()[0] > 1:
            w_widget = x_screen / (mag.get_fullscreen_transform()[0] - 0.1)
            h_widget = y_screen / (mag.get_fullscreen_transform()[0] - 0.1)
            mag.set_fullscreen_transform(round(mag.get_fullscreen_transform()[0] - 0.1, 1),
                                         (round(x_screen / 2 - w_widget / 2), round(y_screen / 2 - h_widget / 2)))
            time.sleep(0.01)

    while not isIconClosed:
        # Process queued commands
        try:
            cmd = command_queue.get(timeout=0.01)
        except queue.Empty:
            cmd = None

        if cmd == "zoom_in":
            zoom_in()
        elif cmd == "zoom_out":
            zoom_out()


# Run the icon in a separate thread so it doesn’t block

thread_icon = threading.Thread(target=icon.run)
thread_zoom = threading.Thread(target=func_magniflow)

thread_icon.start()
thread_zoom.start()

thread_icon.join()
thread_zoom.join()
