import cv2
import os
import queue
import time
import numpy as np
import sounddevice as sd
from kivy.config import Config

from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.camera import Camera
from kivy.uix.video import Video
from kivy.uix.label import Label

from kivy.clock import Clock

import PIL.Image as Image

from AppModules.screens import ScreenVoid, ScreenDetail
from Detection.DeepFake.inference import DeepFakeInference

Config.set('graphics', 'width', '640')
Config.set('graphics', 'height', '800')

# 오디오 데이터를 처리하기 위한 큐
audio_queue = queue.Queue()


class MainPage(GridLayout):
    # runs on initialization
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.deepfakedetector = DeepFakeInference()
        self.cols = 1
        self.rows = 3
        # 카메라 부분, 해당 Grid는 고정이다.
        self.cam = Camera(play=True, resolution=(224, 224))
        # self.cam = cv2.VideoCapture('fake_video.mp4')

        # 오디오 스트림 설정
        stream = sd.Stream(callback=self.audio_callback)
        stream.start()

        # 오디오 레벨 표시 부분
        self.audio_label = Label(text="Audio Level: 0", size_hint_y=None, height='48dp')
        self.add_widget(self.audio_label)

        # FPS 표시 부분
        self.fps_label = Label(text="FPS: 0", size_hint_y=None, height='48dp')
        Clock.schedule_interval(self.update, 1.0 / 2.0)
        self.add_widget(self.cam)

        # 분할된 Screen manager part
        self.screen_manager = ScreenManager()

        screen_void = Screen(name='screen_void')
        screen_void.add_widget(ScreenVoid(self.screen_manager))
        self.screen_manager.add_widget(screen_void)

        screen_detail = Screen(name='screen_detail')
        screen_detail.add_widget(ScreenDetail(self.screen_manager))
        self.screen_manager.add_widget(screen_detail)

        self.add_widget(self.screen_manager)

    def update(self, dt):
        # self.audio_update(dt)
        self.get_frame_predict(dt)

    def audio_callback(self, indata, outdata, frames, time, status):
        volume_norm = np.linalg.norm(indata)
        # indata를 outdata에 넣으면 마이크로 넘어온 데이터가 스피커로 출력된다.
        outdata[:] = indata
        self.audio_label.text = f"Audio Level: {volume_norm:.2f}"

    def get_frame_predict(self, dt):
        texture = self.cam.texture
        size = texture.size
        pixels = texture.pixels
        pil_image = Image.frombytes(mode='RGB', size=size, data=pixels)
        output = self.deepfakedetector.run(pil_image)
        print(output)

        f = open(f"score.txt", 'w', encoding='utf-8')
        f.write(
            f'{output}\n')
        f.close()
