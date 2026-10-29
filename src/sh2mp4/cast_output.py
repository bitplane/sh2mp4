"""Render asciinema's timed JSON stream and record the actual playback boundaries."""

import json
import sys
import time
from pathlib import Path


def render(stream, output, timing_path):
    # asciinema emits its header before the timed events.
    header = json.loads(next(stream))
    if not isinstance(header, dict):
        raise ValueError("Missing asciicast playback header")
    start = None
    end = None
    for line in stream:
        timestamp, kind, data = json.loads(line)
        now = time.time()
        if start is None:
            # Asciinema --out-fmt emits already speed-adjusted timestamps.
            start = now - timestamp
        if kind == "o":
            output.write(data)
            output.flush()
        end = now
    if start is None:
        start = end = time.time()
    timing_path.write_text(json.dumps({"start": start, "end": end}))


def main():
    render(iter(sys.stdin), sys.stdout, Path(sys.argv[1]))


if __name__ == "__main__":
    main()
