import os
import re
import time
import piexif
import exifread
import subprocess
import json
from datetime import datetime
from pathlib import Path

# 支持文件类型
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv"}
IMAGE_EXTS = {".jpg", ".jpeg"}

# 用于收集未能重命名的文件
failed_files = []

def get_creation_time_image(path):
    try:
        exif_dict = piexif.load(str(path))
        dt = exif_dict['Exif'].get(piexif.ExifIFD.DateTimeOriginal)
        if dt:
            return datetime.strptime(dt.decode(), "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass

    try:
        with open(path, "rb") as f:
            tags = exifread.process_file(f, stop_tag="EXIF DateTimeOriginal")
            dt = tags.get("EXIF DateTimeOriginal")
            if dt:
                return datetime.strptime(str(dt), "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None


def get_creation_time_video(path):
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", str(path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        meta = json.loads(result.stdout)
        dt_str = meta.get("format", {}).get("tags", {}).get("creation_time")
        if dt_str:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).astimezone()
    except Exception:
        pass
    return None


def get_time_from_filename(name):
    patterns = [
        r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})[_-]?(\d{2})(\d{2})(\d{2})',          # 20230401_153012
        r'IMG_(\d{8})_(\d{6})',                                               # IMG_20230401_153012
        r'VID_(\d{8})_(\d{6})',                                               # VID_20230401_153012
        r'(\d{13})',                                                          # 1680320204000 timestamp
        r'Screenshot_(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})',        # Screenshot_2025-01-20-21-32-22
    ]
    for p in patterns:
        m = re.search(p, name)
        if m:
            try:
                if len(m.groups()) == 6:
                    return datetime.strptime("".join(m.groups()), "%Y%m%d%H%M%S")
                elif len(m.groups()) == 2:
                    return datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
                elif len(m.groups()) == 1:
                    ts = int(m.group(1))
                    if len(m.group(1)) > 10:
                        ts = ts // 1000
                    return datetime.fromtimestamp(ts)
                elif "Screenshot_" in name and len(m.groups()) == 6:
                    return datetime.strptime("-".join(m.groups()), "%Y-%m-%d-%H-%M-%S")
            except Exception:
                continue
    return None


def resolve_filename(dir_path, dt, ext, is_video):
    prefix = "VID" if is_video else "IMG"
    base = f"{prefix}_{dt.strftime('%Y%m%d_%H%M%S')}"
    filename = f"{base}{ext.lower()}"
    i = 1
    while os.path.exists(os.path.join(dir_path, filename)):
        filename = f"{base}_{i}{ext.lower()}"
        i += 1
    return filename

def process_file(path: Path):
    if is_standard_named(path.name):
        print(f"[跳过] 已标准命名：{path.name}")
        return
    ext = path.suffix.lower()
    is_video = ext in VIDEO_EXTS
    is_image = ext in IMAGE_EXTS

    if not (is_video or is_image):
        return

    # 尝试从元信息读取时间
    dt = get_creation_time_video(path) if is_video else get_creation_time_image(path)
    if not dt:
        dt = get_time_from_filename(path.name)

    if not dt:
        failed_files.append(str(path))
        print(f"[跳过] 无时间信息：{path.name}")
        return

    new_name = resolve_filename(path.parent, dt, path.suffix, is_video)
    new_path = path.parent / new_name
    print(f"[重命名] {path.name} → {new_name}")
    path.rename(new_path)

def scan_and_rename(dir_path):
    for file in os.scandir(dir_path):
        if file.is_file():
            process_file(Path(file.path))

    if failed_files:
        print("\n⛔ 以下文件未能重命名（无时间信息）：")
        for f in failed_files:
            print(" -", f)
    else:
        print("\n✅ 所有文件均成功重命名")

def is_standard_named(filename: str):
    pattern = r'^(IMG|VID)_(\d{8})_(\d{6})(?:_\d+)?\.[a-zA-Z0-9]+$'
    return re.match(pattern, filename) is not None

# 示例入口
if __name__ == "__main__":
    target_folder = "/Users/kiin/Downloads/Camera"  # TODO: 修改为目标路径
    scan_and_rename(target_folder)