from typing import List, Dict, Tuple

import gradio as gr
import numpy as np
from pydub import AudioSegment

from config import COURSE
from parser import (
    TJARhythmAnnotation,
    GenerateTaikoMusic
)

def handle(*files: Tuple[str, str, str]) -> Tuple[Tuple[int, np.ndarray], ...]:
    tja_file, ryan_file, music_file = files
    
    if tja_file != None:
        gr.Info("Processing tja file (prioritized)")
        ryan = TJARhythmAnnotation(open(tja_file, "r", encoding="utf-8").read())
        music = GenerateTaikoMusic(ryan, music_file)
    
    elif ryan_file != None:
        gr.Info("Processing RhythmAnnotation file")
        music = GenerateTaikoMusic(
            open(ryan_file, "r", encoding="utf-8").read(),
            music_file
        )
    else:
        raise gr.Error("Please upload a tja file or a RhythmAnnotation file.")

    channel = 2 if music_file is not None else 1

    return \
        (music[4].frame_rate * channel, np.array(music[4].get_array_of_samples())), \
        (music[3].frame_rate * channel, np.array(music[3].get_array_of_samples())), \
        (music[2].frame_rate * channel, np.array(music[2].get_array_of_samples())), \
        (music[1].frame_rate * channel, np.array(music[1].get_array_of_samples())), \
        (music[0].frame_rate * channel, np.array(music[0].get_array_of_samples()))

def user_interface() -> gr.Interface:
    with gr.Blocks(delete_cache=(86400, 86400)) as demo:    
        gr.Markdown("# Taiko Music Generator")
        gr.Markdown('> Useful Links: [GitHub]("https://github.com/ryanlinjui/taiko-music-generator") [HuggingFace]("https://huggingface.co/ryanlinjui/taiko-music-generator")')
        
        with gr.Row():
            with gr.Column():
                with gr.Tab("tja to Music"):
                    gr.Markdown("# 太鼓達人譜面/Taiko tja file")
                    tja_file = gr.File(label="tja", file_types=[".tja"])
                
                with gr.Tab("RhythmAnnotation to Music"):
                    gr.Markdown("# RhythmAnnotation file (程設二作業 HW0105)")
                    ryan_file = gr.File(label="json txt", file_types=[".json", ".txt"])
            
                gr.Markdown("# 譜面音樂/Chart Music (Optional)")
                music_file = gr.File(label="ogg mp3", file_types=[".ogg", ".mp3"])
                generate_button = gr.Button("Generate Music")
            
            with gr.Column():
                music = [gr.Audio(label=course, format="mp3", interactive=False) for course in reversed(COURSE)]
    
        generate_button.click(
            fn=handle,
            inputs=[tja_file, ryan_file, music_file],
            outputs=music
        )
    
    return demo

if __name__ == "__main__":
    demo = user_interface()
    demo.launch()