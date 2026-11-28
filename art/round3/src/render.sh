#!/bin/bash
# 사용: render.sh <svg폴더> <크기>  -> 같은 폴더에 png
cd "$1" && inkscape --export-type=png --export-width=$2 *.svg >/dev/null 2>&1
