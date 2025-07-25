import os
import pathlib
import subprocess
import logging
import re
import platform
from typing import List, Dict, Any, Optional

import numpy as np
import mlx.core as mx
import mlx_whisper

import tkinter as tk
from tkinter import filedialog

import time
import random
import pyautogui
import threading

# ============ 配置 logging =============
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S"
)

# ============ 常量 =============
FFMPEG_BIN = "/opt/homebrew/bin/ffmpeg"

DEVICE = "mps" if mx.metal.is_available() else "cpu"
MODELS = {
    "tiny-q4":    "mlx-community/whisper-tiny-mlx-q4",
    "large-v3":   "mlx-community/whisper-large-v3-mlx",
    "small-q4":   "mlx-community/whisper-small.en-mlx-q4",
    "small-fp32": "mlx-community/whisper-small-mlx-fp32",
}
LANGUAGES = {
    "auto": None,
    "en": "English",
    "zh": "Chinese",
    "es": "Spanish",
}

BASE_DIR    = pathlib.Path("/Users/yanzhang/Downloads")
OUTPUT_DIR  = BASE_DIR
TEMP_DIR    = pathlib.Path("/tmp")

AUDIO_PARAMS = {
    "sample_rate": 16000,
    "normalize_volume": True,
    "remove_noise": True,
    "voice_enhance": True
}

WHISPER_PARAMS = {
    "temperature": 0.0,
    "condition_on_previous_text": True,
    "word_timestamps": True,
    "prepend_punctuations": "\"'([{-",
    "append_punctuations": "\"'.。,，!！?？:：)]}"
}


# 添加鼠标移动功能的函数
def move_mouse_periodically():
    while True:
        try:
            # 获取屏幕尺寸
            screen_width, screen_height = pyautogui.size()
            
            # 随机生成目标位置，避免移动到屏幕边缘
            x = random.randint(100, screen_width - 100)
            y = random.randint(100, screen_height - 100)
            
            # 缓慢移动鼠标到随机位置
            pyautogui.moveTo(x, y, duration=1)
            
            # 等待30-60秒再次移动
            time.sleep(random.randint(30, 60))
            
        except Exception as e:
            print(f"鼠标移动出错: {str(e)}")
            time.sleep(30)

def enhance_audio(audio_path: str) -> str:
    temp_path = TEMP_DIR / f"enhanced_{os.path.basename(audio_path)}"
    cmd = [
        FFMPEG_BIN, "-y",
        "-i", audio_path,
        "-af", "afftdn=nf=-25,acompressor=threshold=-12dB:ratio=2:attack=200:release=1000,loudnorm=I=-16:LRA=11:TP=-1.5",
        str(temp_path)
    ]
    subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
    return str(temp_path)


def prepare_audio(audio_path: str) -> mx.array:
    if AUDIO_PARAMS["voice_enhance"]:
        audio_path = enhance_audio(audio_path)

    cmd = [
        FFMPEG_BIN, "-y", "-i", audio_path,
        "-f", "s16le", "-acodec", "pcm_s16le",
        "-ar", str(AUDIO_PARAMS["sample_rate"]),
        "-ac", "1"
    ]
    if AUDIO_PARAMS["normalize_volume"]:
        cmd.extend(["-filter:a", "volume=2.0"])
    cmd.append("-")

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    raw, _ = p.communicate()
    arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

    if AUDIO_PARAMS["remove_noise"]:
        from scipy import signal # scipy 是一个额外的依赖
        b, a = signal.butter(4, 100/(AUDIO_PARAMS["sample_rate"]/2), 'high')
        arr = signal.filtfilt(b, a, arr)

    return mx.array(arr)


def post_process_text(text: str) -> str:
    text = re.sub(r'(\d+)\s+([a-zA-Z])', r'\1\2', text)
    text = re.sub(r'([。，！？!?])\1+', r'\1', text)
    text = re.sub(r'\.{2,}', '...', text)
    return text.strip()


