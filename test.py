import cv2
import numpy as np
import pytesseract
from pytesseract import Output
import os
import hashlib

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # 增加对比度和亮度
    alpha = 1.5  # 对比度控制（1.0-3.0）
    beta = 50    # 亮度控制（0-100）
    enhanced = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
    # 使用自适应阈值
    thresh = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return thresh

def image_hash(image):
    return hashlib.md5(image).hexdigest()

def extract_subtitle_frames(video_path, output_folder, roi):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    prev_hash = ""
    start_time = None
    last_change_time = None
    subtitle_roi = None
    recent_hashes = {}
    MIN_TEXT_LENGTH = 10
    MIN_TIME_BETWEEN_SUBTITLES = 0.5  # 至少0.5秒间隔
    TIME_WINDOW = 2.0  # 2秒时间窗口

    last_subtitle_time = -MIN_TIME_BETWEEN_SUBTITLES
    subtitles = []
    subtitle_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

        x, y, w, h = roi
        cropped_frame = frame[y:y+h, x:x+w]

        processed_frame = preprocess_image(cropped_frame)

        d = pytesseract.image_to_data(processed_frame, output_type=Output.DICT)
        text = " ".join([d['text'][i] for i in range(len(d['text'])) if int(d['conf'][i]) > 75]).strip()

        if len(text) >= MIN_TEXT_LENGTH:
            current_hash = image_hash(processed_frame)

            if current_hash not in recent_hashes:
                if prev_hash and current_time - last_subtitle_time >= MIN_TIME_BETWEEN_SUBTITLES:
                    if start_time is not None:
                        # 检查是否在时间窗口内
                        if current_time - start_time > TIME_WINDOW:
                            save_subtitle(output_folder, start_time, last_change_time, subtitle_roi)
                            subtitle_count += 1
                            subtitles.append({
                                'number': subtitle_count,
                                'start': format_time(start_time),
                                'end': format_time(last_change_time)
                            })
                            print(f"Saved subtitle: {format_time(start_time)} - {format_time(last_change_time)}")
                            start_time = current_time
                        else:
                            # 更新结束时间
                            last_change_time = current_time
                    else:
                        start_time = current_time
                    
                    recent_hashes = {}

                last_change_time = current_time
                subtitle_roi = cropped_frame.copy()
                prev_hash = current_hash
                last_subtitle_time = current_time
                recent_hashes[current_hash] = current_time
            else:
                last_change_time = current_time
                recent_hashes[current_hash] = current_time

    # 保存最后一个字幕
    if prev_hash and start_time is not None:
        save_subtitle(output_folder, start_time, last_change_time, subtitle_roi)
        subtitle_count += 1
        subtitles.append({
            'number': subtitle_count,
            'start': format_time(start_time),
            'end': format_time(last_change_time)
        })
        print(f"Saved subtitle: {format_time(start_time)} - {format_time(last_change_time)}")

    cap.release()
    cv2.destroyAllWindows()

    # 写入srt文件
    write_srt_file(output_folder, subtitles)

def save_subtitle(output_folder, start_time, end_time, roi_image):
    start_time_str = format_time(start_time)
    end_time_str = format_time(end_time)
    output_filename = os.path.join(output_folder, f"{start_time_str}_{end_time_str}.png")
    cv2.imwrite(output_filename, roi_image)

def write_srt_file(output_folder, subtitles):
    srt_filename = os.path.join(output_folder, "sub.srt")
    with open(srt_filename, 'w', encoding='utf-8') as f:
        for i, subtitle in enumerate(subtitles, 1):
            f.write(f"{i}\n")
            f.write(f"{subtitle['start']} --> {subtitle['end']}\n")
            f.write("waiting for joint\n\n")

def format_time(time):
    hours = int(time // 3600)
    minutes = int((time % 3600) // 60)
    seconds = int(time % 60)
    milliseconds = int((time % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

video_path = '/Users/yanzhang/Downloads/RPReplay_Final1720051080.mov'
output_folder = '/Users/yanzhang/Movies/Subtitle'
roi = (0, 846, 856, 257)
extract_subtitle_frames(video_path, output_folder, roi)