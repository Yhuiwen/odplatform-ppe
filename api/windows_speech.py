"""Pre-generate bounded fixed WAV prompts; playback owns no speech synthesis."""
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import wave

PROMPTS = ('未佩戴安全帽', '未穿反光背心', 'PPE 状态未知')


class WindowsSpeech:
    def __init__(self, rate=180, volume=1.0):
        self.rate = max(-10, min(10, int(math.log(rate / 200, 1.1))))
        self.volume = int(round(volume * 100))
        self.cache = None
        self.files = {}

    def prepare(self):
        if self.files:
            return
        from win32com.client import Dispatch
        self.cache = TemporaryDirectory(prefix='ppe-alert-audio-')
        try:
            for index, text in enumerate(PROMPTS):
                path = Path(self.cache.name) / f'{index}.wav'
                voice = Dispatch('SAPI.SpVoice')
                stream = Dispatch('SAPI.SpFileStream')
                stream.Open(str(path), 3, False)
                try:
                    voice.Rate = self.rate
                    voice.Volume = self.volume
                    voice.AudioOutputStream = stream
                    voice.Speak(text, 0)
                finally:
                    stream.Close()
                with wave.open(str(path), 'rb') as audio:
                    if audio.getnframes() <= 0:
                        raise RuntimeError('Empty speech WAV')
                self.files[text] = path
        except Exception:
            self.close()
            raise

    def __call__(self, text):
        if text not in PROMPTS:
            raise ValueError('Unsupported speech prompt')
        if text not in self.files:
            raise RuntimeError('Speech audio is not prepared')
        import winsound
        winsound.PlaySound(str(self.files[text]), winsound.SND_FILENAME | winsound.SND_NODEFAULT)

    def close(self):
        self.files.clear()
        if self.cache is not None:
            self.cache.cleanup()
            self.cache = None