def format_timestamp(sec: float, vtt: bool=False) -> str:
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    h, m, s = max(0, h), max(0, m), max(0, s)
    if vtt:
        return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"
    else:
        return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".",",")


def split_text_into_lines(text: str, max_chars: int=42) -> List[str]:
    segments = re.split(r'([。！？\?!])', text)
    lines, current, length = [], [], 0
    for seg in segments:
        if not seg: continue
        words = seg.split()
        for w in words:
            if length + len(w) + 1 > max_chars:
                lines.append(" ".join(current))
                current, length = [w], len(w)
            else:
                current.append(w)
                length += len(w) + 1
        if re.match(r'[。！？\?!]', seg):
            lines.append(" ".join(current))
            current, length = [], 0
    if current:
        lines.append(" ".join(current))
    return lines


def write_subtitles(segments: List[Dict[str, Any]],
                    fmt: str,
                    out_path: str,
                    remove_fillers: bool = True) -> None:
    """
    1) 先把每个 segment 拆成若干 subtitle block（带 start/end/text）
    2) 再合并相邻、文本相同的 block
    3) 过滤和调整时间不合逻辑的 block:
       - 丢弃 end <= start 的 block
       - 如果某 block 的 start <= 上一个 block 的 end，则把它的 start 调整为 prev_end + 0.001，
         若此时 start >= end，则丢弃该 block
    4) 最后一次性写入文件
    """
    # ———— 一、收集所有小块 ————
    blocks = []
    for seg in segments:
        words = seg.get("words", [])
        if not words:
            continue
        # 拼文本
        text = " ".join(w["word"] for w in words)
        if remove_fillers:
            text = re.sub(r"\b(um|uh|er|ah|oh)\b", "", text).strip()
        text = post_process_text(text)

        # 这里依然按你原来拆行、分块的逻辑来做
        lines = split_text_into_lines(text)
        # 每两行（或最后一行）做一个 block
        for i in range(0, len(lines), 2):
            part = lines[i:i+2]
            # 计算这一块在 word 列表里的起止词索引
            start_idx = sum(len(x.split()) for x in lines[:i])
            end_idx   = sum(len(x.split()) for x in lines[:i+2])
            if start_idx >= len(words):
                continue
            t0 = words[start_idx]["start"]
            t1 = words[min(end_idx - 1, len(words) - 1)]["end"]
            # 保证最短和最长时长
            dur = t1 - t0
            min_dur = max(len(" ".join(part)) / 20, 1.8)
            max_dur = min(min_dur * 2.5, 7.0)
            if dur < min_dur:
                t1 = t0 + min_dur
            elif dur > max_dur:
                t1 = t0 + max_dur
            blocks.append({
                "start": t0,
                "end":   t1,
                "text":  "\n".join(part)
            })

    # ———— 二、合并相邻且文本相同的 blocks ————
    merged = []
    for b in blocks:
        if merged and merged[-1]["text"] == b["text"]:
            # 直接把前一块的 end 推到这一块的 end
            merged[-1]["end"] = b["end"]
        else:
            merged.append(b)

    # ———— 三、过滤 & 调整时间不合逻辑的 blocks ————
    cleaned = []
    prev_end = 0.0
    delta = 0.001  # 1ms
    for b in merged:
        # 丢弃 end <= start
        if b["end"] <= b["start"]:
            continue
        # 如果与前一条重叠或开始早于前一条结束，则调整 start
        if b["start"] <= prev_end:
            b["start"] = prev_end + delta
            # 调整后仍然不合理，则丢弃
            if b["start"] >= b["end"]:
                continue
        cleaned.append(b)
        prev_end = b["end"]

    # ———— 四、写入文件 ————
    with open(out_path, "w", encoding="utf-8") as f:
        if fmt == "vtt":
            f.write("WEBVTT\n\n")
        for idx, b in enumerate(cleaned, start=1):
            start_ts = format_timestamp(b["start"], vtt=(fmt=="vtt"))
            end_ts   = format_timestamp(b["end"],   vtt=(fmt=="vtt"))

            # [这里是关键改动] 把换行统统换成空格
            one_line = b["text"].replace("\n", " ").strip()

            if fmt == "srt":
                f.write(f"{idx}\n")
                f.write(f"{start_ts} --> {end_ts}\n")
                f.write(one_line + "\n\n")
            else:  # vtt
                f.write(f"{start_ts} --> {end_ts}\n")
                f.write(one_line + "\n\n")


