import cv2
import numpy as np
import pytesseract
from pytesseract import Output
import os
import sys
import tkinter as tk
from tkinter import filedialog
from difflib import SequenceMatcher

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return thresh

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def extract_subtitle_frames(video_path, output_folder, roi):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    frame_idx = 0
    prev_text = ""
    start_time = None
    subtitle_roi = None
    recent_texts = []
    MAX_RECENT = 9
    SIMILARITY_THRESHOLD = 0.88
    MIN_TEXT_LENGTH = 12
    MIN_FRAMES_BETWEEN_SUBTITLES = int(fps * 1.5)  # 至少1秒间隔

    last_subtitle_frame = -MIN_FRAMES_BETWEEN_SUBTITLES

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        x, y, w, h = roi
        cropped_frame = frame[y:y+h, x:x+w]

        processed_frame = preprocess_image(cropped_frame)

        d = pytesseract.image_to_data(processed_frame, output_type=Output.DICT)
        text = " ".join([d['text'][i] for i in range(len(d['text'])) if int(d['conf'][i]) > 75]).strip()

        current_time = frame_idx / fps

        if len(text) >= MIN_TEXT_LENGTH:
            recent_texts.append(text)
            if len(recent_texts) > MAX_RECENT:
                recent_texts.pop(0)

            most_common_text = max(set(recent_texts), key=recent_texts.count) if recent_texts else ""

            if (similar(most_common_text, prev_text) < SIMILARITY_THRESHOLD and 
                frame_idx - last_subtitle_frame >= MIN_FRAMES_BETWEEN_SUBTITLES):
                if prev_text and start_time is not None:
                    save_subtitle(output_folder, start_time, current_time, subtitle_roi)

                start_time = current_time
                subtitle_roi = cropped_frame.copy()
                prev_text = most_common_text
                last_subtitle_frame = frame_idx
        elif prev_text and frame_idx - last_subtitle_frame >= MIN_FRAMES_BETWEEN_SUBTITLES:
            save_subtitle(output_folder, start_time, current_time, subtitle_roi)
            prev_text = ""
            start_time = None
            subtitle_roi = None
            last_subtitle_frame = frame_idx

        frame_idx += 1

    if prev_text and start_time is not None:
        save_subtitle(output_folder, start_time, current_time, subtitle_roi)

    cap.release()
    cv2.destroyAllWindows()

def save_subtitle(output_folder, start_time, end_time, roi_image):
    start_time_str = format_time(start_time)
    end_time_str = format_time(end_time)
    output_filename = os.path.join(output_folder, f"{start_time_str}_{end_time_str}.png")
    cv2.imwrite(output_filename, roi_image)

def format_time(time):
    hours = int(time // 3600)
    minutes = int((time % 3600) // 60)
    seconds = int(time % 60)
    milliseconds = int((time % 1) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

# 初始化Tkinter，不显示主窗口
root = tk.Tk()
root.withdraw()

# 弹出文件选择对话框，选择源文件
video_path = filedialog.askopenfilename(
    title='选择要处理的文件',
    filetypes=[('Text files', '*.txt'), ('All files', '*.*')]
)

# 用户没有选择文件则退出
if not video_path:
    print('没有选择文件。')
    sys.exit()

output_folder = '/Users/yanzhang/Downloads/'
roi = (0, 1182, 1080, 281)  # 替换为实际的ROI坐标和尺寸
extract_subtitle_frames(video_path, output_folder, roi)