from typing import List

from pydub import AudioSegment

from parser.music.generate import GenerateTaikoMusic
from .utils import tja_to_ryan

def TJARhythmAnnotation(tja: str, music_path: str | None = None) -> List[AudioSegment]:
    ryan = tja_to_ryan(tja)
    return GenerateTaikoMusic(ryan, music_path)