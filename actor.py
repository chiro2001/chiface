import psd_tools
from psd_tools import PSDImage
import cv2
import os
import sys
import json
import numpy as np
from base_logger import logger


class Actor:
    PATH_PREFIX = 'actors'

    def __init__(self, psd_file: str = None, psd: PSDImage = None):
        self.psd = psd
        self.psd_file = None
        self.config_file = None
        if self.psd is None and psd_file is not None:
            self.load(psd_file)
        self.tree: dict = None
        self.cached: np.ndarray = None
        self.adjust = {
            '眼': 0.2,
            '嘴': [0.2, 0.1],
            '眉': 0.9
        }
        self.edges = {
            '眼': 0.69,
            '嘴': [1.0, 1.0],
            '眉': [1.08, 1.2]
        }
        self.orders = {

        }
        self.target_info = {
            'resize': 0.8
        }
        self.reset()

    def __getstate__(self) -> dict:
        return {
            'psd_file': self.psd_file,
            'adjust': self.adjust,
            'edges': self.edges,
            'orders': self.orders,
            'target_info': self.target_info
        }

    def load(self, name: str, generate: bool = False):
        path = os.path.join(self.PATH_PREFIX, name)
        self.config_file = os.path.join(path, f"{name}.json")
        try:
            try:
                with open(self.config_file, "r", encoding='utf-8') as f:
                    config = json.load(f)
            except FileNotFoundError as e:
                if generate:
                    config = {}
                else:
                    raise e
            self.adjust = config.get('adjust', self.adjust)
            self.edges = config.get('edges', self.edges)
            self.orders = config.get('orders', self.orders)
            self.target_info = config.get('target_info', self.target_info)
            self.psd_file = config.get(
                'psd_file', os.path.join(path, f"{name}.psd"))
            self.psd = PSDImage.open(self.psd_file)
        except Exception as e:
            logger.error(str(e))
            # sys.exit(1)
            raise e
        self.save()
        self.reset()

    def save(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.__getstate__(), f, sort_keys=True, indent=2, ensure_ascii=False)

    @staticmethod
    def disable_layers(layers):
        if isinstance(layers, dict):
            for key in layers:
                if isinstance(layers[key], dict):
                    Actor.disable_layers(layers[key])
                else:
                    layers[key].visible = False
        elif isinstance(layers, list):
            for layer in layers:
                # layer.visible = False
                Actor.disable_layers(layer)
        else:
            layers.visible = False

    def reset(self):
        if self.psd is None:
            return
        self.tree = scan_psd_tree(self.psd)
        self.disable_layers([self.tree['嘴'], self.tree['眼'], self.tree['眉']])
        self.eye(self.eye()[0])
        self.eyebrow(self.eyebrow()[0])
        mouth_attrs = self.mouth()
        mouth_states = self.mouth(mouth_attrs[0])
        self.mouth(mouth_attrs[0], mouth_states[0])

    def get_image(self) -> np.ndarray:
        if self.cached is not None:
            return self.cached

        def f(x) -> list:
            r = []
            if not x.is_visible():
                return r
            if x.is_group():
                for i in x:
                    r.extend(f(i))
                return r
            else:
                return [x]
        temp = f(self.psd)
        # comp = self.psd.composite(ignore_preview=True)
        comp = psd_tools.compose(temp)
        im = cv2.cvtColor(np.array(comp), cv2.COLOR_RGBA2BGRA)
        im = cv2.resize(im, (int(im.shape[0] * self.target_info['resize']),
                        int(im.shape[1] * self.target_info['resize'])))
        if self.cached is None:
            self.cached = im
        return im

    def set_attr(self, attr: str, state: str):
        logger.debug(f'Try to set attr: {attr}.{state}...')
        if attr not in self.tree:
            logger.debug("attr not in self.tree")
            return False
        if state is None:
            logger.debug("state is None")
            return list(self.tree[attr].keys())
        if state not in self.tree[attr]:
            logger.debug("state not in self.tree[attr]")
            return False
        self.disable_layers(self.tree[attr])
        if not self.tree[attr][state].visible:
            self.cached = None
        self.tree[attr][state].visible = True
        logger.debug(f'set attr: {attr}.{state}')
        return True

    def eye(self, state: str = None):
        return self.set_attr('眼', state)

    def eyebrow(self, state: str = None):
        return self.set_attr('眉', state)

    def mouth(self, state: str = None, val: str = None):
        logger.debug(f'Try to set attr: 嘴.{state}.{val}...\t')
        if state is None:
            logger.debug("state is None")
            return list(self.tree['嘴'].keys())
        if val is None:
            logger.debug("val is None")
            return list(self.tree['嘴'][state].keys())
        if state not in self.tree['嘴']:
            logger.debug("state not in self.tree['嘴']")
            return False
        if val not in self.tree['嘴'][state]:
            logger.debug("val not in self.tree['嘴'][state]")
            return False
        self.disable_layers(self.tree['嘴'])
        logger.debug(f'set attr: 嘴.{state}.{val}')
        if not self.tree['嘴'][state][val].visible:
            self.cached = None
        self.tree['嘴'][state][val].visible = True
        return True


def scan_psd_tree(parent) -> dict:
    tree = {}
    for layer in parent:
        if layer.is_group():
            tree[layer.name] = scan_psd_tree(layer)
        else:
            tree[layer.name] = layer
    return tree


def main():
    psd_default = "./actors/mahilo/mahilo.psd"
    psd_file = psd_default
    actor = Actor(psd_file=psd_file)
    im = actor.get_image()
    cv2.imshow("im", im)
    cv2.waitKey(0)
    actor.mouth('开启', '窄')
    im = actor.get_image()
    cv2.imshow("im", im)
    cv2.waitKey(0)


if __name__ == '__main__':
    main()
