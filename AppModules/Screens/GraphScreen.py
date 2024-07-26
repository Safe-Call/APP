import os
import numpy as np

from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy_garden.graph import Graph, MeshLinePlot
from kivy.clock import Clock


class ScreenVoid(GridLayout):
    def __init__(self, screen_graph_manager):
        super().__init__()
        self.cols = 1
        self.rows = 2
        self.screen_graph_manager = screen_graph_manager
        fontName = '/'.join([os.getenv('SystemRoot'), '/fonts/gulim.ttc'])

        # 버튼 부분
        self.button = Button(text="자세히 버튼", size_hint_y=None, font_name=fontName, font_size=15)
        self.button.bind(on_press=self.change_to_detail)
        self.add_widget(self.button)

    def change_to_detail(self, instance):
        print('디테일 페이지로 넘어가기')
        self.screen_graph_manager.current = "screen_graph"


class ScreenGraph(GridLayout):
    def __init__(self, screen_graph_manager, screen_video_voice_manager):
        super().__init__()
        self.cols = 1
        self.rows = 2
        self.screen_graph_manager = screen_graph_manager
        self.screen_video_voice_manager = screen_video_voice_manager
        fontName = '/'.join([os.getenv('SystemRoot'), '/fonts/gulim.ttc'])

        # 버튼 부분
        self.button = Button(text="자세히 버튼", size_hint_y=None, font_name=fontName, font_size=15)
        self.button.bind(on_press=self.change_to_detail)
        self.add_widget(self.button)

        # 디테일 부분
        self.graph = Graph(xlabel='X', ylabel='Y', x_ticks_minor=5,
                           x_ticks_major=25, y_ticks_major=1,
                           y_grid_label=True, x_grid_label=True, padding=5,
                           x_grid=True, y_grid=True, xmin=0, xmax=100, ymin=0, ymax=1)
        # self.plot = MeshLinePlot()
        self.plot_colors = [
            [1, 0, 0, 1],  # Red (Video)
            [0, 1, 0, 1],  # Green (Voice)
        ]
        # self.plot.line_width = 2  # 선 두께를 두껍게 설정
        # self.graph.add_plot(self.plot)
        self.threshold = 0.25
        self.threshold_line = MeshLinePlot(color=[1, 0, 1, 1]) # Magenta
        self.threshold_line.line_width = 2
        self.graph.add_plot(self.threshold_line)

        self.plots = []

        self.add_widget(self.graph)
        Clock.schedule_interval(self.graph_update, 1.0 / 2.0)

    def graph_update(self, dt):
        try:
            current_screen = self.screen_video_voice_manager.current
            if current_screen == "screen_video":
                file_path = "AppModules/detection_log/video_log.txt"
            elif current_screen == "screen_voice":
                file_path = "AppModules/detection_log/audio_log.txt"
            else:
                file_path = "AppModules/detection_log/cam_log.txt"

            detection_prov = np.loadtxt(file_path, delimiter=" ", unpack=False)

            x = np.arange(detection_prov.shape[0])

            # Clear previous plots
            for plot in self.plots:
                self.graph.remove_plot(plot)
            self.plots.clear()

            if len(detection_prov.shape) == 1:  # If the data is a single line
                if current_screen == 'screen_video':
                    color = self.plot_colors[0]
                else:
                    color = self.plot_colors[1]

                plot = MeshLinePlot(color=color)
                plot.line_width = 2
                y = detection_prov
                plot.points = [(xi, yi) for xi, yi in zip(x, y)]
                self.graph.add_plot(plot)
                self.plots.append(plot)

            else:
                # Multiple plots if detection_prov has multiple columns
                for i in range(detection_prov.shape[1]):
                    color = self.plot_colors[i % len(self.plot_colors)]
                    plot = MeshLinePlot(color=color)
                    plot.line_width = 5  # 선 두께를 두껍게 설정
                    y = detection_prov[:, i]
                    plot.points = [(xi, yi) for xi, yi in zip(x, y)]
                    self.graph.add_plot(plot)
                    self.plots.append(plot)

            self.graph.xmax = max(0, len(x))
            # 임계값 수평선 업데이트
            self.threshold_line.points = [(0, self.threshold), (self.graph.xmax, self.threshold)]
        except Exception as e:
            print(f"Error reading or plotting data: {e}")

    def change_to_detail(self, instance):
        print('디테일 페이지로 넘어가기')
        self.screen_graph_manager.current = "screen_void"


def ScreenGraphManager(screen_video_voice_manager):
    screen_graph_manager = ScreenManager()
    screen_void = Screen(name='screen_void')
    screen_void.add_widget(ScreenVoid(screen_graph_manager))
    screen_graph_manager.add_widget(screen_void)

    screen_graph = Screen(name='screen_graph')
    screen_graph.add_widget(ScreenGraph(screen_graph_manager, screen_video_voice_manager))
    screen_graph_manager.add_widget(screen_graph)

    return screen_graph_manager