def chunked_transcribe(audio: mx.array,
                       model_repo: str,
                       sr: int = 16000,
                       chunk_s: int = 200,
                       overlap_s: int = 0,
                       language: Optional[str] = None,
                       **whisper_opts) -> Dict[str, Any]:
    """
    将长音频分块转录，每块 chunk_s 秒，重叠 overlap_s 秒，
    然后拼接所有 segments 并做后处理。
    """
    arr = audio.asnumpy() if hasattr(audio, "asnumpy") else np.array(audio)
    hop = chunk_s - overlap_s
    total = arr.shape[0]
    offset = 0.0
    all_segs: List[Dict[str, Any]] = []

    base_opts = {"language": language} if language else {}
    base_opts.update(whisper_opts)

    for start in range(0, total, hop * sr):
        end = start + chunk_s * sr
        chunk = arr[start:end]
        if chunk.size < sr:
            break

        logging.info(f"→ chunk [{offset:.1f}s – {offset + chunk_s:.1f}s]")
        result = mlx_whisper.transcribe(
            mx.array(chunk),
            path_or_hf_repo=model_repo,
            fp16=False,
            verbose=False,
            **base_opts
        )

        for seg in result["segments"]:
            seg["start"] += offset
            seg["end"]   += offset
            seg["text"]  = post_process_text(seg["text"])
            if "words" in seg:
                for w in seg["words"]:
                    w["start"] += offset
                    w["end"]   += offset
                    # 确保最小单词时长
                    min_dur = len(w["word"]) * 0.05
                    if w["end"] - w["start"] < min_dur:
                        w["end"] = w["start"] + min_dur

        all_segs.extend(result["segments"])
        offset += hop

    all_segs.sort(key=lambda x: x["start"])
    return {"segments": all_segs}


def run_pipeline(video_path: str,
                 model_key: str = "large-v3",
                 language: str = None):
    try:
        logging.info(f"▶ 处理：{video_path}")
        repo = MODELS.get(model_key, model_key)
        audio = prepare_audio(video_path)
        result = chunked_transcribe(
            audio,
            model_repo=repo,
            sr=AUDIO_PARAMS["sample_rate"],
            chunk_s=200,
            overlap_s=0,
            language=language,
            **WHISPER_PARAMS
        )

        base = OUTPUT_DIR / pathlib.Path(video_path).stem
        srt_path = f"{base}.srt"
        write_subtitles(result["segments"], "srt", srt_path, remove_fillers=True)
        logging.info(f"✔ SRT 已保存: {srt_path}")

    except Exception as e:
        logging.error(f"出错: {e}")
        raise
    finally:
        for f in TEMP_DIR.glob("enhanced_*"):
            try: f.unlink()
            except: pass


def select_video_file() -> Optional[str]:
    root = tk.Tk()
    root.withdraw()
    if platform.system() == "Darwin":
        try:
            script = 'tell app "System Events" to set frontmost of process "Python" to true'
            subprocess.run(['osascript', '-e', script], check=True,
                           capture_output=True)
        except:
            pass
    path = filedialog.askopenfilename(
        title="请选择视频文件",
        filetypes=[("视频","*.mp4 *.mov *.avi *.mkv"),("所有文件","*.*")]
    )
    root.destroy()
    return path if path else None


if __name__ == "__main__":
    # 开启防挂机鼠标线程
    threading.Thread(target=move_mouse_periodically, daemon=True).start()
    
    print("启动选择器…")
    vp = select_video_file()
    if vp:
        print(f"已选：{vp}，开始…")
        run_pipeline(vp, "large-v3", None)
        print("完成。")
    else:
        print("取消，退出。")