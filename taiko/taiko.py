import functools
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Union

import numpy as np
from pydub import AudioSegment
from tja import parse_tja, PyChart

DON_WAV = "./assets/sound/Don.wav"
KA_WAV = "./assets/sound/Ka.wav"
BIGDON_WAV = "./assets/sound/BigDon.wav"
BALLOON_BANG_WAV = "./assets/sound/Balloon.wav"
PARTY_POPPER_SUCCESS_WAV = "./assets/sound/PartyPopperSuccess.wav"
PARTY_POPPER_FAILURE_WAV = "./assets/sound/PartyPopperFailure.wav"

DEFAULT_HIT_PER_SEC = 20  # drum hits in drumroll, balloon
DEFAULT_SOUND_VOLUME = 5  # for song, taiko notes volume settings
DEFAULT_BALLOON_COUNT = 5  # set default if balloon count is missing in tja file

SHEET_BRANCH = {
    "普通譜面 / Normal": "N",
    "玄人譜面 / Expert": "E",
    "達人譜面 / Master": "M",
}

@dataclass
class CourseMusic:
    ura: Union[AudioSegment, Tuple[int, np.ndarray]] = field(default_factory=AudioSegment.empty)
    oni: Union[AudioSegment, Tuple[int, np.ndarray]] = field(default_factory=AudioSegment.empty)
    hard: Union[AudioSegment, Tuple[int, np.ndarray]] = field(default_factory=AudioSegment.empty)
    normal: Union[AudioSegment, Tuple[int, np.ndarray]] = field(default_factory=AudioSegment.empty)
    easy: Union[AudioSegment, Tuple[int, np.ndarray]] = field(default_factory=AudioSegment.empty)

@functools.lru_cache(maxsize=None)
def load_wav(file_path: str) -> AudioSegment:
    """Load a WAV file from disk."""
    return AudioSegment.from_wav(file_path)

@functools.lru_cache(maxsize=None)
def adjust_audio_cached(file_path: str, target_duration: float, target_amplitude: int, volume: int) -> AudioSegment:
    """
    Adjust audio to a target duration and amplitude, then apply volume scaling.
    
    Parameters:
        file_path (str): Path to the WAV file.
        target_duration (float): Duration in seconds to trim the audio.
        target_amplitude (int): Target amplitude (in dBFS) to normalize the audio.
        volume (int): Volume scaling factor relative to DEFAULT_SOUND_VOLUME.
    
    Returns:
        AudioSegment: The adjusted audio segment.
    """
    audio = load_wav(file_path)
    # Trim audio to target duration (in milliseconds)
    audio = audio[:int(target_duration * 1000)]
    # Normalize audio to target_amplitude (in dBFS)
    if audio.dBFS != float("-inf"):
        gain = target_amplitude - audio.dBFS
        audio = audio.apply_gain(gain)
    
    # Apply volume scaling (volume factor relative to DEFAULT_SOUND_VOLUME)
    volume_factor = volume / DEFAULT_SOUND_VOLUME
    volume_factor = np.log10(volume_factor) if volume_factor > 0 else -np.inf
    audio = audio + (20 * volume_factor)
    
    # Increase volume
    if file_path in (DON_WAV, BALLOON_BANG_WAV, BIGDON_WAV, PARTY_POPPER_SUCCESS_WAV, PARTY_POPPER_FAILURE_WAV):
        audio = audio + 8

    # Decrease volume
    if file_path in (KA_WAV):
        audio = audio - 3
    
    return audio

