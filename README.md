
# Img2Color Palette Extractor ComfyUI Node

![alt text](wiki/demo.png)

- Uses KMeans clustering to extract the dominant colors from an image
- Uses `webcolors` and `colornamer` to get closest matching color names from various color naming systems
- `get_complementary` toggler to get the complementary colors instead


## Requirements

- colornamer==0.2.3
- scikit_learn>=1.4.0
- webcolors==1.13

## Installation

- `cd` to the `ComfyUI` directory
- `git clone` this repository
- `cd` to the `img2colors-palette-detector` directory
- `pip install -r requirements.txt`


## Color Name Categories

- From webcolors: CSS3, CSS2, CSS2.1, and HTML4 webcolors
- From colornamer: XKCD, Design, Common, Color Families, Color or Neutral, Color Type
  - [Explanation of colornamer categories](https://github.com/stitchfix/colornamer?tab=readme-ov-file#interpreting-results)