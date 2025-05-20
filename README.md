# 🎥 sh2mp4

Records a shell script to mp4.

```bash
$ ./sh2mp4.sh "command to run" [output.mp4] [cols] [lines] [fps] [font]
```

I set up a stdbuf fifo so you should be able to pipe stuff like keypresses
in, but it's untested and you won't be able to see what you're doing
either. Might be useful though.

## Defaults

| arg     | value            | description                           |
| ------- | ---------------- | ------------------------------------- |
| command | (required)       | Command or script to run in recording |
| output  | output.mp4       | Output file name                      |
| cols    | `$(tput cols)`   | Terminal width in characters          |
| lines   | `$(tput rows)`   | Terminal height in characters         |
| fps     | 30               | Frames per second for recording       |
| font    | DejaVu Sans Mono | Font to use (must be monospace)       |

## Fonts

Font size is fixed at 6pt, which is 5x10 pixels per character in most
monospaced fonts. If you want to change that, run the python script to
get dimensions and hack your changes in.

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

* [📺 tvmux](https://bitplane.net/sh/tvmux) -
  a tmux recorder using asciinema.

