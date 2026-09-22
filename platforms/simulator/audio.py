import pygame

from platforms.interfaces import AudioPlayer


class SimulatorAudioPlayer(AudioPlayer):
    """pygame.mixer-backed audio: background music on the dedicated music
    channel (pygame.mixer.music), sound effects as one-shot Sounds on
    whatever free channel pygame picks - the two never fight each other,
    so a sound effect never interrupts the music."""

    def __init__(self):
        pygame.mixer.init()
        self._muted = False
        self._bgm_path = None
        self._bgm_loop = True

    def play_bgm(self, path: str, loop: bool = True):
        self._bgm_path = path
        self._bgm_loop = loop
        if not self._muted:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1 if loop else 0)

    def stop_bgm(self):
        self._bgm_path = None
        pygame.mixer.music.stop()

    def play_sfx(self, path: str):
        if not self._muted:
            pygame.mixer.Sound(path).play()

    def set_muted(self, muted: bool):
        if muted == self._muted:
            return
        self._muted = muted
        if muted:
            pygame.mixer.music.stop()
        elif self._bgm_path:
            pygame.mixer.music.load(self._bgm_path)
            pygame.mixer.music.play(-1 if self._bgm_loop else 0)
