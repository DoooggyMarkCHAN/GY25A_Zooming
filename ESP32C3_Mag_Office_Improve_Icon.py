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
    # --- Setup DPI awareness ---
    user32 = windll.user32
    user32.SetProcessDPIAware()

    # --- Screen dimensions ---
    x_screen = win32api.GetSystemMetrics(0)
    y_screen = win32api.GetSystemMetrics(1)

    # --- Initialize magnification ---
    mag.initialize()
    is_zoom_in = False

    # --- Queue for commands ---
    command_queue = queue.Queue()

    # --- Hotkey callbacks (only enqueue commands) ---
    def request_zoom_in():
        command_queue.put("zoom_in")

    def request_zoom_out():
        command_queue.put("zoom_out")

    def request_exit():
        command_queue.put("exit")

    keyboard.add_hotkey('ctrl+alt+shift+up', request_zoom_in)
    keyboard.add_hotkey('ctrl+alt+shift+down', request_zoom_out)
    keyboard.add_hotkey('esc', request_exit)

    # --- Zoom logic functions (executed in main thread) ---
    def zoom_in():
        global is_zoom_in
        while mag.get_fullscreen_transform()[0] < k_mag:
            step_delta_mag = 0.1
            k_mag_temp = round(mag.get_fullscreen_transform()[0] + step_delta_mag, 3)
            w_widget = round(x_screen / k_mag_temp)
            h_widget = round(y_screen / k_mag_temp)

            x_cursor, y_cursor = win32api.GetCursorPos()

            x_widget_center = min(max(x_cursor, w_widget / 2), x_screen - w_widget / 2)
            y_widget_center = min(max(y_cursor, h_widget / 2), y_screen - h_widget / 2)

            mag.set_fullscreen_transform(
                k_mag_temp,
                (round(x_widget_center - w_widget / 2), round(y_widget_center - h_widget / 2))
            )
            time.sleep(0.01)
        is_zoom_in = True

    def zoom_out():
        global is_zoom_in
        while mag.get_fullscreen_transform()[0] > 1:
            step_delta_mag = -0.1
            k_mag_temp = round(mag.get_fullscreen_transform()[0] + step_delta_mag, 3)
            w_widget = round(x_screen / k_mag_temp)
            h_widget = round(y_screen / k_mag_temp)

            x_cursor, y_cursor = win32api.GetCursorPos()

            x_widget_center = min(max(x_cursor, w_widget / 2), x_screen - w_widget / 2)
            y_widget_center = min(max(y_cursor, h_widget / 2), y_screen - h_widget / 2)

            mag.set_fullscreen_transform(
                k_mag_temp,
                (round(x_widget_center - w_widget / 2), round(y_widget_center - h_widget / 2))
            )
            time.sleep(0.01)
        is_zoom_in = False

    def follow_cursor():
        """Adjust zoom window so it follows cursor when zoomed in."""
        k_mag_real = mag.get_fullscreen_transform()[0]
        if k_mag_real > 1:
            offset_data = mag.get_fullscreen_transform()[1]
            w_widget = round(x_screen / k_mag_real)
            h_widget = round(y_screen / k_mag_real)

            x_cursor, y_cursor = win32api.GetCursorPos()
            x_offset, y_offset = offset_data

            delta_x_cursor = x_cursor - (x_offset + w_widget / 2)
            delta_y_cursor = y_cursor - (y_offset + h_widget / 2)

            # Horizontal panning
            if w_widget * 0.1 < x_cursor < (x_screen - w_widget * 0.1):
                if abs(delta_x_cursor) > 0.4 * w_widget:
                    if delta_x_cursor > 0:
                        x_offset = round(x_offset + delta_x_cursor - 0.4 * w_widget)
                    else:
                        x_offset = round(x_offset + delta_x_cursor + 0.4 * w_widget)
            elif x_cursor < w_widget * 0.1:
                x_offset = 0
            elif x_cursor > (x_screen - w_widget * 0.1):
                x_offset = x_screen - w_widget

            # Vertical panning
            if h_widget * 0.1 < y_cursor < (y_screen - h_widget * 0.1):
                if abs(delta_y_cursor) > 0.4 * h_widget:
                    if delta_y_cursor > 0:
                        y_offset = round(y_offset + delta_y_cursor - 0.4 * h_widget)
                    else:
                        y_offset = round(y_offset + delta_y_cursor + 0.4 * h_widget)
            elif y_cursor < h_widget * 0.1:
                y_offset = 0
            elif y_cursor > (y_screen - h_widget * 0.1):
                y_offset = y_screen - h_widget

            mag.set_fullscreen_transform(k_mag_real, (x_offset, y_offset))

    # --- Main loop (single thread, safe for Magnification API) ---
    print("Press Ctrl+Alt+Shift+Up to zoom in, Ctrl+Alt+Shift+Down to zoom out, Esc to quit.")

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
        # elif cmd == "exit":
        #     break

        # Always update cursor tracking when zoomed in
        follow_cursor()


# Run the icon in a separate thread, so it doesn’t block

thread_icon = threading.Thread(target=icon.run)
thread_zoom = threading.Thread(target=func_magniflow)

thread_icon.start()
thread_zoom.start()

thread_icon.join()
thread_zoom.join()