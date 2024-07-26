import os
import sounddevice as sd
import numpy as np
import PIL.Image as PILImage
from PIL import ImageFilter

from kivy.uix.screenmanager import Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.camera import Camera
from kivy.clock import Clock
from kivy.graphics.texture import Texture

class ScreenCAM(Screen):
    def __init__(self, deepfakedetector, deepvoicedetector, **kwargs):
        super(ScreenCAM, self).__init__(**kwargs)
        self.deepfakedetector = deepfakedetector
        self.audio_processor = AudioProcessor(deepvoicedetector)

        self.layout = GridLayout(cols=1, rows=2)
        self.event_video = None
        self.event_audio = None
        self.overlay_color = None  # 색상 오버레이를 저장할 변수

        fontName = '/'.join([os.getenv('SystemRoot'), '/fonts/gulim.ttc'])

        # 딥페이크 탐지 출력값
        self.output_layout = GridLayout(cols=3, spacing=(5, 5), size_hint_y=None, height=80)
        self.prob_video_label = Label(text="딥페이크 확률: 0%", size_hint_y=None, font_name=fontName)
        self.prob_voice_label = Label(text="딥보이스 확률: 0%", size_hint_y=None, font_name=fontName)

        self.detection_result = Label(text="위조 위험", size_hint_y=None, font_name=fontName)

        self.output_layout.add_widget(self.prob_video_label)
        self.output_layout.add_widget(self.prob_voice_label)
        self.output_layout.add_widget(self.detection_result)
        self.layout.add_widget(self.output_layout)

        # 캠 출력
        self.cam = Camera(play=True)
        self.layout.add_widget(self.cam)
        self.add_widget(self.layout)

    def on_enter(self, *args):
        # 영상과 오디오 Detection 진행
        self.event_video = Clock.schedule_interval(self.get_predict, 1.0 / 30.0)

    def on_leave(self, *args):
        if self.event_video:
            self.event_video.cancel()
        if self.event_audio:
            self.event_audio.cancel()

        self.audio_processor.stop_stream()

    def get_predict(self, dt):
        # 영상 데이터 처리
        texture = self.cam.texture
        cam_output = 0
        if texture:
            size = texture.size
            pixels = texture.pixels
            pil_image = PILImage.frombytes(mode='RGB', size=size, data=pixels)
            pil_image = pil_image.resize((224, 224)).filter(ImageFilter.EDGE_ENHANCE_MORE)
            cam_output = self.deepfakedetector.run(pil_image)
            self.prob_video_label.text = f"딥페이크 확률: {(1 - cam_output) * 100:.2f}%"

        # 오디오 데이터 처리
        audio_output = self.audio_processor.process_audio()
        if audio_output is not None:
            self.prob_voice_label.text = f"딥보이스 확률: {(1 - audio_output) * 100:.2f}%"

        try:
            if (cam_output * 100) > 75 and (audio_output * 100) > 75:
                self.detection_result.text = "위조 안전"
                self.overlay_color = [0, 255, 0, 128]  # 초록색 오버레이
            elif 71.25 <= (cam_output * 100) < 75 and 71.25 <= (audio_output * 100) < 75:
                self.detection_result.text = "위조 의심"
                self.overlay_color = [255, 255, 0, 128]  # 노란색 오버레이
            else:
                self.detection_result.text = "위조 위험"
                self.overlay_color = [255, 0, 0, 128]  # 빨간색 오버레이

            with open("AppModules/detection_log/cam_log.txt", 'a', encoding='utf-8') as f:
                f.write(f'{1 - cam_output} {1 - audio_output}\n')

        except:
            self.detection_result.text = "오류"
            if audio_output is None:
                with open("AppModules/detection_log/cam_log.txt", 'a', encoding='utf-8') as f:
                    f.write(f'{1 - cam_output} 1\n')
            else:
                with open("AppModules/detection_log/cam_log.txt", 'a', encoding='utf-8') as f:
                    f.write(f'1 1\n')

        # 캠 영상에 오버레이 적용
        self.apply_overlay()

    def apply_overlay(self):
        texture = self.cam.texture
        if texture and self.overlay_color:
            frame = np.frombuffer(texture.pixels, np.uint8).reshape(texture.size[1], texture.size[0], 4)
            overlay = np.full((frame.shape[0], frame.shape[1], 4), self.overlay_color, dtype=np.uint8)
            alpha = self.overlay_color[3] / 255.0  # 투명도 설정
            frame = (1 - alpha) * frame + alpha * overlay
            frame = frame.astype(np.uint8)

            frame = np.flipud(frame)
            buf = frame.tobytes()
            new_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='rgba')
            new_texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
            self.cam.texture = new_texture


class AudioProcessor:
    def __init__(self, deepvoicedetector):
        self.deepvoicedetector = deepvoicedetector
        self.audio_queue = []
        self.output_audio_queue = []
        self.samplerate = 16000
        self.blocksize = int(self.samplerate / 2)
        self.stream = sd.Stream(callback=self.audio_callback, channels=1, samplerate=self.samplerate)
        self.stream.start()

    def audio_callback(self, indata, outdata, frames, time, status):
        self.audio_queue.append(indata.copy())
        self.output_audio_queue.append(indata.copy())

        if self.output_audio_queue:
            audio_data = np.concatenate(self.output_audio_queue)
            self.output_audio_queue = []
            outdata[:] = audio_data[:frames].reshape(outdata.shape)
            if len(audio_data) > frames:
                self.output_audio_queue.append(audio_data[frames:])
        else:
            outdata.fill(0)

    def process_audio(self):
        if self.audio_queue:
            audio_data = np.concatenate(self.audio_queue)
            self.audio_queue = []

            audio_data = audio_data.flatten()
            audio_output = self.deepvoicedetector.run(audio_data, self.samplerate)
            return audio_output

        return None

    def stop_stream(self):
        self.stream.stop()
        self.stream.close()
