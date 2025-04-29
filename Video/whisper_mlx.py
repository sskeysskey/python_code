import os
import pathlib
import subprocess
import logging
import re
# from zipfile import ZipFile
from typing import List, Dict, Any, Optional # 增加了 Optional
import platform # 增加了 platform
# import json

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
TEMP_DIR   = pathlib.Path("/tmp")

# /tmp 一般自带，无需 mkdir

# 音频预处理参数
AUDIO_PARAMS = {
    "sample_rate": 16000,
    "normalize_volume": True,
    "remove_noise": True,
    "voice_enhance": True
}

# Whisper模型参数
WHISPER_PARAMS = {
    "temperature": 0.0,  # 0表示使用贪婪解码
    "condition_on_previous_text": True,
    "word_timestamps": True,
    "prepend_punctuations": "\"'([{-",
    "append_punctuations": "\"'.。,，!！?？:：)]}"
}

def enhance_audio(audio_path: str) -> str:
    """音频增强处理"""
    temp_path = TEMP_DIR / f"enhanced_{os.path.basename(audio_path)}"
    
    cmd = [
        FFMPEG_BIN, "-y",
        "-i", audio_path,
        # 降噪
        "-af", "afftdn=nf=-25",
        # 动态范围压缩
        "-af", "acompressor=threshold=-12dB:ratio=2:attack=200:release=1000",
        # 音量归一化
        "-filter:a", "loudnorm=I=-16:LRA=11:TP=-1.5",
        str(temp_path)
    ]
    
    subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
    return str(temp_path)

def prepare_audio(audio_path: str) -> mx.array:
    """用 ffmpeg 解出 16k 单声道原始 PCM 并转成 float32"""
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
    
    # 转换为float32并归一化
    arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    
    # 如果需要降噪
    if AUDIO_PARAMS["remove_noise"]:
        from scipy import signal
        # 简单的高通滤波去除低频噪声
        b, a = signal.butter(4, 100/(AUDIO_PARAMS["sample_rate"]/2), 'high')
        arr = signal.filtfilt(b, a, arr)
    
    return mx.array(arr)

def post_process_text(text: str) -> str:
    """文本后处理"""
    # 修复数字和单位之间的空格
    text = re.sub(r'(\d+)\s+([a-zA-Z])', r'\1\2', text)
    
    # 修复重复的标点符号
    text = re.sub(r'([。，！？!?])\1+', r'\1', text)
    
    # 修复错误的省略号
    text = re.sub(r'\.{2,}', '...', text)
    
    return text.strip()

def process_audio(model_repo: str, audio: mx.array, language: str = None) -> Dict[str, Any]:
    opts = {"language": language} if language else {}
    opts.update(WHISPER_PARAMS)
    
    logging.info(f"→ 调用 Whisper: model={model_repo}  language={language or 'auto'}")
    
    result = mlx_whisper.transcribe(
        audio,
        path_or_hf_repo=model_repo,
        fp16=False,
        verbose=True,
        **opts
    )
    
    # 对每个segment进行后处理
    for segment in result["segments"]:
        segment["text"] = post_process_text(segment["text"])
        
        # 优化时间戳
        if "words" in segment:
            for word in segment["words"]:
                # 确保单词时长合理
                min_word_duration = len(word["word"]) * 0.05  # 每个字符至少50ms
                if word["end"] - word["start"] < min_word_duration:
                    word["end"] = word["start"] + min_word_duration
    
    logging.info("✔ 转码完成")
    return result

def format_timestamp(sec: float, vtt: bool=False) -> str:
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    # 确保时间戳不会出现负值
    h, m, s = max(0, h), max(0, m), max(0, s)
    if vtt:
        return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"
    else:
        return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".",",")

def split_text_into_lines(text: str, max_chars: int=42) -> List[str]:
    """智能分行"""
    # 首先按标点符号分割
    segments = re.split(r'([。！？\?!])', text)
    lines = []
    current_line = []
    current_length = 0
    
    for segment in segments:
        if not segment:
            continue
        
        words = segment.split()
        for word in words:
            if current_length + len(word) + 1 > max_chars:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)
            else:
                current_line.append(word)
                current_length += len(word) + 1
                
        # 如果是标点符号，强制换行
        if re.match(r'[。！？\?!]', segment):
            if current_line:
                lines.append(" ".join(current_line))
            current_line = []
            current_length = 0
    
    if current_line:
        lines.append(" ".join(current_line))
    
    return lines

def write_subtitles(segments: List[Dict[str, Any]],
                    fmt: str,
                    out_path: str,
                    remove_fillers: bool = True) -> None:
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
                text = re.sub(r"\b(um|uh|er|ah|oh)\b", "", text).strip()
            
            # 应用文本后处理
            text = post_process_text(text)
            
            lines = split_text_into_lines(text)
            
            for i in range(0, len(lines), 2):
                part = lines[i:i+2]
                start_idx = sum(len(x.split()) for x in lines[:i])
                end_idx   = sum(len(x.split()) for x in lines[:i+2])
                
                if start_idx >= len(words):
                    continue
                    
                t0 = words[start_idx]["start"]
                t1 = words[min(end_idx - 1, len(words) - 1)]["end"]
                
                # 智能调整时长
                duration = t1 - t0
                min_dur = max(len(" ".join(part)) / 20, 1.8)  # 略微增加最小显示时间
                max_dur = min(min_dur * 2.5, 7.0)  # 设置最大显示时间
                
                if duration < min_dur:
                    t1 = t0 + min_dur
                elif duration > max_dur:
                    t1 = t0 + max_dur
                
                # 确保时间戳递增
                if idx > 1:
                    prev_end = getattr(write_subtitles, 'prev_end', 0)
                    if t0 < prev_end:
                        t0 = prev_end + 0.001
                write_subtitles.prev_end = t1
                
                # 这里只有 srt 和 vtt，实际只会调用 srt
                if fmt == "srt":
                    f.write(f"{idx}\n")
                    f.write(f"{format_timestamp(t0)} --> {format_timestamp(t1)}\n")
                    f.write("\n".join(part) + "\n\n")
                else:  # vtt
                    f.write(f"{format_timestamp(t0, True)} --> {format_timestamp(t1, True)}\n")
                    f.write("\n".join(part) + "\n\n")
                idx += 1

