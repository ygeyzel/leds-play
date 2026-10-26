import pygame

from platforms.interfaces import AudioPlayer


class PygameAudioPlayer(AudioPlayer):
    """pygame.mixer-backed audio, shared by both backends: background music
    on the dedicated music channel (pygame.mixer.music), sound effects as
    one-shot Sounds on whatever free channel pygame picks - the two never
    fight each other, so a sound effect never interrupts the music.

    Audio is optional: if no output device can be opened, every call is a
    no-op rather than a crash."""

    def __init__(self):
        try:
            pygame.mixer.init()
            self._available = True
        except pygame.error as e:
            print(f"warning: no audio output, running without sound ({e})")
            self._available = False
        self._muted = False
        self._bgm_path = None
        self._bgm_loop = True

    def play_bgm(self, path: str, loop: bool = True):
        self._bgm_path = path
        self._bgm_loop = loop
        if self._available and not self._muted:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1 if loop else 0)

    def stop_bgm(self):
        self._bgm_path = None
        if self._available:
            pygame.mixer.music.stop()

    def play_sfx(self, path: str):
        if self._available and not self._muted:
            pygame.mixer.Sound(path).play()

    def set_muted(self, muted: bool):
        if muted == self._muted:
            return
        self._muted = muted
        if not self._available:
            return
        if muted:
            pygame.mixer.music.stop()
        elif self._bgm_path:
            pygame.mixer.music.load(self._bgm_path)
            pygame.mixer.music.play(-1 if self._bgm_loop else 0)
