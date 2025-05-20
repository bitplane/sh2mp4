# 🎥 sh2mp4

Records a shell script to mp4.

```bash
$ ./record.sh "command to run" [output.mp4] [cols] [lines] [fps]
```

## Defaults

| arg     | value      | description                           |
| ------- | ---------- | ------------------------------------- |
| command | (required) | Command or script to run in recording |
| output  | output.mp4 | Output file name                      |
| cols    | 136        | Terminal width in characters          |
| lines   | 41         | Terminal height in characters         |
| fps     | 30         | Frames per second for recording       |

