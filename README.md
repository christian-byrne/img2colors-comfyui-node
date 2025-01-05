
# Img2Color Palette Extractor ComfyUI Node

![alt text](https://github.com/christian-byrne/img2colors-comfyui-node/blob/demo-files/wiki/demo.png?raw=true)

- Uses KMeans clustering to extract the dominant colors from an image
- Uses `webcolors` and `colornamer` to get closest matching color names from various color naming systems
- `get_complementary` toggler to get the complementary colors instead


## Requirements

- colornamer==0.2.3
- scikit_learn>=1.4.0
- webcolors==1.13

## Installation

- If you use a virtual environment to run ComfyUI, activate it
- `cd` to the `ComfyUI/custom_nodes` directory
- `git clone` this repository
- `cd` to the `img2colors-comfyui-node` directory
- `pip install -r requirements.txt`


## Color Name Categories

- From webcolors: CSS3, CSS2, CSS2.1, and HTML4 webcolors
- From colornamer: XKCD, Design, Common, Color Families, Color or Neutral, Color Type
  - [Explanation of colornamer categories](https://github.com/stitchfix/colornamer?tab=readme-ov-file#interpreting-results)