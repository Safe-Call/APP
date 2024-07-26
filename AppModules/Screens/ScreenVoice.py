import os
import sounddevice as sd
import soundfile as sf

from kivy.uix.screenmanager import Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock



class ScreenVoice(Screen):
    def __init__(self, deepvoicedetector, **kwargs):
        super().__init__(**kwargs)
        self.data, self.sr = sf.read('samples/Obama-to-Biden.wav')
        self.audio_processor = AudioProcessor(deepvoicedetector, self.data, self.sr)

        self.layout = GridLayout(cols=1, rows=2)
        self.event_predict = None
        self.event_voice = None
        self.overlay_color = None

        fontName = '/'.join([os.getenv('SystemRoot'), '/fonts/gulim.ttc'])

        # 딥페이크 탐지 출력값
        self.output_layout = GridLayout(cols=2, spacing=(5, 5), size_hint_y=None, height=80)
        self.prob_label = Label(text="딥보이스 확률: 0%", size_hint_y=None, font_name=fontName)
        self.detection_result = Label(text="위조 위험", size_hint_y=None, font_name=fontName)

        self.output_layout.add_widget(self.prob_label)
        self.output_layout.add_widget(self.detection_result)

        self.layout.add_widget(self.output_layout)
        self.add_widget(self.layout)

        # 오버레이 위젯
        self.overlay = OverlayWidget()
        self.add_widget(self.overlay)

    def on_enter(self, *args):
        # Detection 진행
        sd.play(self.data, samplerate=self.sr)
        self.event_audio = Clock.schedule_interval(self.get_audio_prediction, 1.0 / 30.0)

    def on_leave(self, *args):
        if self.event_audio:
            sd.stop()
            self.event_audio.cancel()

    def get_audio_prediction(self, dt):
        audio_output, audio_block = self.audio_processor.process_audio()
        if audio_output is not None:
            self.prob_label.text = f"딥페이크 확률: {(1 - audio_output) * 100:.2f}%"

            if (audio_output * 100) >= 75:
                self.detection_result.text = "위조 안전"
                self.overlay.set_color(0, 1, 0, 0.5)  # 초록색 오버레이
            elif 71.25 <= (audio_output * 100) < 75:
                self.detection_result.text = "위조 의심"
                self.overlay.set_color(1, 1, 0, 0.5)  # 노란색 오버레이
            else:
                self.detection_result.text = "위조 위험"
                self.overlay.set_color(1, 0, 0, 0.5)  # 빨간색 오버레이

            with open("AppModules/detection_log/audio_log.txt", 'a', encoding='utf-8') as f:
                f.write(f'{1-audio_output}\n')


class OverlayWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self.color = Color(0, 0, 0, 0)  # 초기에는 투명하게 설정
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def set_color(self, r, g, b, a):
        self.color.r = r
        self.color.g = g
        self.color.b = b
        self.color.a = a

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class AudioProcessor:
    def __init__(self, deepvoicedetector, audio_data, sr):
        self.deepvoicedetector = deepvoicedetector
        self.audio_data = audio_data
        self.sr = sr
        self.blocksize = self.sr  # 초 단위로 데이터 블록 크기 설정
        self.current_pos = 0

    def process_audio(self):
        if self.current_pos < len(self.audio_data):
            end_pos = min(self.current_pos + self.blocksize, len(self.audio_data))
            audio_block = self.audio_data[self.current_pos:end_pos]
            self.current_pos = end_pos

            # 오디오 데이터 처리
            audio_block = audio_block.flatten()
            audio_output = self.deepvoicedetector.run(audio_block, self.sr)

            return audio_output, audio_block
        return None, None