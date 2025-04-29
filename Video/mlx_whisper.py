import os
import pathlib
import subprocess
import logging
import re
from zipfile import ZipFile
from typing import List, Dict, Any

import numpy as np
import mlx.core as mx
import mlx_whisper

from pynput import keyboard
import tkinter as tk
from tkinter import filedialog

# ============ 配置 logging =============
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S"
)

# ============ 常量 =============
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
    # …按需扩展
}

APP_DIR   = pathlib.Path(__file__).parent
OUTPUT_DIR = APP_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ============ 工具函数 =============
def prepare_audio(audio_path: str) -> mx.array:
    """用 ffmpeg 解出 16k 单声道原始 PCM 并转成 float32"""
    cmd = [
        "ffmpeg", "-y", "-i", audio_path,
        "-f", "s16le", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1", "-"
    ]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    raw, _ = p.communicate()
    arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    return mx.array(arr)

def process_audio(model_repo: str, audio: mx.array, language: str = None) -> Dict[str, Any]:
    opts = {"language": language} if language else {}
    logging.info(f"→ 调用 Whisper: model={model_repo}  language={language or 'auto'}")
    result = mlx_whisper.transcribe(
        audio, path_or_hf_repo=model_repo,
        fp16=False, verbose=True, word_timestamps=True,
        **opts
    )
    logging.info("✔ 转码完成")
    return result

def format_timestamp(sec: float, vtt: bool=False) -> str:
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    if vtt:
        return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"
    else:
        return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".",",")

def split_text_into_lines(text: str, max_chars: int=42) -> List[str]:
    words = text.split()
    lines, cur, L = [], [], 0
    for w in words:
        if L + len(w) + 1 > max_chars:
            lines.append(" ".join(cur))
            cur, L = [w], len(w)
        else:
            cur.append(w); L += len(w)+1
    if cur: lines.append(" ".join(cur))
    return lines

def write_subtitles(segments: List[Dict[str, Any]], fmt: str, out_path: str):
    with open(out_path, "w", encoding="utf-8") as f:
        if fmt=="vtt": f.write("WEBVTT\n\n")
        idx = 1
        for seg in segments:
            words = seg.get("words", [])
            if not words: continue
            text = " ".join(w["word"] for w in words)
            text = re.sub(r"\b(um|uh)\b","", text).strip()
            lines = split_text_into_lines(text)
            for i in range(0, len(lines), 2):
                part = lines[i:i+2]
                t0 = words[ sum(len(x.split()) for x in lines[:i]) ]["start"]
                t1 = words[ sum(len(x.split()) for x in lines[:i+2]) - 1 ]["end"]
                if fmt=="srt":
                    f.write(f"{idx}\n{format_timestamp(t0)} --> {format_timestamp(t1)}\n" +
                            "\n".join(part) + "\n\n")
                else:
                    f.write(f"{format_timestamp(t0,True)} --> {format_timestamp(t1,True)}\n" +
                            "\n".join(part) + "\n\n")
                idx += 1

def write_transcript_txt(segments: List[Dict[str, Any]], out_path: str):
    with open(out_path, "w", encoding="utf-8") as f:
        for seg in segments:
            txt = re.sub(r"\b(um|uh)\b","", seg["text"]).strip()
            f.write(txt + "\n")

# ============ 主流程 =============
def run_pipeline(video_path: str,
                 model_key: str = "large-v3",
                 language: str = None):
    logging.info(f"▶ 处理文件: {video_path}")
    model_repo = MODELS.get(model_key, model_key)
    audio = prepare_audio(video_path)
    result = process_audio(model_repo, audio, language)

    # 输出文件
    base = OUTPUT_DIR / pathlib.Path(video_path).stem
    vtt = f"{base}.vtt"; srt = f"{base}.srt"; txt = f"{base}.txt"; zp = f"{base}.zip"

    write_subtitles(result["segments"], "vtt", vtt)
    write_subtitles(result["segments"], "srt", srt)
    write_transcript_txt(result["segments"], txt)

    # 打包
    with ZipFile(zp, "w") as z:
        z.write(vtt, os.path.basename(vtt))
        z.write(srt, os.path.basename(srt))
        z.write(txt, os.path.basename(txt))

    logging.info(f"✔ 全部完成，结果保存在: {OUTPUT_DIR}")
    logging.info(f"   - {vtt}\n   - {srt}\n   - {txt}\n   - {zp}")

# ============ 全局热键 & 文件对话框 ============
def on_activate():
    # 弹出文件选取框
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        title="Select a video file", 
        filetypes=[("video files","*.mp4 *.mov *.avi *.mkv")]
    )
    root.destroy()
    if path:
        # 这里可以硬编码，也可以提 prompt 让用户在终端输入
        chosen_model = "large-v3"
        chosen_lang  = None   # None=自动检测
        run_pipeline(path, chosen_model, chosen_lang)
    
if __name__ == "__main__":
    logging.info("📺 请按 ⌘+⌥+C 选择视频并开始转码…")
    on_activate()