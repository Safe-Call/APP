import os
import cv2

import numpy as np
import PIL.Image as PILImage
from PIL import ImageFilter

from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics.texture import Texture


class ScreenVideo(Screen):
    def __init__(self, deepfakedetector, **kwargs):
        super(ScreenVideo, self).__init__(**kwargs)
        self.deepfakedetector = deepfakedetector
        self.layout = GridLayout(cols=1, rows=2)
        self.event_predict = None
        self.event_video = None
        self.overlay_color = None  # 색상 오버레이를 저장할 변수

        fontName = '/'.join([os.getenv('SystemRoot'), '/fonts/gulim.ttc'])

        # 딥페이크 탐지 출력값
        self.output_layout = GridLayout(cols=2, spacing=(5, 5), size_hint_y=None, height=80)
        self.prob_label = Label(text="딥페이크 확률: 0%", size_hint_y=None, font_name=fontName)

        self.detection_result = Label(text="위조 위험", size_hint_y=None, font_name=fontName)

        self.output_layout.add_widget(self.prob_label)
        self.output_layout.add_widget(self.detection_result)

        # OpenCV 비디오 캡처 객체
        self.cap = cv2.VideoCapture('samples/deepfake_youtube.mp4')

        # Kivy Image 위젯
        self.img = Image()

        self.layout.add_widget(self.output_layout)
        self.layout.add_widget(self.img)
        self.add_widget(self.layout)

    def on_enter(self, *args):
        # Detection 진행
        self.event_predict = Clock.schedule_interval(self.get_frame_predict, 1.0 / 2.0)
        # CV로 불러온 영상 출력 Frame
        self.event_video = Clock.schedule_interval(self.get_frame_video, 1.0 / 30.0)

    def on_leave(self, *args):
        if self.event_predict:
            self.event_predict.cancel()
        if self.event_video:
            self.event_video.cancel()

    def get_frame_predict(self, dt):
        ret, frame = self.cap.read()
        os.makedirs('AppModules/detection_log/', exist_ok=True)
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = PILImage.fromarray(frame_rgb)
            pil_image = pil_image.filter(ImageFilter.EDGE_ENHANCE_MORE)
            video_output = self.deepfakedetector.run(pil_image)
            self.prob_label.text = f"딥페이크 확률: {(1 - video_output) * 100:.2f}%"

            if (video_output * 100) >= 75:
                self.detection_result.text = "위조 안전"
                self.overlay_color = (0, 255, 0)  # 초록색 오버레이
            elif 71.25 <= (video_output * 100) < 75:
                print('의심!!!')
                self.detection_result.text = "위조 의심"
                self.overlay_color = (0, 255, 255)  # 노란색 오버레이
            else:
                self.detection_result.text = "위조 위험"
                self.overlay_color = (0, 0, 255) # 빨간색 오버레이

            with open("AppModules/detection_log/video_log.txt", 'a', encoding='utf-8') as f:
                f.write(f'{1-video_output}\n')

    def get_frame_video(self, dt):
        ret, frame = self.cap.read()
        if ret:
            # Convert to Kivy texture
            if self.overlay_color is not None:
                overlay = np.full(frame.shape, self.overlay_color, dtype=np.uint8)
                alpha = 0.3  # 블렌딩 강도
                cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

            buf = cv2.flip(frame, 0).tobytes()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.img.texture = texture
        else:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
