# Taiko Music Generator

**Mix sougs and [太鼓の達人 (Taiko no Tatsujin)](https://taiko.namco-ch.net/taiko/en/) drum sounds to generate Taiko Music.**

> Go to website [here](https://huggingface.co/spaces/ryanlinjui/taiko-music-generator).

# Demo

https://github.com/user-attachments/assets/d4c202a1-d9d1-4323-96f5-c8848f5d1185

> Input `.tja` format must follow [TJA Tools](https://whmhammer.github.io/tja-tools/) website.

# Features
- [x] **Music Course Level Output**
  - 裏 (Ura)
  - おに (Oni)
  - むずかしい (Hard)
  - ふつう (Normal)
  - かんたん (Easy)
- [x] **Common Settings**
  - 譜面分岐 (Sheet Branch)
  - 連打/秒 (DrumRoll hits per second)
- [x] **Adjustable Volume**: Modify the volume for individual taiko notes or entire songs.
- [x] **Example Music**: Preloaded sample .tja files and songs to help you get started quickly.

# Getting Started
### Setup
Use [poetry](https://github.com/python-poetry/poetry) to set up the development environment:

```bash
poetry shell
poetry install
```

> You might need to use [pyenv](https://github.com/pyenv/pyenv) to create a Python virtual environment. Currently, the project is using Python 3.10 or above.

### Run the App

```bash
python app.py
```

# FAQ
### What is `.tja` file?  
The `.tja` file format is designed for Taiko simulators to provide playable charts data.
> For more details, visit this [wiki](https://wikiwiki.jp/jiro/太鼓さん次郎#tja).

### How is `.tja` converted to music?  
By [tja-rs](https://github.com/JacobLinCool/tja-rs), taiko notes in the `.tja` file are mapped to a timeline in the song.<br>
This concept can be found in [Homework 01, Problem 05](https://drive.google.com/file/d/1Wdv4nLaoXsXFZX17OleQpllvq5ii_n08/view) from the [2024 NTNU CP2 course](https://sites.google.com/gapps.ntnu.edu.tw/neokent/teaching/2024spring-computer-programming-ii).

> Credits by [JacobLinCool](https://github.com/JacobLinCool), [RyanLin(ryanlinjui)](https://github.com/ryanlinjui).