#!/bin/sh -e

cd "$(readlink -f $(dirname "$0"))"

# Pixel Code build script

# Activate python virtual environment.
../activate.sh
source ../.venv/bin/activate

# Build UFOs from images and fea files.
python3 build_from_images.py

# Variable font (experimental)
# fontmake ../build/PixelCode.designspace -o variable --output-dir ../dist/variable
# woff2_compress ../dist/variable/*.ttf

# Call fontmake to build the UFOs in to OTF and TTF fonts.
fontmake -u ../build/*.ufo -o otf --output-dir ../dist/otf
fontmake -u ../build/*.ufo -o ttf --output-dir ../dist/ttf

# Create woff2 fonts from the TTFs.
ls ../dist/ttf/*.ttf | xargs -I {} woff2_compress {}
mv ../dist/ttf/*.woff2 ../dist/woff2
