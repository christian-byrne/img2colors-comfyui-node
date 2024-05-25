"""
@author: christian-byrne
@title: Img2Color Node - Detect and describe color palettes in images
@nickname: img2color
@description:
"""

import sys
import os
import torch
import webcolors
from colornamer import get_color_from_rgb
from numpy import ndarray
from sklearn.cluster import KMeans

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from typing import Tuple, List


class Img2ColorNode:
    CATEGORY = "img2txt"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input_image": ("IMAGE",),
            },
            "optional": {
                "num_colors": ("INT", {"default": 5}),
                "get_complementary": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "label_off": "Get Original Colors",
                        "label_on": "Get Complementary Colors",
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
                    },
                ),
                "exclude_colors": (
                    "STRING",
                    {
                        "default": "",
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
    FUNCTION = "main"
    OUTPUT_NODE = True

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

        self.num_iterations = int(512 * (accuracy / 100))
        self.algorithm = k_means_algorithm
        self.webcolor_dict = webcolors.CSS3_HEX_TO_NAMES
        self.webcolor_dict.update(
            webcolors.CSS2_HEX_TO_NAMES,
        )
        self.webcolor_dict.update(
            webcolors.CSS21_HEX_TO_NAMES,
        )
        self.webcolor_dict.update(
            webcolors.HTML4_HEX_TO_NAMES,
        )

        original_colors = self.interrogate_colors(input_image, num_colors)
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

    def interrogate_colors(self, image: torch.Tensor, num_colors: int) -> List[ndarray]:
        pixels = image.view(-1, image.shape[-1]).numpy()
        colors = (
            KMeans(
                n_clusters=num_colors,
                algorithm=self.algorithm,
                max_iter=self.num_iterations,
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
