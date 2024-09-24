import queue
from kivy.uix.gridlayout import GridLayout

from AppModules.Screens.GraphScreen import ScreenGraphManager
from AppModules.Screens.DetectionScreen import ScreenVideoVioceManager, ButtonDiv
from Detectors.DeepFake.deepfake_inference import DeepFakeInference
from Detectors.DeepVoice.deepvoice_inference import DeepVoiceInference

# 오디오 데이터를 처리하기 위한 큐
audio_queue = queue.Queue()


class MainPage(GridLayout):
    # runs on initialization
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.deepfakedetector = DeepFakeInference()
        self.deepvoicedetector = DeepVoiceInference()
        self.cols = 1
        self.spacing = (0, 0)  # rows와 cols 간의 간격을 0으로 설정
        self.padding = (10, 10, 10, 10)  # 레이아웃의 여백을 10으로 설정

        self.screen_video_voice_manager = ScreenVideoVioceManager(self.deepfakedetector, self.deepvoicedetector)

        inside = GridLayout(cols=3, spacing=(5, 5), size_hint_y=None, height=80)
        inside.add_widget(ButtonDiv(self.screen_video_voice_manager))
        self.add_widget(inside)
        self.add_widget(self.screen_video_voice_manager)
        # ===============================================================================
        # 분할된 Screen manager part
        self.screen_graph_manager = ScreenGraphManager(self.screen_video_voice_manager)
        self.add_widget(self.screen_graph_manager)

