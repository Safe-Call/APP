import os

from kivy.uix.screenmanager import ScreenManager
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button

from AppModules.Screens.ScreenVideo import ScreenVideo
from AppModules.Screens.ScreenVoice import ScreenVoice
from AppModules.Screens.ScreenCAM import ScreenCAM


class ButtonDiv(GridLayout):
    def __init__(self, screen_video_voice_manager):
        super().__init__()
        self.cols = 3
        self.rows = 1
        self.screen_video_voice_manager = screen_video_voice_manager
        fontName = '/'.join([os.getenv('SystemRoot'), '/fonts/gulim.ttc'])

        self.button_cam = Button(text="캠 버튼", size_hint_y=None, font_name=fontName, font_size=15)
        self.button_cam.bind(on_press=self.press_button_cam)

        self.button_deepfake = Button(text="딥페이크 영상 버튼", size_hint_y=None, font_name=fontName, font_size=15)
        self.button_deepfake.bind(on_press=self.press_button_deepfake)

        self.button_deepvoice = Button(text="딥보이스 영상 버튼", size_hint_y=None, font_name=fontName, font_size=15)
        self.button_deepvoice.bind(on_press=self.press_button_deepvoice)

        self.add_widget(self.button_cam)
        self.add_widget(self.button_deepfake)
        self.add_widget(self.button_deepvoice)

    def press_button_cam(self, instance):
        self.screen_video_voice_manager.current = 'screen_cam'

    def press_button_deepfake(self, instance):
        self.screen_video_voice_manager.current = 'screen_video'

    def press_button_deepvoice(self, instance):
        self.screen_video_voice_manager.current = 'screen_voice'


def ScreenVideoVioceManager(deepfakedetector, deepvoicedetector):
    screen_video_voice_manager = ScreenManager()

    screen_cam = ScreenCAM(name='screen_cam', deepfakedetector=deepfakedetector, deepvoicedetector=deepvoicedetector)
    screen_video_voice_manager.add_widget(screen_cam)

    screen_video = ScreenVideo(name='screen_video', deepfakedetector=deepfakedetector)
    screen_video_voice_manager.add_widget(screen_video)

    screen_voice = ScreenVoice(name='screen_voice', deepvoicedetector=deepvoicedetector)
    screen_video_voice_manager.add_widget(screen_voice)

    return screen_video_voice_manager

