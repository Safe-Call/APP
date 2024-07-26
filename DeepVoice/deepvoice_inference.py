import torch
import torchaudio
import torchvision
import torch.nn as nn
from PIL import Image
from argparse import ArgumentParser

import timm
import numpy as np


class DeepVoiceInference:
    def __init__(self):
        super().__init__()
        self.model = timm.create_model('repvgg_a2.rvgg_in1k', pretrained=False, exportable=True, num_classes=2)
        self.model.load_state_dict(torch.load('Detectors/DeepVoice/a2_ckpt_93.92.pth.tar', map_location='cpu'))
        self.model.eval()

    def make_spectrogram(self, data, sr):
        SAMPLE_RATE = 8000
        WIN_LENGTH = None
        N_FFT = 512
        HOP_SIZE = N_FFT // 2
        N_MELS = 60

        transform = nn.Sequential(
            torchaudio.transforms.Resample(orig_freq=sr, new_freq=SAMPLE_RATE),
            torchaudio.transforms.MelSpectrogram(sample_rate=SAMPLE_RATE, win_length=WIN_LENGTH, n_fft=N_FFT,
                                                 n_mels=N_MELS, normalized=True, hop_length=HOP_SIZE),
            torchaudio.transforms.AmplitudeToDB(),
        )
        # 모노채널로 변환
        data = torch.Tensor(data)
        # Transform 수행
        output = transform(data)

        return output

    def to_rgb(self, t_img: torch.Tensor):
        output = t_img.expand((3, -1, -1))
        return output.unsqueeze(0)

    def run(self, x, sr):
        x_mel = self.make_spectrogram(x, sr)
        x_input = self.to_rgb(torchvision.transforms.Resize((128, 128))(x_mel.unsqueeze(0)))

        with torch.no_grad():
            output = self.model(x_input)

        output = nn.functional.softmax(output)

        return output.detach().numpy()[0][1]



