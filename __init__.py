

from .color_detector_node import Img2ColorNode        

__node_name = "Img2Color - Color Palette Extractor"
NODE_CLASS_MAPPINGS = {
    "bmy_Img2ColorNode": Img2ColorNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "bmy_Img2ColorNode": __node_name
}

# WEB_DIRECTORY = "./web"