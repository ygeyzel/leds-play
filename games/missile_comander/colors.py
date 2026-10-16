from enum import Enum


class HSVColor(Enum):
    """Full-spectrum rainbow, evenly spaced every 30 degrees of hue, at
    full saturation and full brightness. Each member's `.value` is a plain
    (hue, saturation, value) tuple — exactly what the rest of this codebase
    already expects (e.g. SHIP_COLOR_HSV = (240, 1, 1)).

    Use a member directly when you want a pure, vivid color:
        BORDER_COLOR_HSV = HSVColor.BLUE.value

    Use `.with_sv(...)` when you want this hue but muted, like the
    existing BORDER_COLOR_HSV = (200, 0.7, 0.6):
        BORDER_COLOR_HSV = HSVColor.AZURE.with_sv(0.7, 0.6)
    """

    RED = (0, 1, 1)
    ORANGE = (30, 1, 1)
    YELLOW = (60, 1, 1)
    CHARTREUSE = (90, 1, 1)
    GREEN = (120, 1, 1)
    SPRING_GREEN = (150, 1, 1)
    CYAN = (180, 1, 1)
    AZURE = (210, 1, 1)
    BLUE = (240, 1, 1)
    VIOLET = (270, 1, 1)
    MAGENTA = (300, 1, 1)
    ROSE = (330, 1, 1)

    def with_sv(self, saturation, value):
        """Returns this hue as a plain (h, s, v) tuple with a custom
        saturation/value instead of the default full (1, 1) — e.g. for a
        dim border or a pale pastel version of the same color."""
        hue, _, _ = self.value
        return (hue, saturation, value)


# A few fixed neutrals that don't fit on the hue wheel (hue is meaningless
# when saturation is 0), kept separate so HSVColor stays a pure rainbow.
class HSVNeutral(Enum):
    WHITE = (0, 0, 1)
    GRAY = (0, 0, 0.5)
    BLACK = (0, 0, 0)