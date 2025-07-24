# 🎥 sh2mp4

Records a shell command to an MP4 video, using xterm in a hidden desktop session.

This version is now written in Python. Use `uvx sh2mp4` or `pipx sh2mp4` to execute.

## Usage

### Record commands
```bash
# Basic recording
$ sh2mp4 "command to run" [output.mp4]

# With custom settings
$ sh2mp4 "htop" demo.mp4 --cols 120 --lines 40 --theme dark --font-size 14

# Live preview while recording
$ sh2mp4 "sl" train.mp4 --watch
```

### Convert asciinema recordings
```bash
# Convert .cast files to MP4 (with window size optimization)
$ sh2mp4 --cast-file recording.cast output.mp4

# Fast conversion using speed multiplier (8x faster conversion time)
$ sh2mp4 --cast-file recording.cast output.mp4 --speed 8x

# Apply theme and font settings to cast conversion
$ sh2mp4 --cast-file demo.cast demo.mp4 --theme solarized-dark --font-size 16

# Watch the conversion in real-time
$ sh2mp4 --cast-file demo.cast demo.mp4 --watch
```

### Utilities
```bash
# Check system dependencies
$ sh2mp4 --check-deps

# Measure available fonts and sizes
$ sh2mp4 --measure-fonts
```

## Defaults

| arg       | value            | description                           |
| --------- | ---------------- | ------------------------------------- |
| command   | (required)       | Command or script to run in recording |
| output    | output.mp4       | Output file name                      |
| cols      | `$(tput cols)`   | Terminal width in characters          |
| lines     | `$(tput rows)`   | Terminal height in characters         |
| fps       | 30               | Frames per second for recording       |
| font      | DejaVu Sans Mono | Font to use (must be monospace)       |
| font_size | 12               | Font size in points (4,6,8,10,12,14,16,18,20) |
| theme     | sh2mp4           | Terminal color theme                  |
| watch     | False            | Show live preview during recording    |
| cast_file | None             | Convert asciinema .cast file instead |
| speed     | None             | Speed multiplier for fast cast conversion (2x, 4x, 8x) |

## Fonts

Font size is configurable (default 12pt). Character dimensions are automatically
calculated based on the font size. Supported sizes: 4, 6, 8, 10, 12, 14, 16, 18, 20.
Run `sh2mp4 --measure-fonts` to see pixel dimensions for all available fonts and sizes.

## Themes

Available themes:
- `sh2mp4`: Custom theme optimized for video recording (default)
- `tango`: Tango-based theme
- `dark`: High-contrast dark theme
- `light`: Light theme
- `solarized-dark`: Solarized Dark theme

You can customize or add new themes in the `src/sh2mp4/themes.py` file.

## Speed Conversion

The `--speed` option accelerates cast file conversion without affecting the final video timing:

- **2x, 4x, 8x faster conversion**: A 10-minute cast file with `--speed 8x` converts in ~1.25 minutes
- **Real-time output**: Final MP4 plays at normal speed and maintains original timing
- **How it works**:
  1. Asciinema plays the cast file at accelerated speed (`--speed 8x`)
  2. FFmpeg records at higher frame rate (8x normal fps)
  3. Video is automatically slowed back down to real-time during encoding
- **Window optimization**: Automatically scans cast file for maximum terminal dimensions to prevent text wrapping

```bash
# Convert a long recording quickly
$ sh2mp4 --cast-file long-session.cast output.mp4 --speed 8x
```

## Dependencies

Run `sh2mp4 --check-deps` to see the full list of required system dependencies.
The main requirements are:
- ffmpeg (with libx264 support)
- Xvfb (virtual framebuffer)
- xterm (terminal emulator)
- openbox (window manager)
- Various X11 utilities (wmctrl, xdotool, unclutter)

You might want to run this in a container due to the number of dependencies.

## License

WTFPL with one additional clause:

* 🛑 Don't blame me

Do wtf you want, but you're on your own.

## Links

* [🏠 home](https://bitplane.net/dev/python/sh2mp4)
* [🐍 pypi](https://pypi.org/project/sh2mp4)
* [🐱 github](https://github.com/bitplane/sh2mp4)

### See also

* [📺 tvmux](https://bitplane.net/dev/sh/tvmux) -
  a tmux recorder using asciinema.

