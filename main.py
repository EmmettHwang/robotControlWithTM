# coding: utf-8
import os
import cv2
import numpy as np
import tensorflow as tf
import time
import serial
import serial.tools.list_ports 
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageFont, ImageDraw, Image
import threading
import configparser
import ctypes  # 윈도우 커서 제어를 위한 라이브러리

# --- 윈도우 커서 상수 설정 ---
IDC_HAND = 32649
IDC_ARROW = 32512
LoadCursor = ctypes.windll.user32.LoadCursorW
SetCursor = ctypes.windll.user32.SetCursor

# --- 1. 설정 및 초기화 UI ---
class AppSetup:
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
        self.config = configparser.ConfigParser()
        self.last_port = self.load_config()
        self.selected_port = None
        self.root = tk.Tk()
        self.root.title("휴머노이드 AI 초기화")
        self.root.geometry("450x280")
        self.center_window(self.root, 450, 280)
        self.show_port_selection()
        self.root.mainloop()

    def load_config(self):
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
            return self.config.get("SETTINGS", "last_port", fallback=None)
        return None

    def save_config(self, port):
        if "SETTINGS" not in self.config: self.config.add_section("SETTINGS")
        self.config.set("SETTINGS", "last_port", port)
        with open(self.config_file, 'w', encoding='utf-8') as f: self.config.write(f)

    def center_window(self, window, w, h):
        ws, hs = window.winfo_screenwidth(), window.winfo_screenheight()
        window.geometry(f'{w}x{h}+{int((ws/2)-(w/2))}+{int((hs/2)-(h/2))}')

    def show_port_selection(self):
        for w in self.root.winfo_children(): w.destroy()
        tk.Label(self.root, text="로봇 연결 포트 선택 (115200)", font=("Malgun Gothic", 12, "bold")).pack(pady=20)
        ports = serial.tools.list_ports.comports()
        display_list = [f"{p.device} - {p.description}" for p in ports]
        self.actual_ports = [p.device for p in ports]
        self.combo = ttk.Combobox(self.root, values=display_list, state="readonly", width=55)
        self.combo.pack(pady=10)
        if self.last_port in self.actual_ports:
            self.combo.current(self.actual_ports.index(self.last_port))
        elif display_list: self.combo.current(0)
        tk.Button(self.root, text="시스템 시작", command=self.start_loading, bg="#28a745", fg="white", width=25).pack(pady=25)

    def start_loading(self):
        idx = self.combo.current()
        if idx == -1: return
        self.selected_port = self.actual_ports[idx]
        self.save_config(self.selected_port)
        for w in self.root.winfo_children(): w.destroy()
        self.status_label = tk.Label(self.root, text="준비 중...", font=("Malgun Gothic", 11, "bold"))
        self.status_label.pack(pady=(50, 5))
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=350, mode="determinate")
        self.progress.pack(pady=10)
        self.detail_label = tk.Label(self.root, text="", fg="gray")
        self.detail_label.pack()
        threading.Thread(target=self.initialization_task, daemon=True).start()

    def update_ui(self, msg, detail, val):
        self.status_label.config(text=msg); self.detail_label.config(text=detail)
        self.progress['value'] = val; self.root.update()

    def initialization_task(self):
        global interpreter, input_details, output_details, class_names, camera, ser
        try:
            self.update_ui("1. 포트 연결 중...", "Serial 115200bps 접속", 15); ser = serial.Serial(self.selected_port, 115200, timeout=1); time.sleep(0.7)
            self.update_ui("2. 모델 로드 중...", "TFLite 신경망 로딩", 40); base_path = os.path.dirname(os.path.abspath(__file__))
            interpreter = tf.lite.Interpreter(model_path=os.path.join(base_path, "model_unquantized.tflite")); interpreter.allocate_tensors()
            input_details, output_details = interpreter.get_input_details(), interpreter.get_output_details(); time.sleep(0.7)
            self.update_ui("3. 엔진 설정 중...", "labels.txt 매핑", 65)
            with open(os.path.join(base_path, "labels.txt"), "r", encoding="utf-8") as f: class_names = [line.strip() for line in f.readlines()]
            time.sleep(0.7)
            self.update_ui("4. 카메라 활성화 중...", "영상 장치 응답 대기", 85); camera = cv2.VideoCapture(0); camera.set(cv2.CAP_PROP_BUFFERSIZE, 1); time.sleep(0.5)
            self.update_ui("준비 완료!", "메인 화면을 실행합니다.", 100); time.sleep(0.8); self.root.destroy()
        except Exception as e: messagebox.showerror("에러", f"실패: {e}"); os._exit(0)

# --- 2. 제어 및 이벤트 함수 ---
btn_exit = [540, 10, 630, 50]
btn_19 = [20, 420, 150, 460]
btn_18 = [160, 420, 290, 460]
btn_17 = [300, 420, 430, 460]
buttons = [btn_exit, btn_19, btn_18, btn_17]