class TaikoMusic:
    def __init__(self):
        # Input filepath
        self.tja_file: Optional[str] = None
        self.song_file: Optional[str] = None

        # Sheet branch for "普通譜面, 玄人譜面, 達人譜面"
        self.sheet_branch: Optional[str] = None

        # DrumRoll hits per seconds
        self.per_hits_second: int = DEFAULT_HIT_PER_SEC

        # Volume settings for each elements
        self.song_sound_volume: int = DEFAULT_SOUND_VOLUME
        self.don_sound_volume: int = DEFAULT_SOUND_VOLUME
        self.ka_sound_volume: int = DEFAULT_SOUND_VOLUME
        self.big_don_sound_volume: int = DEFAULT_SOUND_VOLUME
        self.big_ka_sound_volume: int = DEFAULT_SOUND_VOLUME
        self.drum_roll_sound_volume: int = DEFAULT_SOUND_VOLUME
        self.big_drum_roll_sound_volume: int = DEFAULT_SOUND_VOLUME
        self.balloon_sound_volume: int = DEFAULT_SOUND_VOLUME
        self.balloon_bang_sound_volume: int = DEFAULT_SOUND_VOLUME
        self.party_popper_sound_volume: int = DEFAULT_SOUND_VOLUME
        self.party_popper_success_volume: int = DEFAULT_SOUND_VOLUME
        self.party_popper_failure_volume: int = DEFAULT_SOUND_VOLUME

    def generate_taiko_music(self) -> CourseMusic:
        with open(self.tja_file, "r", encoding="utf-8") as f:
            tja_content = f.read()

        parsed_tja = parse_tja(tja_content)        
        music = CourseMusic()
        for chart in parsed_tja.charts:
            course = chart.course
            if course in ("Easy", "Normal", "Hard", "Oni", "Ura"):
                setattr(music, course.lower(), self.__process(chart))
        return self.__post_process(music)

    def __process(self, chart: PyChart) -> AudioSegment:
        annotated_chart = self.__annotate_sound(chart)
        drum_hit_duration = 0.5
        sample_end_times = []
        
        # Calculate maximum required sample length for mixing (in samples)
        for file_path, start_time, vol in annotated_chart:
            audio = adjust_audio_cached(file_path, drum_hit_duration, -20, vol)
            sr = audio.frame_rate
            duration_samples = int((len(audio) / 1000.0) * sr)
            sample_end = int(start_time * sr) + duration_samples
            sample_end_times.append(sample_end)
        max_length = max(sample_end_times) if sample_end_times else 0
        mixed_audio = np.zeros(max_length, dtype=np.int32)

        # Mix each annotated audio into the final mix
        for file_path, start_time, volume in annotated_chart:
            audio = adjust_audio_cached(file_path, drum_hit_duration, -20, volume)
            sr = audio.frame_rate
            audio_array = np.array(audio.get_array_of_samples(), dtype=np.int32)
            start_index = int(start_time * sr)
            end_index = start_index + len(audio_array)
            
            if mixed_audio.shape[0] < end_index:
                mixed_audio = np.pad(mixed_audio, (0, end_index - mixed_audio.shape[0]), mode="constant")

            mixed_audio[start_index:end_index] += audio_array

        # Clip the mixed audio to valid int16 range
        mixed_audio = np.clip(mixed_audio, -32768, 32767)
        mixed_audio_segment = AudioSegment(
            mixed_audio.astype(np.int16).tobytes(),
            frame_rate=sr,
            sample_width=2,
            channels=1
        )

        if self.song_file is None:  # Only taiko drum sound
            return mixed_audio_segment
        else:
            # Overlay drum sounds on background music
            if self.song_file.endswith((".mp3", ".ogg", ".wav")):
                background_music = AudioSegment.from_file(self.song_file)
            else:
                raise ValueError(
                    "Unsupported file format. Please provide mp3, ogg, or wav file."
                )
            
            # Calculate gain in dB relative to DEFAULT_SOUND_VOLUME
            if self.song_sound_volume > 0:
                volume_factor = self.song_sound_volume / DEFAULT_SOUND_VOLUME
                gain_db = 20 * np.log10(volume_factor)
                background_music = background_music.apply_gain(gain_db)
            else:
                # If volume is zero or negative, mute the background music
                background_music = background_music - 120

            mixed_audio_with_bg = background_music.overlay(mixed_audio_segment)
            return mixed_audio_with_bg

    def __annotate_sound(self, chart: PyChart) -> List[Tuple[str, float, int]]:
        def find_end(flat_notes: List, current_index: int) -> Tuple[Optional[int], float]:
            for idx in range(current_index + 1, len(flat_notes)):
                if flat_notes[idx].note_type == "EndOf":
                    return idx, flat_notes[idx].timestamp
            return None, flat_notes[current_index].timestamp

        annotated_chart: List[Tuple[str, float, int]] = []
        balloon_list = chart.balloons.copy()

        flat_notes = []
        for segment in chart.segments:
            if segment.branch is not None and segment.branch != SHEET_BRANCH.get(self.sheet_branch, None):
                continue
            flat_notes.extend(segment.notes)

        i = 0
        while i < len(flat_notes):
            note = flat_notes[i]
            note_type = note.note_type
            timestamp = note.timestamp

            if note_type == "Don":
                annotated_chart.append((DON_WAV, timestamp, self.don_sound_volume))
                i += 1

            elif note_type == "DonBig":
                annotated_chart.append((BIGDON_WAV, timestamp, self.big_don_sound_volume))
                i += 1

            elif note_type in {"Ka", "KaBig"}:
                volume = self.big_ka_sound_volume if note_type == "KaBig" else self.ka_sound_volume
                annotated_chart.append((KA_WAV, timestamp, volume))
                i += 1

            elif note_type in {"Roll", "RollBig", "Balloon", "BalloonAlt"}:
                end_index, end_time = find_end(flat_notes, i)
                if note_type in {"Roll", "RollBig"}:
                    time_count = timestamp
                    while time_count < end_time:
                        vol = self.big_drum_roll_sound_volume if note_type == "RollBig" else self.drum_roll_sound_volume
                        annotated_chart.append((DON_WAV, time_count, vol))
                        time_count += 1 / self.per_hits_second
                else:  # Balloon or BalloonAlt
                    time_count = timestamp
                    balloon_count = 0
                    balloon_threshold = balloon_list[0] if balloon_list else DEFAULT_BALLOON_COUNT
                    while time_count < end_time and balloon_count < balloon_threshold:
                        vol = self.balloon_sound_volume if note_type == "Balloon" else self.party_popper_sound_volume
                        annotated_chart.append((DON_WAV, time_count, vol))
                        time_count += 1 / self.per_hits_second
                        balloon_count += 1

                    if balloon_count >= balloon_threshold:
                        if note_type == "Balloon":
                            annotated_chart.append((BALLOON_BANG_WAV, time_count, self.balloon_bang_sound_volume))
                        else:
                            annotated_chart.append((PARTY_POPPER_SUCCESS_WAV, time_count, self.party_popper_success_volume))
                    elif note_type == "BalloonAlt":
                        annotated_chart.append((PARTY_POPPER_FAILURE_WAV, time_count, self.party_popper_failure_volume))

                    if balloon_list:
                        balloon_list.pop(0)

                i = (end_index + 1) if end_index is not None else i + 1
            
            else:
                i += 1

        return annotated_chart

    def __post_process(self, music: CourseMusic) -> CourseMusic:
        for attr in ("ura", "oni", "hard", "normal", "easy"):
            segment = getattr(music, attr)
            if isinstance(segment, AudioSegment):
                array = np.array(segment.get_array_of_samples())
                if segment.channels > 1:
                    array = array.reshape((-1, segment.channels))
                setattr(music, attr, (segment.frame_rate, array))
        return music
