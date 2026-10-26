#!/usr/bin/env python3
"""Helper for running this repo on the Raspberry Pi over SSH.

Reads connection info from `.rpi-ssh.json` at the repo root:

    {
      "host": "10.0.0.7",            # required
      "username": "pi",              # required
      "identities": ["~/.ssh/id_rsa"],  # optional, passed as -i
      "port": 22,                    # optional
      "is_mounted": false,           # optional, default false
      "remote_dir": "~/leds-play",   # optional, default ~/leds-play
      "sudo-password": "..."         # optional, used by `run --sudo`
    }

`is_mounted: true` means this local folder *is* the Pi's `remote_dir`
(e.g. an sshfs mount), so no syncing is needed. Otherwise `sync` rsyncs the
repo to `remote_dir` before running.

Subcommands:
    info            print the resolved config and the ssh command
    sync            copy the repo to the Pi (no-op when mounted)
    setup           create .venv-rpi on the Pi and install requirements-rpi.txt
    run [-t] [--sudo] [--no-sync] -- CMD...
                    sync (unless mounted/--no-sync), then run CMD inside
                    remote_dir on the Pi, using .venv-rpi/bin/python if present.
                    --sudo uses `sudo-password` from the config when set
    ssh -- CMD...   run a raw command on the Pi (no cd, no sync); a single
                    argument is run as a shell snippet
"""
import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
CONFIG_PATH = REPO_ROOT / ".rpi-ssh.json"
DEFAULT_REMOTE_DIR = "~/leds-play"

# Never pushed to the Pi. Excluded paths are also protected from --delete, so
# Pi-side state like .venv-rpi/ and .best_score survives a sync.
RSYNC_EXCLUDES = [
    ".git/", ".venv/", ".venv-rpi/", "__pycache__/", "*.py[cod]", "*.swp",
    ".best_score", ".env", ".rpi-ssh.json", ".claude/",
]


def load_config():
    if not CONFIG_PATH.exists():
        sys.exit(f"error: {CONFIG_PATH} not found (see this script's docstring for the format)")
    cfg = json.loads(CONFIG_PATH.read_text())
    for key in ("host", "username"):
        if not cfg.get(key):
            sys.exit(f"error: {CONFIG_PATH.name} is missing '{key}'")
    cfg.setdefault("identities", [])
    cfg.setdefault("is_mounted", False)
    cfg.setdefault("remote_dir", DEFAULT_REMOTE_DIR)
    return cfg


def ssh_base(cfg, tty=False):
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]
    if tty:
        cmd.append("-t")
    if cfg.get("port"):
        cmd += ["-p", str(cfg["port"])]
    for identity in cfg["identities"]:
        cmd += ["-i", os.path.expanduser(identity)]
    return cmd + [f"{cfg['username']}@{cfg['host']}"]


def remote_dir_expr(cfg):
    """remote_dir as a shell word, letting the remote shell expand a leading ~."""
    remote_dir = cfg["remote_dir"]
    if remote_dir == "~" or remote_dir.startswith("~/"):
        return "~" + shlex.quote(remote_dir[1:]) if len(remote_dir) > 1 else "~"
    return shlex.quote(remote_dir)


def run_remote(cfg, script, tty=False):
    return subprocess.call(ssh_base(cfg, tty) + [script])


def stage_sudo_askpass(cfg):
    """Put a one-shot SUDO_ASKPASS helper on the Pi and return its directory.

    The password travels over ssh stdin, so it never shows up in a command
    line (`ps`) on either machine. The helper deletes itself (and the
    password) on first use; `run` also removes it on exit as a fallback.
    """
    script = (
        'umask 077; d=$(mktemp -d) && cat > "$d/pw" && '
        """printf '#!/bin/sh\\ncat "%s/pw"\\nrm -rf "%s"\\n' "$d" "$d" > "$d/askpass" && """
        'chmod 700 "$d/askpass" && echo "$d"'
    )
    result = subprocess.run(ssh_base(cfg) + [script], input=cfg["sudo-password"] + "\n",
                            capture_output=True, text=True)
    if result.returncode:
        sys.exit(f"error: couldn't stage sudo askpass on the Pi: {result.stderr.strip()}")
    return result.stdout.strip()