def setHumanoidMotion(motionIndex):
    global ser
    if ser is None or not ser.is_open: return
    packet_buff = [0xff, 0xff, 0x4c, 0x53, 0x00, 0x00, 0x00, 0x00, 0x30, 0x0c, 0x03, motionIndex, 0x00, 100, 0x00]
    for i in range(6, 14): packet_buff[14] = (packet_buff[14] + packet_buff[i]) & 0xFF
    ser.write(bytearray(packet_buff)); ser.flush()

def draw_korean_text(img, text, position, font_size, color):
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil); font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", font_size)
    draw.text(position, text, font=font, fill=color)
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

manual_action, running = 0, True
def on_mouse_event(event, x, y, flags, param):
    global manual_action, running
    # 마우스 이동 시 커서 변경 로직 (Hovering)
    is_over_button = False
    for b in buttons:
        if b[0] < x < b[2] and b[1] < y < b[3]:
            is_over_button = True; break
    
    if is_over_button:
        SetCursor(LoadCursor(0, IDC_HAND)) # 손가락 모양
    else:
        SetCursor(LoadCursor(0, IDC_ARROW)) # 기본 화살표

    # 클릭 이벤트
    if event == cv2.EVENT_LBUTTONDOWN:
        if btn_exit[0] < x < btn_exit[2] and btn_exit[1] < y < btn_exit[3]: running = False
        elif btn_19[0] < x < btn_19[2] and btn_19[1] < y < btn_19[3]: manual_action = 19
        elif btn_18[0] < x < btn_18[2] and btn_18[1] < y < btn_18[3]: manual_action = 18
        elif btn_17[0] < x < btn_17[2] and btn_17[1] < y < btn_17[3]: manual_action = 17

# --- 3. 메인 프로세스 ---
setup = AppSetup()
cv2.namedWindow("Robot AI System")
cv2.setMouseCallback("Robot AI System", on_mouse_event)

is_sequencing, sequence_start_time, current_step, prev_label = False, 0, 0, ""

while running:
    ret, frame = camera.read()
    if not ret: break
    frame = cv2.flip(frame, 1)

    # UI 버튼 그리기
    cv2.rectangle(frame, (btn_exit[0], btn_exit[1]), (btn_exit[2], btn_exit[3]), (0, 0, 180), -1)
    for b, t in zip([btn_19, btn_18, btn_17], ["인사(19)", "손흔들기(18)", "챔피온(17)"]):
        cv2.rectangle(frame, (b[0], b[1]), (b[2], b[3]), (50, 50, 50), -1)
        frame = draw_korean_text(frame, t, (b[0]+12, b[1]+7), 17, (255, 255, 255))
    frame = draw_korean_text(frame, "종료", (btn_exit[0]+18, btn_exit[1]+7), 17, (255, 255, 255))

    # AI 추론 및 제어 (중복 방지 로직 포함)
    img_input = cv2.resize(frame, (224, 224)); img_input = np.expand_dims(img_input, axis=0).astype(np.float32); img_input = (img_input / 127.5) - 1
    interpreter.set_tensor(input_details[0]['index'], img_input); interpreter.invoke()
    prediction = interpreter.get_tensor(output_details[0]['index'])
    index = np.argmax(prediction[0]); label_name = class_names[index][2:].strip(); confidence = prediction[0][index]; current_time = time.time()

    action_to_run = 0
    if manual_action > 0:
        action_to_run, manual_action = manual_action, 0
    elif not is_sequencing and confidence > 0.85 and label_name != prev_label:
        if "사람" in label_name: action_to_run = 19
        elif "로봇" in label_name: action_to_run = 39
        elif "생활용품" in label_name: action_to_run = 84
        prev_label = label_name

    if action_to_run > 0:
        setHumanoidMotion(action_to_run); is_sequencing, current_step, sequence_start_time = True, 1, current_time

    # 시퀀스 관리 (7초 대기 -> 1번 복귀 -> 3초 대기)
    status_msg = "상태: 감지 중"
    if is_sequencing:
        elapsed = current_time - sequence_start_time
        if current_step == 1:
            status_msg = f"동작 중... {int(7-elapsed)}초 뒤 복귀"
            if elapsed >= 7: setHumanoidMotion(1); current_step, sequence_start_time = 2, time.time()
        elif current_step == 2:
            status_msg = f"복귀 중... {int(3-elapsed)}초 뒤 감지"
            if elapsed >= 3: is_sequencing, current_step = False, 0

    frame = draw_korean_text(frame, f"감지: {label_name} ({confidence*100:.1f}%)", (20, 30), 25, (0, 255, 0))
    frame = draw_korean_text(frame, status_msg, (20, 70), 20, (255, 255, 0))
    cv2.imshow("Robot AI System", frame)
    if cv2.waitKey(1) == 27: break

if ser: ser.close()
camera.release(); cv2.destroyAllWindows()