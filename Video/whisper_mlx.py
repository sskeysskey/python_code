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

import tkinter as tk
from tkinter import filedialog

# ============ 配置 logging =============
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S"
)

# ============ 常量 =============
# 如果你在环境变量中也想支持自定义，可以改为：
# FFMPEG_BIN = os.environ.get("FFMPEG_BIN", "/opt/homebrew/bin/ffmpeg")
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
    # …按需扩展
}

APP_DIR    = pathlib.Path(__file__).parent
OUTPUT_DIR = APP_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ============ 工具函数 =============
def prepare_audio(audio_path: str) -> mx.array:
    """用 ffmpeg 解出 16k 单声道原始 PCM 并转成 float32"""
    cmd = [
        FFMPEG_BIN, "-y", "-i", audio_path,
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
            cur.append(w); L += len(w) + 1
    if cur:
        lines.append(" ".join(cur))
    return lines


def check_data_loss(segment: Dict[str, Any], processed_lines: List[str]) -> None:
    processed_words = ' '.join(processed_lines).split()
    original_words  = [w['word'] for w in segment.get('words', [])]
    if len(processed_words) != len(original_words):
        logging.warning(f"⚠️ Segment {segment.get('id', '<no-id>')} 词数不一致: 原始 {len(original_words)} vs 处理后 {len(processed_words)}")
        logging.warning(f"    原始: {' '.join(original_words)}")
        logging.warning(f"    处理后: {' '.join(processed_words)}")


def check_final_output(segments: List[Dict[str, Any]], out_path: str) -> None:
    original_text = ' '.join(seg.get('text', '') for seg in segments).strip()
    lines = []
    with open(out_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 过滤掉 SRT 序号行、时间戳行、WEBVTT header
            if re.fullmatch(r'\d+', line): continue
            if '-->' in line:          continue
            if line.upper() == 'WEBVTT': continue
            lines.append(line)
    final_text = ' '.join(lines).strip()
    if original_text != final_text:
        logging.warning("⚠️ 最终输出文本与原始 segments['text'] 不一致，可能存在丢字或顺序变化")
        logging.debug(f"原始全文: {original_text}")
        logging.debug(f"最终全文: {final_text}")


def write_subtitles(segments: List[Dict[str, Any]],
                    fmt: str,
                    out_path: str,
                    remove_fillers: bool = True) -> None:
    """
    fmt: "srt" 或 "vtt"
    """
    with open(out_path, "w", encoding="utf-8") as f:
        if fmt == "vtt":
            f.write("WEBVTT\n\n")
        idx = 1
        for seg in segments:
            words = seg.get("words", [])
            if not words:
                continue
            text = " ".join(w["word"] for w in words)
            if remove_fillers:
                text = re.sub(r"\b(um|uh)\b", "", text).strip()
            lines = split_text_into_lines(text)
            # 每两行构成一个字幕条目
            for i in range(0, len(lines), 2):
                part = lines[i:i+2]
                start_idx = sum(len(x.split()) for x in lines[:i])
                end_idx   = sum(len(x.split()) for x in lines[:i+2])
                t0 = words[start_idx]["start"]
                t1 = words[end_idx - 1]["end"]
                # 强制最短显示时长
                duration = t1 - t0
                min_dur = max(len(" ".join(part)) / 21, 1.5)
                if duration < min_dur:
                    t1 = t0 + min_dur
                # 写入
                if fmt == "srt":
                    f.write(f"{idx}\n")
                    f.write(f"{format_timestamp(t0)} --> {format_timestamp(t1)}\n")
                    f.write("\n".join(part) + "\n\n")
                else:  # vtt
                    f.write(f"{format_timestamp(t0, True)} --> {format_timestamp(t1, True)}\n")
                    f.write("\n".join(part) + "\n\n")
                idx += 1
            # 本段校验
            check_data_loss(seg, lines)
    # 全局校验
    check_final_output(segments, out_path)


def write_transcript_txt(segments: List[Dict[str, Any]],
                         out_path: str,
                         remove_fillers: bool = True) -> None:
    with open(out_path, "w", encoding="utf-8") as f:
        for seg in segments:
            txt = seg.get("text", "")
            if remove_fillers:
                txt = re.sub(r"\b(um|uh)\b", "", txt).strip()
            f.write(txt + "\n")


# ============ 主流程 =============
def run_pipeline(video_path: str,
                 model_key: str = "large-v3",
                 language: str = None):
    logging.info(f"▶ 处理文件: {video_path}")
    model_repo = MODELS.get(model_key, model_key)
    audio = prepare_audio(video_path)
    result = process_audio(model_repo, audio, language)

    # 输出路径
    base = OUTPUT_DIR / pathlib.Path(video_path).stem
    vtt_path = f"{base}.vtt"
    srt_path = f"{base}.srt"
    txt_path = f"{base}.txt"
    zip_path = f"{base}.zip"

    # 写入文件
    write_subtitles(result["segments"], "vtt", vtt_path, remove_fillers=True)
    write_subtitles(result["segments"], "srt", srt_path, remove_fillers=True)
    write_transcript_txt(result["segments"], txt_path, remove_fillers=True)

    # 打包
    with ZipFile(zip_path, "w") as z:
        for p in [vtt_path, srt_path, txt_path]:
            z.write(p, os.path.basename(p))

    logging.info(f"✔ 全部完成，结果保存在: {OUTPUT_DIR}")
    logging.info(f"   - {vtt_path}\n   - {srt_path}\n   - {txt_path}\n   - {zip_path}")


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
        chosen_model = "large-v3"
        chosen_lang  = None   # None = 自动检测，也可以改成 "en"/"zh"…
        run_pipeline(path, chosen_model, chosen_lang)


if __name__ == "__main__":
    logging.info("📺 请按 ⌘+⌥+C 选择视频并开始转码…")
    on_activate()