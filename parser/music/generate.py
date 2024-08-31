import json
from typing import List

import numpy as np
from pydub import AudioSegment

from .utils import (
    txt_loads,
    annotate_sound,
    resize_audio
)

def process(chart: list, music: str | None = None) -> AudioSegment:
    max_length = int(max([start_time + len(resize_audio(file_path, target_duration=1, target_amplitude=-20))
                         for file_path, start_time in chart]))

    mixed_audio = np.zeros(max_length)

    for file_path, start_time in chart:
        audio = resize_audio(file_path, target_duration=0.5, target_amplitude=-20)
        audio_array = np.array(audio.get_array_of_samples())

        start_index = int(start_time * audio.frame_rate)
        end_index = start_index + len(audio_array)

        if len(mixed_audio) < end_index:
            mixed_audio = np.pad(mixed_audio, (0, end_index - len(mixed_audio)))

        mixed_audio[start_index:end_index] += audio_array

    mixed_audio = np.clip(mixed_audio, -32768, 32767)

    mixed_audio_segment = AudioSegment(
        mixed_audio.astype(np.int16).tobytes(),
        frame_rate=audio.frame_rate,
        sample_width=2,
        channels=1
    )

    if music is None: # no background chart music, only drum sound
        return mixed_audio_segment
    else:
        background_music = AudioSegment.from_ogg(music)
        mixed_audio_with_bg = background_music.overlay(mixed_audio_segment)
        return mixed_audio_with_bg

def GenerateTaikoMusic(ryan: str, music_path: str | None = None) -> List[AudioSegment]:
    try:
        data = json.loads(ryan)
    except ValueError as e:
        data = txt_loads(ryan)

    if len(data["data"]) < 0 and len(data["data"]) > 5:
        raise("Issue occur: chart data")

    music = [AudioSegment.empty()] * 5

    for d in data["data"]:
        chart = annotate_sound(d["chart"])
        music[d["course"]] = process(chart, music_path)

    return music