# def write_transcript_txt(segments: List[Dict[str, Any]],
#                          out_path: str,
#                          remove_fillers: bool = True) -> None:
#     with open(out_path, "w", encoding="utf-8") as f:
#         for seg in segments:
#             txt = seg.get("text", "")
#             if remove_fillers:
#                 txt = re.sub(r"\b(um|uh|er|ah|oh)\b", "", txt).strip()
#             txt = post_process_text(txt)
#             f.write(txt + "\n")

def run_pipeline(video_path: str,
                 model_key: str = "large-v3",
                 language: str = None):
    try:
        logging.info(f"▶ 处理文件: {video_path}")
        model_repo = MODELS.get(model_key, model_key)
        
        # 音频处理
        audio = prepare_audio(video_path)
        result = process_audio(model_repo, audio, language)
        
        # 只输出 .srt
        base     = OUTPUT_DIR / pathlib.Path(video_path).stem
        # vtt_path = f"{base}.vtt"
        srt_path = f"{base}.srt"
        # txt_path = f"{base}.txt"
        # json_path = f"{base}.json"
        # zip_path = f"{base}.zip"
        
        # 保存原始结果
        # with open(json_path, 'w', encoding='utf-8') as f:
        #     json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 写入字幕文件
        # write_subtitles(result["segments"], "vtt", vtt_path, remove_fillers=True)
        write_subtitles(result["segments"], "srt", srt_path, remove_fillers=True)
        # write_transcript_txt(result["segments"], txt_path, remove_fillers=True)
        
        # 打包
        # with ZipFile(zip_path, "w") as z:
        #     for p in [vtt_path, srt_path, txt_path, json_path]:
        #         z.write(p, os.path.basename(p))
        
        logging.info(f"✔ 转码完成，SRT 保存在: {srt_path}")
        # logging.info(f"   - {vtt_path}\n   - {srt_path}\n   - {txt_path}\n   - {json_path}\n   - {zip_path}")
        
    except Exception as e:
        logging.error(f"处理过程中出错: {str(e)}")
        raise
    finally:
        # 清理 /tmp 下的增强音频文件
        for f in TEMP_DIR.glob("enhanced_*"):
            try:
                f.unlink()
            except:
                pass

def on_activate():
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        title="Select a video file", 
        filetypes=[("video files","*.mp4 *.mov *.avi *.mkv")]
    )
    root.destroy()
    if path:
        chosen_model = "large-v3"
        chosen_lang  = None
        run_pipeline(path, chosen_model, chosen_lang)

def select_video_file() -> Optional[str]:
    """弹出文件选择对话框并返回所选视频文件的路径"""
    root = tk.Tk()
    root.withdraw() # 隐藏主窗口

    # --- 尝试将对话框置于顶层 (macOS specific) ---
    if platform.system() == "Darwin": # 检查是否为 macOS
        try:
            # 使用 AppleScript 尝试将 Python 应用激活到前台
            # 这通常会使得随后弹出的对话框也出现在前面
            script = 'tell app "System Events" to set frontmost of process "Python" to true'
            # 注意：如果通过终端运行，进程名可能是 "Terminal" 或其他
            # 可以尝试更通用的方法，比如激活当前应用
            # script = 'tell application (path to frontmost application as text) to activate'
            subprocess.run(['osascript', '-e', script], check=True, capture_output=True)
            logging.debug("尝试使用 osascript 将应用置前。")
        except FileNotFoundError:
            logging.warning("osascript 未找到，无法尝试将对话框置前。")
        except subprocess.CalledProcessError as e:
            logging.warning(f"执行 osascript 将应用置前失败: {e.stderr.decode()}")
        except Exception as e:
            logging.warning(f"尝试将应用置前时发生未知错误: {e}")
    # --- 结束置顶尝试 ---

    path = filedialog.askopenfilename(
        title="请选择一个视频文件进行转码",
        filetypes=[("视频文件", "*.mp4 *.mov *.avi *.mkv *.wmv *.flv"), # 增加了更多格式
                   ("所有文件", "*.*")]
    )
    root.destroy() # 关闭 Tkinter 实例
    return path if path else None # 如果用户取消则返回 None

if __name__ == "__main__":
    print("正在启动视频选择器...") # 仅打印少量启动信息

    video_path = select_video_file() # 首先调用文件选择

    if video_path:
        # 用户选择了文件，现在开始处理流程
        print(f"已选择文件: {video_path}")
        print("开始处理，请查看后续日志输出...")

        # ---- 在这里可以选择模型和语言 ----
        # 目前硬编码为 large-v3 和 自动检测
        chosen_model = "large-v3"
        chosen_lang  = None # None 表示自动检测
        # --------------------------------

        run_pipeline(video_path, chosen_model, chosen_lang)
        print("\n处理完成。")
    else:
        # 用户取消了选择
        print("用户取消了文件选择，程序退出。")