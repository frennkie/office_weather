# -*- coding: utf-8 -*-

import os
import sys
import random
import pygame
import subprocess


def get_random_sound_file(sounds_dir):
    """get a random filename from given (absolute) path dir

    Args:
        sounds_dir (str):

    """

    sound_files = []

    files = [f for f in os.listdir(sounds_dir) if os.path.isfile(sounds_dir + "/" + f)]

    for filename in files:
        if filename.lower().endswith("wav") or filename.lower().endswith("mp3"):
            sound_files.append(os.path.abspath(sounds_dir + "/" + filename))

    if sound_files:
        return sound_files[random.randint(0, len(sound_files) - 1)]
    else:
        return False


def play_sound_file(sound_file_abs_path):
    """play sound from wav file

    Args:
        sound_file_abs_path (str):

    """
    pygame.mixer.init()
    pygame.mixer.music.load(sound_file_abs_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        continue


def play_tts(words, lang="en-US"):
    """use text-to-speech engine to say a given words

    Args:
        words (str):
        lang (str):

    """
    tempfile = "/tmp/.temp." + str(os.getpid()) + ".wav"
    devnull = open("/dev/null", "w")
    subprocess.call(["sudo", "/usr/bin/amixer", "cset", "numid=3", "1"], stderr=devnull)
    subprocess.call(["pico2wave", "-l", lang, "-w", tempfile, words], stderr=devnull)
    subprocess.call(["aplay", tempfile], stderr=devnull)
    os.remove(tempfile)


if __name__ == "__main__":
    pass
