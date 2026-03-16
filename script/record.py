
from pynput import mouse, keyboard
import time
import json
from PIL import ImageGrab, ImageChops
import os

events = []
start_time = time.time()

# Screenshot save directory in main project folder
MAIN_DIR = os.path.dirname(os.path.dirname(__file__))
SCREENSHOT_DIR = os.path.join(MAIN_DIR, "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

RECORDS_DIR = os.path.join(MAIN_DIR, "records")
os.makedirs(RECORDS_DIR, exist_ok=True)
record_path = os.path.join(RECORDS_DIR, "record.json")

def record_event(event_type, data):
    t = time.time() - start_time
    events.append({
        "time": t,
        "type": event_type,
        "data": data
    })
    print(events[-1])

def take_screenshot():
    t = time.time() - start_time
    filename = f"screenshot_{t:.2f}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    # Capture the screen
    img = ImageGrab.grab()
    img.save(filepath)
    print(f"Screenshot saved: {filepath}")
    return filepath

def compare_images(img1_path, img2_path, threshold=10):
    img1 = ImageGrab.open(img1_path).convert('RGB')
    img2 = ImageGrab.open(img2_path).convert('RGB')
    diff = ImageChops.difference(img1, img2)
    # Calculate sum of differences
    diff_sum = sum(diff.getdata())
    return diff_sum < threshold

def wait_for_task_completion(screenshot_folder, wait_time=30, check_interval=2, similarity_threshold=10):
    """
    Wait for task completion by checking screen similarity.
    If screen is similar to reference screenshot, continue.
    If not, click and keep waiting.
    """
    reference_imgs = [os.path.join(screenshot_folder, f) for f in os.listdir(screenshot_folder) if f.endswith('.png')]
    if not reference_imgs:
        print("No reference screenshots found.")
        return
    reference_img = reference_imgs[-1]  # Use last screenshot as reference
    start = time.time()
    while time.time() - start < wait_time:
        current_path = take_screenshot()
        similar = compare_images(reference_img, current_path, threshold=similarity_threshold)
        if similar:
            print("Screen is similar, task likely completed.")
            break
        else:
            print("Screen not similar, clicking and waiting...")
            # Simulate click (user can customize)
            # pyautogui.click(x, y)  # Uncomment and set coordinates if needed
        time.sleep(check_interval)
    print("Wait loop finished.")

# 鼠标点击
def on_click(x, y, button, pressed):
    record_event(
        "mouse_click",
        {
            "x": x,
            "y": y,
            "button": str(button),
            "pressed": pressed
        }
    )

# 键盘按下
def on_press(key):
    try:
        k = key.char
    except:
        k = str(key)


    # If X is pressed, take screenshot
    if k == 'x' or k == 'X':
        path = take_screenshot()
        record_event(
            "screenshot",
            {"file": path}
        )
    # If W is pressed, start wait-for-task-completion logic
    elif k == 'w' or k == 'W':
        print("开始检测任务完成状态...")
        wait_for_task_completion(SCREENSHOT_DIR)
    else:
        record_event(
            "key_press",
            {"key": k}
        )

# ESC停止录制
def on_release(key):
    if key == keyboard.Key.esc:
        print("停止录制")
        return False

mouse_listener = mouse.Listener(on_click=on_click)
keyboard_listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release
)

mouse_listener.start()
keyboard_listener.start()

keyboard_listener.join()

# 保存文件到主目录的 records 文件夹

with open(record_path, "w") as f:
    json.dump(events, f, indent=2)

print(f"保存完成，文件路径: {record_path}")