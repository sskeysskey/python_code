import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog

class VideoPlayer:
    def __init__(self, video_path):
        self.cap = cv2.VideoCapture(video_path)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        self.playing = False
        self.current_frame = 0
        
        self.start_point = None
        self.end_point = None
        self.selecting = False

    @staticmethod
    def choose_video():
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        video_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        return video_path

    def play(self):
        cv2.namedWindow('Video Player')
        cv2.createTrackbar('Progress', 'Video Player', 0, self.frame_count - 1, self.on_trackbar)
        cv2.setMouseCallback('Video Player', self.mouse_callback)

        while True:
            if self.playing:
                ret, frame = self.cap.read()
                if not ret:
                    self.playing = False
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                self.current_frame += 1
                cv2.setTrackbarPos('Progress', 'Video Player', self.current_frame)
            else:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
                ret, frame = self.cap.read()

            frame_with_roi = self.draw_roi(frame.copy())
            cv2.imshow('Video Player', frame_with_roi)

            key = cv2.waitKey(1000 // self.fps) & 0xFF
            if key == 27:  # 27 是 ESC 键的 ASCII 码
                break
            elif key == ord(' '):
                self.playing = not self.playing

        self.cap.release()
        cv2.destroyAllWindows()

    def on_trackbar(self, value):
        self.current_frame = value
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, value)

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.start_point = (x, y)
            self.selecting = True
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.selecting:
                self.end_point = (x, y)
        elif event == cv2.EVENT_LBUTTONUP:
            self.end_point = (x, y)
            self.selecting = False
            self.print_roi()

    def draw_roi(self, frame):
        if self.start_point and self.end_point:
            cv2.rectangle(frame, self.start_point, self.end_point, (0, 255, 0), 2)
        return frame

    def print_roi(self):
        if self.start_point and self.end_point:
            x1, y1 = self.start_point
            x2, y2 = self.end_point
            x = min(x1, x2)
            y = min(y1, y2)
            w = abs(x2 - x1)
            h = abs(y2 - y1)
            roi = (x, y, w, h)
            print(f"ROI = {roi}")

# 使用文件选择对话框选择视频
video_path = VideoPlayer.choose_video()

if video_path:
    # 获取视频帧的宽度和高度
    cap = cv2.VideoCapture(video_path)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"视频宽度: {frame_width}, 视频高度: {frame_height}")

    player = VideoPlayer(video_path)
    player.play()