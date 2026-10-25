from platforms.interfaces import AudioPlayer


class RpiAudioPlayer(AudioPlayer):
    """No-op stub - real Pi audio hardware (speaker/DAC, GPIO/I2S wiring)
    isn't implemented yet, same pattern create_matrix/create_banner_matrix
    already use for other rpi/sim capability gaps."""

    def play_bgm(self, path: str, loop: bool = True):
        pass

    def stop_bgm(self):
        pass

    def play_sfx(self, path: str):
        pass

    def set_muted(self, muted: bool):
        pass
