# 🎥 sh2mp4

Records a shell command to an MP4 video, using xterm in a hidden desktop session.

This version is now written in Python. Use `uvx sh2mp4` or `pipx sh2mp4` to execute.

## Usage

```bash
$ sh2mp4 "command to run" [output.mp4]
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

## Fonts

Font size is configurable (default 12pt). Character dimensions are automatically
calculated based on the font size. Supported sizes: 4, 6, 8, 10, 12, 14, 16, 18, 20.
Run `python3 measure_fonts.py` to see pixel dimensions for all available fonts and sizes.

## Themes

Available themes:
- `sh2mp4`: Custom theme optimized for video recording (default)
- `tango`: Tango-based theme
- `dark`: High-contrast dark theme
- `light`: Light theme
- `solarized-dark`: Solarized Dark theme

You can customize or add new themes in the `themes.sh` file.

## Deps

See/run `./configure` for a list. There's a few, so you might wanna run it in a
container.

## License

WTFPL with one additional clause:

* 🛑 Don't blame me

Do wtf you want, but you're on your own.

## Links

* [🏠 home](https://bitplane.net/dev/sh/sh2mp4)
* [🐱 github](https://github.com/bitplane/sh2mp4)

### See also

* [📺 tvmux](https://bitplane.net/dev/sh/tvmux) -
  a tmux recorder using asciinema.

