import re
from typing import List, Tuple

from pydub import AudioSegment

from config import (
    DON_WAV,
    KATSU_WAV,
    BALLOON_BANG_WAV,
    HIT_PER_SEC
)

def txt_loads(data_str: str):
    data = []
    current_course = None
    chart = []

    for line in data_str.split('\n'):
        if line.startswith("course:"):
            if current_course is not None:
                data.append({"course": current_course, "chart": chart})
                chart = []
            current_course = int(re.search(r'\d+', line).group())
        elif line:
            line = line.strip("[]")
            nums = line.split(",")
            chart.append([int(nums[0]), float(nums[1])])

    if current_course is not None:
        data.append({"course": current_course, "chart": chart})

    output_data = {"data": data}
    return output_data

def annotate_sound(data: list, offset: float = 0) -> List[Tuple[str, float]]:
    chart = []
    for m in data:
        if m[0] in {1, 3}:  # Don or Big Don
            chart.append((DON_WAV, offset + m[1]))
        elif m[0] in {2, 4}:  # Katsu or Big Katsu
            chart.append((KATSU_WAV, offset + m[1]))
        elif m[0] in {5, 6}:  # Drum Roll or Big Drum Roll
            count = m[1]
            while count < m[2]:
                chart.append((DON_WAV, offset + count))
                count += (1 / HIT_PER_SEC)
                
        elif m[0] == 7:  # Balloon
            count = m[1]
            balloon_count = 0
            while count < m[2] and balloon_count < m[3]:
                chart.append((DON_WAV, offset + count))
                count += (1 / HIT_PER_SEC)
                balloon_count += 1

            if balloon_count >= m[3]:
                chart.append((BALLOON_BANG_WAV, offset + m[1]))
        else:
            raise ValueError("Your chart file has some problems.")
    return chart

def resize_audio(file_path: str, target_duration: int, target_amplitude: int) -> AudioSegment:
    audio = AudioSegment.from_wav(file_path)
    audio = audio[:target_duration * 1000]

    if file_path == DON_WAV or file_path == BALLOON_BANG_WAV:
        return audio

    audio = audio - (audio.dBFS - target_amplitude)
    return audio