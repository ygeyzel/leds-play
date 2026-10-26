import os
import pwd

from platforms.audio import PygameAudioPlayer


def _use_sudo_user_sound_server():
    """rpi mode runs under sudo (the LED driver needs root), but the sound
    server (PipeWire, whose default sink is the USB sound card) belongs to
    the desktop user's session. Without this, root's SDL falls back to bare
    ALSA, whose default card is HDMI - i.e. silence. Point it at the
    invoking user's Pulse socket instead."""

    sudo_user = os.environ.get("SUDO_USER")
    if not sudo_user or "PULSE_SERVER" in os.environ:
        return
    socket = f"/run/user/{pwd.getpwnam(sudo_user).pw_uid}/pulse/native"
    if os.path.exists(socket):
        os.environ["PULSE_SERVER"] = f"unix:{socket}"


class RpiAudioPlayer(PygameAudioPlayer):
    def __init__(self):
        _use_sudo_user_sound_server()
        super().__init__()
