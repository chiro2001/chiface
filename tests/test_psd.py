from psd_tools import PSDImage
import cv2
import numpy as np

psd_file = "./actors/0/mahilo.psd"
# psd_file = "./out.psd"

class Actor:
    def __init__(self, psd_file: str = None, psd: PSDImage = None):
        self.psd = psd
        if self.psd is None:
            self.psd = PSDImage.open(psd_file)
        self.tree: dict = None
        self.reset()
    
    @staticmethod
    def disable_layers(layers):
        if isinstance(layers, dict):
            for key in layers:
                layers[key].visible = False
        elif isinstance(layers, list):
            for layer in layers:
                layer.visible = False
        else:
            layers.visible = False
    
    def reset(self):
        self.tree = scan_psd_tree(self.psd)
        self.disable_layers(self.tree['嘴']['开启'])
        self.disable_layers(self.tree['嘴']['闭合']['窄'])
        self.disable_layers(self.tree['眼']['闭合'])
        self.disable_layers(self.tree['眉'])
    
    def get_image(self) -> np.ndarray:
        return psd2image(self.psd)


def scan_psd_tree(parent) -> dict:
    tree = {}
    for layer in parent:
        if layer.is_group():
            tree[layer.name] = scan_psd_tree(layer)
        else:
            tree[layer.name] = layer
    return tree

def psd2image(psd) -> np.ndarray:
    comp = psd.composite(ignore_preview=True, force=True)
    image = cv2.cvtColor(np.array(comp), cv2.COLOR_RGBA2BGRA)
    return image

# psd = PSDImage.open(psd_file)
# tr = scan_psd_tree(psd)
# # print(tr)

# im = psd2image(psd)
# print(im.shape)
# cv2.imshow("comp", im)
# # cv2.waitKey(0)

# # tr['嘴']['开启']['宽'].visible = not tr['嘴']['开启']['宽'].visible
# # tr['嘴']['闭合']['宽'].visible = not tr['嘴']['闭合']['宽'].visible
# tr['嘴']['闭合']['宽'].visible = False
# # tr['嘴']['开启']['宽'].visible = True
# # print(tr)
# im = psd2image(psd)
# cv2.imshow("comp2", im)
# # cv2.waitKey(1000)

# tr['嘴']['闭合']['宽'].visible = True
# im = psd2image(psd)
# cv2.imshow("comp3", im)
# cv2.waitKey(1000)

def main():
    actor = Actor(psd_file=psd_file)
    im = actor.get_image()
    cv2.imshow("im", im)
    cv2.waitKey(0)

if __name__ == '__main__':
    main()
