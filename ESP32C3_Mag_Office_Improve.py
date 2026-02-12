import time
import queue
import win_magnification as mag
import win32api
from ctypes import windll
import keyboard

# --- Setup DPI awareness ---
user32 = windll.user32
user32.SetProcessDPIAware()

# --- Screen dimensions ---
x_screen = win32api.GetSystemMetrics(0)
y_screen = win32api.GetSystemMetrics(1)

# --- Initialize magnification ---
mag.initialize()
k_mag = 2
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
        step_delta_mag = 0.05
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
        step_delta_mag = -0.05
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

while True:
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