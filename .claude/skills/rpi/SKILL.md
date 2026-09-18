---
name: rpi
description: Run this repo's code on the Raspberry Pi over SSH (rpi mode, hardware tests, one-off commands on the Pi). Reads connection info from .rpi-ssh.json and syncs the repo to the Pi first unless the folder is mounted from it. Use whenever the task needs real hardware (LED matrix, GPIO buttons, serial score display) or anything that has to execute on the Pi.
---

# Working on the Raspberry Pi

All Pi access goes through `.claude/skills/rpi/scripts/rpi.py`. It reads the
connection settings from `.rpi-ssh.json`, so don't hand-write `ssh`/`rsync`
commands.

## Config: `.rpi-ssh.json` (repo root, gitignored)

```json
{
  "host": "10.0.0.7",
  "username": "pi",
  "identities": ["~/.ssh/id_rsa"],
  "port": 22,
  "is_mounted": false,
  "remote_dir": "~/leds-play",
  "sudo-password": "..."
}
```

- `host`, `username`: required. `identities`, `port`: optional.
- `is_mounted` (default **false**): `true` means this local folder *is* the
  Pi's `remote_dir` (e.g. an sshfs mount), so edits are already on the Pi and
  no sync happens. When `false`, every `run` rsyncs the repo to the Pi first.
- `remote_dir` (default `~/leds-play`): where the code lives on the Pi. When
  mounted, it must be the directory that's mounted here.
- `sudo-password` (optional): used by `run --sudo`. Never print it, echo it,
  or put it on a command line; `info` shows it as `<set>`.

If the file is missing, ask the user for the details rather than guessing.

## Commands

Run from the repo root:

```bash
S=.claude/skills/rpi/scripts/rpi.py
python3 $S info                     # show resolved config + ssh command
python3 $S sync                     # push repo to the Pi (no-op if mounted)
python3 $S setup                    # create .venv-rpi on the Pi, pip install requirements-rpi.txt
python3 $S run -- python main.py    # sync (if needed), cd remote_dir, run
python3 $S run --sudo -- python main.py   # same, as root
python3 $S ssh -- uptime            # raw command on the Pi, no cd/sync
python3 $S ssh -- 'ls /tmp | wc -l' # single arg = shell snippet
```

`run` executes inside `remote_dir` and replaces a leading `python`/`python3`
with the Pi's `.venv-rpi/bin/python` when that venv exists. Sync excludes `.git/`,
`.venv/`, `.venv-rpi/`, `__pycache__/`, `.best_score`, `.rpi-ssh.json` and `.claude/`, and
those are never deleted on the Pi either.

## Things to know

- **Dependencies**: `rpi` mode needs `Adafruit-Blinka-Raspberry-Pi5-Neopixel`, `lgpio`, `pyserial` on the
  Pi. If `run` fails with `ModuleNotFoundError`, run `setup` (it installs
  into a Pi-side `.venv-rpi`, separate from the local uv `.venv` since the repo may be an sshfs mount of the Pi; created with `--system-site-packages` so the apt-provided `python3-lgpio` / `python3-rpi-lgpio` are used instead of building `lgpio` from source, which needs `swig`) — tell the user before doing so, since it installs
  packages on their device.
- **Root**: the WS281x LED driver normally needs root, so run hardware code
  with `--sudo`. The password from `sudo-password` goes to the Pi over SSH
  stdin and is fed to `sudo -A` through a one-shot askpass helper in a
  private temp dir, which is deleted after use. If `sudo-password` isn't set,
  `--sudo` falls back to `sudo -n` (passwordless sudo only).
- **Long-running / interactive programs**: `main.py` is an endless game loop,
  and `tests/*.py` block on `input()` and need a human at the physical
  buttons. Don't run these in the foreground without a timeout: use a Bash
  `timeout` or `run_in_background`, and for the interactive tests ask the
  user to run them in their own terminal with `-t`, e.g.
  `python3 .claude/skills/rpi/scripts/rpi.py run -t -- python -m tests.test_keys`.
- The LED matrix keeps its last frame if a process is killed mid-run; that's
  expected, not a bug in your change.
- Keep hardware imports confined to `hardware/rpi/` (see CLAUDE.md) — being
  able to run on the Pi is not a reason to import `RPi.GPIO`/`adafruit_raspberry_pi5_neopixel_write`
  elsewhere.
