
import json
import time
import pyautogui
from PIL import ImageGrab, ImageChops
import os
from PIL import Image

def compare_images(img1_path, threshold=10):
    """Compare current screen with img1_path, return True if similar."""
    img1 = Image.open(img1_path).convert('RGB')
    img2 = ImageGrab.grab().convert('RGB')
    diff = ImageChops.difference(img1, img2)
    # For RGB, getdata() returns tuples, so sum all channel values
    diff_sum = sum(sum(pixel) for pixel in diff.getdata())
    return diff_sum < threshold

def monitor_screen_and_click_if_needed(screenshot_path, monitor_time=120, check_interval=2, similarity_threshold=10):
    """
    Monitor the screen for up to monitor_time seconds.
    If the screen is not similar to the screenshot, click center and keep monitoring.
    If the screen becomes similar, return.
    """
    print(f"开始监控屏幕，参考图像: {screenshot_path}")
    start = time.time()
    screen_width, screen_height = pyautogui.size()
    center_x, center_y = screen_width // 2, screen_height // 2
    while time.time() - start < monitor_time:
        similar = compare_images(screenshot_path, threshold=similarity_threshold)
        if similar:
            print("屏幕与截图一致，继续后续操作。")
            return
        else:
            print("屏幕与截图不一致，点击屏幕中央并继续等待...")
            pyautogui.click(center_x, center_y)
        time.sleep(check_interval)
    print("监控超时，继续执行后续操作。")


def load_macro(file_path):
    """读取宏文件"""
    with open(file_path, "r") as f:
        events = json.load(f)
    return events




def normalize_button(button_str):
    # Convert 'Button.left' to 'left', etc.
    if button_str.startswith('Button.'):
        return button_str.split('.')[-1]
    return button_str

def execute_event(event, click_count=None):
    """执行单个事件"""

    event_type = event["type"]
    data = event["data"]

    if event_type == "mouse_click":
        if click_count is not None:
            print(f"Mouse click #{click_count}: {data}")
        button = normalize_button(data["button"])
        pyautogui.click(data["x"], data["y"], button=button)

    elif event_type == "mouse_move":
        pyautogui.moveTo(data["x"], data["y"])

    elif event_type == "key_press":
        pyautogui.press(data["key"])




def play_macro(events):
    """按时间顺序执行，遇到截图事件则监控屏幕。"""

    last_time = 0
    click_count = 0
    screenshot_events = []

    # 预处理所有截图事件，记录其时间和路径
    for idx, event in enumerate(events):
        if event["type"] == "screenshot":
            screenshot_events.append((idx, event["time"], event["data"]["file"]))

    i = 0
    while i < len(events):
        event = events[i]
        delay = event["time"] - last_time
        time.sleep(max(delay, 0))

        # 检查是否为截图事件
        if event["type"] == "screenshot":
            screenshot_path = event["data"]["file"]
            # 监控前后2分钟
            monitor_start = event["time"] - 120
            monitor_end = event["time"] + 120
            # 跳过前2分钟内的事件
            j = i - 1
            while j >= 0 and events[j]["time"] >= monitor_start:
                j -= 1
            # 监控
            monitor_screen_and_click_if_needed(screenshot_path, monitor_time=120, check_interval=2, similarity_threshold=10)
            # 跳过后2分钟内的事件
            k = i + 1
            while k < len(events) and events[k]["time"] <= monitor_end:
                k += 1
            i = k
            last_time = event["time"]
            continue

        if event["type"] == "mouse_click":
            click_count += 1
            execute_event(event, click_count)
        else:
            execute_event(event)
        last_time = event["time"]
        i += 1


if __name__ == "__main__":

    # 读取主目录 records 文件夹下的 record.json
    MAIN_DIR = os.path.dirname(os.path.dirname(__file__))
    RECORDS_DIR = os.path.join(MAIN_DIR, "records")
    macro_file = os.path.join(RECORDS_DIR, "record.json")
    events = load_macro(macro_file)

    while True:
        print("3秒后开始执行...")
        time.sleep(3)
        play_macro(events)
        print("本轮执行完成，3秒后自动重启...")
        time.sleep(3)