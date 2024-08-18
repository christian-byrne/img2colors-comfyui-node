"""
@author: christian-byrne
@title: Img2Color Node - Detect and describe color palettes in images
@nickname: img2color
@description:
"""

import torch
import webcolors
from colornamer import get_color_from_rgb
from numpy import ndarray
from sklearn.cluster import KMeans

from typing import Tuple, List, Dict, Any, Optional


class Img2ColorNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input_image": ("IMAGE",),
            },
            "optional": {
                "num_colors": (
                    "INT",
                    {
                        "default": 5,
                        "min": 1,
                        "max": 128,
                        "tooltip": "Number of colors to detect",
                    },
                ),
                "get_complementary": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "label_off": "Get Original Colors",
                        "label_on": "Get Complementary Colors",
                        "tooltip": "Get the complementary colors of the detected palette",
                    },
                ),
                "k_means_algorithm": (
                    ["lloyd", "elkan", "auto", "full"],
                    {
                        "default": "lloyd",
                    },
                ),
                "accuracy": (
                    "INT",
                    {
                        "default": 60,
                        "display": "slider",
                        "min": 1,
                        "max": 100,
                        "tooltip": "Adjusts accuracy by changing number of iterations of the K-means algorithm",
                    },
                ),
                "exclude_colors": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Comma-separated list of colors to exclude from the output",
                    },
                ),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "output_text": (
                    "STRING",
                    {
                        "default": "",
                    },
                ),
            },
        }

    RETURN_TYPES = (
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "STRING",
    )
    RETURN_NAMES = (
        "plain_english_colors",
        "rgb_colors",
        "hex_colors",
        "xkcd_colors",
        "design_colors",
        "common_colors",
        "color_types",
        "color_families",
    )
    OUTPUT_TOOLTIPS = (
        "Plain English Colors correspond to the closest named color in the CSS3, CSS2, CSS21, and HTML4 color dictionaries.",
        'RGB Colors are in the format "rgb(255, 0, 255)"',
        "Hex Colors are in the format #RRGGBB",
        "XKCD Color is the finest level of granularity, and corresponds to the colors in the XKCD color survey. There are about 950 colors in this space.",
        "Design Color is the next coarsest level. There are about 250 Design Colors",
        "Common Color is the next coarsest level. There are about 120 Common Colors. This is probably the most useful level for most purposes.",
        "Color Type is another dimension that tells, roughly, how light, dark or saturated a color is. There are 11 color types.",
        "Color Family is even coarser, and has 26 families. These are all primary, secondary, or tertiary colors, or corresponding values for neutrals.",
    )
    FUNCTION = "main"
    OUTPUT_NODE = True
    CATEGORY = "img2txt"

    def main(
        self,
        input_image: torch.Tensor,  # [Batch_n, H, W, 3-channel]
        num_colors: int = 5,
        k_means_algorithm: str = "lloyd",
        accuracy: int = 80,
        get_complementary: bool = False,
        exclude_colors: str = "",
        output_text: str = "",
        unique_id=None,
        extra_pnginfo=None,
    ) -> Tuple[str, ...]:
        if exclude_colors.strip():
            self.exclude = exclude_colors.strip().split(",")
            self.exclude = [color.strip().lower() for color in self.exclude]
        else:
            self.exclude = []
        num_colors = max(1, num_colors)
        self.num_iterations = int(512 * (accuracy / 100))
        self.algorithm = k_means_algorithm
        self.webcolor_dict = {}
        for color_dict in [
            webcolors.CSS2_HEX_TO_NAMES,
            webcolors.CSS21_HEX_TO_NAMES,
            webcolors.CSS3_HEX_TO_NAMES,
            webcolors.HTML4_HEX_TO_NAMES,
        ]:
            self.webcolor_dict.update(color_dict)

        original_colors = self.interrogate_colors(
            input_image, num_colors, self.try_get_seed(extra_pnginfo)
        )
        rgb = self.ndarrays_to_rgb(original_colors)
        if get_complementary:
            rgb = self.rgb_to_complementary(rgb)

        plain_english_colors = [self.get_webcolor_name(color) for color in rgb]
        rgb_colors = [f"rgb{color}" for color in rgb]
        hex_colors = [f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}" for color in rgb]

        colornamer_names = self.get_colornamer_names(rgb)
        xkcd_colors = [color["xkcd_color"] for color in colornamer_names]
        design_colors = [color["design_color"] for color in colornamer_names]
        common_colors = [color["common_color"] for color in colornamer_names]
        color_types = [color["color_type"] for color in colornamer_names]
        color_families = [color["color_family"] for color in colornamer_names]

        return (
            self.join_and_exclude(plain_english_colors),
            self.join_and_exclude(rgb_colors),
            self.join_and_exclude(hex_colors),
            self.join_and_exclude(xkcd_colors),
            self.join_and_exclude(design_colors),
            self.join_and_exclude(common_colors),
            self.join_and_exclude(color_types),
            self.join_and_exclude(color_families),
        )

    def join_and_exclude(self, colors: List[str]) -> str:
        return ", ".join(
            [str(color) for color in colors if color.lower() not in self.exclude]
        )

    def get_colornamer_names(self, colors: List[Tuple[int, int, int]]) -> List[str]:
        return [get_color_from_rgb(color) for color in colors]

    def rgb_to_complementary(
        self, colors: List[Tuple[int, int, int]]
    ) -> List[Tuple[int, int, int]]:
        return [(255 - color[0], 255 - color[1], 255 - color[2]) for color in colors]

    def ndarrays_to_rgb(self, colors: List[ndarray]) -> List[Tuple[int, int, int]]:
        return [(int(color[0]), int(color[1]), int(color[2])) for color in colors]

    def interrogate_colors(
        self, image: torch.Tensor, num_colors: int, seed: Optional[int] = None
    ) -> List[ndarray]:
        pixels = image.view(-1, image.shape[-1]).numpy()
        colors = (
            KMeans(
                n_clusters=num_colors,
                algorithm=self.algorithm,
                max_iter=self.num_iterations,
                random_state=seed,
            )
            .fit(pixels)
            .cluster_centers_
            * 255
        )
        return colors

    def get_webcolor_name(self, rgb: Tuple[int, int, int]) -> str:
        closest_match = None
        min_distance = float("inf")

        for hex, name in self.webcolor_dict.items():
            distance = sum(abs(a - b) for a, b in zip(rgb, webcolors.hex_to_rgb(hex)))
            if distance < min_distance:
                min_distance = distance
                closest_match = name

        return closest_match

    def try_get_seed(self, extra_pnginfo: Dict[str, Any]) -> Optional[int]:
        try:
            for node in extra_pnginfo["workflow"]["nodes"]:
                if "Ksampler" not in node["type"]:
                    continue
                if isinstance(node["widgets_values"][0], (int, float)):
                    seed = node["widgets_values"][0]
                    if seed <= 0 or seed > 0xFFFFFFFF:
                        return None
                    return seed
        except Exception:
            pass
        return None