def sync(cfg):
    if cfg["is_mounted"]:
        print(f"[rpi] {REPO_ROOT} is mounted on the Pi, skipping sync", file=sys.stderr)
        return 0
    rc = run_remote(cfg, f"mkdir -p {remote_dir_expr(cfg)}")
    if rc:
        return rc
    rsh = " ".join(shlex.quote(part) for part in ssh_base(cfg)[:-1])
    remote_dir = cfg["remote_dir"]
    if remote_dir.startswith("~/"):
        remote_dir = remote_dir[2:]  # rsync paths are relative to the remote home
    cmd = ["rsync", "-az", "--delete", "-e", rsh]
    cmd += [f"--exclude={pattern}" for pattern in RSYNC_EXCLUDES]
    cmd += [f"{REPO_ROOT}/", f"{cfg['username']}@{cfg['host']}:{remote_dir}/"]
    print(f"[rpi] syncing {REPO_ROOT} -> {cfg['host']}:{cfg['remote_dir']}", file=sys.stderr)
    return subprocess.call(cmd)


def cmd_info(cfg, _args):
    shown = dict(cfg)
    if shown.get("sudo-password"):
        shown["sudo-password"] = "<set>"
    print(json.dumps(shown, indent=2))
    print("ssh:", shlex.join(ssh_base(cfg)))
    return 0


def cmd_sync(cfg, _args):
    return sync(cfg)


def cmd_setup(cfg, _args):
    script = (
        f"cd {remote_dir_expr(cfg)} && "
        "{ [ -x .venv-rpi/bin/python ] || python3 -m venv --system-site-packages .venv-rpi; } && "
        ".venv-rpi/bin/pip install -r requirements-rpi.txt"
    )
    return run_remote(cfg, script)


def cmd_run(cfg, args):
    if not args.command:
        sys.exit("error: nothing to run (usage: run -- python main.py)")
    if not args.no_sync:
        rc = sync(cfg)
        if rc:
            return rc
    command = list(args.command)
    # Prefer the Pi-side venv's interpreter over the system python.
    if command[0] in ("python", "python3"):
        command[0] = '"$PY"'
    else:
        command[0] = shlex.quote(command[0])
    command = [command[0]] + [shlex.quote(part) for part in command[1:]]
    prefix = ""
    script = ""
    if args.sudo and cfg.get("sudo-password"):
        askpass_dir = shlex.quote(stage_sudo_askpass(cfg))
        script = f"trap 'rm -rf {askpass_dir}' EXIT HUP INT TERM; "
        prefix = f"SUDO_ASKPASS={askpass_dir}/askpass sudo -A "
    elif args.sudo:
        prefix = "sudo -n "
    script += (
        f"cd {remote_dir_expr(cfg)} && "
        'if [ -x .venv-rpi/bin/python ]; then PY="$PWD/.venv-rpi/bin/python"; else PY=python3; fi && '
        f"{prefix}{' '.join(command)}"
    )
    return run_remote(cfg, script, tty=args.tty)


def cmd_ssh(cfg, args):
    if not args.command:
        sys.exit("error: nothing to run")
    # A single argument is taken as a shell snippet (pipes, globs, ...).
    script = args.command[0] if len(args.command) == 1 else shlex.join(args.command)
    return run_remote(cfg, script, tty=args.tty)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="subcommand", required=True)
    sub.add_parser("info").set_defaults(func=cmd_info)
    sub.add_parser("sync").set_defaults(func=cmd_sync)
    sub.add_parser("setup").set_defaults(func=cmd_setup)
    run = sub.add_parser("run")
    run.add_argument("-t", "--tty", action="store_true", help="allocate a TTY (interactive programs)")
    run.add_argument("--sudo", action="store_true", help="run under sudo, using sudo-password from the config (else sudo -n)")
    run.add_argument("--no-sync", action="store_true", help="skip syncing even when not mounted")
    run.add_argument("command", nargs=argparse.REMAINDER)
    run.set_defaults(func=cmd_run)
    raw = sub.add_parser("ssh")
    raw.add_argument("-t", "--tty", action="store_true")
    raw.add_argument("command", nargs=argparse.REMAINDER)
    raw.set_defaults(func=cmd_ssh)

    args = parser.parse_args()
    if getattr(args, "command", None) and args.command[0] == "--":
        args.command = args.command[1:]
    sys.exit(args.func(load_config(), args))


if __name__ == "__main__":
    main()
