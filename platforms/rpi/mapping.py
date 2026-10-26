import json
from pathlib import Path

MAPPING_PATH = Path(__file__).with_name("mapping.json")


def load_mapping() -> dict:
    """The rig's GPIO wiring: `leds_data_pin` (the board matrix's data pin),
    `leds_brightness` (0-1, scales the board matrix's colors) and `keys`
    ({key name: [button input pin, button LED output pin]})."""

    with open(MAPPING_PATH) as f:
        return json.load(f)
