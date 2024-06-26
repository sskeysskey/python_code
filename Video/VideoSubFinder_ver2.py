import cv2
import numpy as np
import pytesseract
from pytesseract import Output
import os
import tkinter as tk
from tkinter import filedialog
from difflib import SequenceMatcher
import hashlib

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return thresh

def image_hash(image):
    return hashlib.md5(image).hexdigest()

def extract_subtitle_frames(video_path, output_folder, roi):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    frame_idx = 0
    prev_hash = ""
    start_time = None
    subtitle_roi = None
    recent_hashes = set()
    MIN_TEXT_LENGTH = 10
    MIN_FRAMES_BETWEEN_SUBTITLES = int(fps * 0.5)  # 至少0.5秒间隔

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
            current_hash = image_hash(processed_frame)

            if current_hash not in recent_hashes:
                if prev_hash and frame_idx - last_subtitle_frame >= MIN_FRAMES_BETWEEN_SUBTITLES:
                    save_subtitle(output_folder, start_time, current_time, subtitle_roi)

                start_time = current_time
                subtitle_roi = cropped_frame.copy()
                prev_hash = current_hash
                last_subtitle_frame = frame_idx
                recent_hashes.add(current_hash)
            elif prev_hash and frame_idx - last_subtitle_frame >= MIN_FRAMES_BETWEEN_SUBTITLES:
                save_subtitle(output_folder, start_time, current_time, subtitle_roi)
                prev_hash = ""
                start_time = None
                subtitle_roi = None
                last_subtitle_frame = frame_idx

        frame_idx += 1

    if prev_hash and start_time is not None:
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

video_path = '/Users/yanzhang/Downloads/RPReplay_Final1719361160.mov'
output_folder = '/Users/yanzhang/Downloads/'
roi = (0, 758, 1080, 345)  # 替换为实际的ROI坐标和尺寸
extract_subtitle_frames(video_path, output_folder, roi)