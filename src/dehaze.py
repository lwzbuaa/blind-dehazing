import cv2
import cPickle
import logging
import os
import sys
import yaml
import numpy as np
import time

from bunch import bunchify

# Our module imports
import steps

from config.arguments import parser
from tools import show_img


logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

PATCH_SIZE = 7


def save(img_file, patches, pairs):
    with open(img_file.split('.')[0] + '.patches', 'wb') as f:
        cPickle.dump(patches, f)
    with open(img_file.split('.')[0] + '.pairs', 'wb') as f:
        cPickle.dump(pairs, f)


def load(img_file):
    if not os.path.exists(img_file.split('.')[0] + '.patches'):
        return None, None
    with open(img_file.split('.')[0] + '.patches', 'rb') as f:
        patches = cPickle.load(f)
    with open(img_file.split('.')[0] + '.pairs', 'rb') as f:
        pairs = cPickle.load(f)
    return patches, pairs


def main():
    args = parser.parse_args()
    with open(args.constants, 'r') as f:
        constants = bunchify(yaml.load(f))

    logger.info("Loading image %s ..." % args.input)
    img = cv2.imread(args.input, flags=cv2.IMREAD_COLOR)
    # image scaled in 0-1 range
    img = img / 255.0
    # Scale array must be in decreasing order
    scaled_imgs = steps.scale(img, [1, 0.75, 0.5, 0.375, 0.3, 0.25])

    if not args.no_cache:
        patches, pairs = load(args.input)
    else:
        patches, pairs = None, None
    if patches is None and pairs is None:
        logger.info("Extracting patches ...")
        patches = steps.generate_patches(scaled_imgs, constants)

        logger.info("Generating pairs of patches ...")
        pairs = steps.generate_pairs(patches, constants)

        logger.info("Saving patches and pairs ...")
        save(args.input, patches, pairs)
    else:
        logger.info("Using saved patches and pairs ...")

    logger.info("Filtering pairs of patches and estimating local airlight ...")
    pairs = steps.filter_pairs(patches, pairs, constants)
    import pdb; pdb.set_trace()
    sum1 = np.zeros((len(pairs), 3))
    for i, pair in enumerate(pairs):
        sum1[i] = pair.airlight
    print np.mean(sum1, axis=0)

    logger.info("Removing outliers ...")
    pairs = steps.remove_outliers(pairs, constants)

    logger.info("Estimating global airlight ...")
    airlight = steps.estimate_airlight(pairs)

    logger.info("Estimatied airlight is ...")

if __name__ == '__main__':
    main()
