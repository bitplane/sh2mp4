#!/bin/bash

watch -n 0.1 -t -c 'DISPLAY=:99 import -window root screenshot.png; chafa --polite=on -c 16 screenshot.png'
