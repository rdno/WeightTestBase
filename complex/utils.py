import numpy as np
import os
from pprint import pprint
from pytomo3d.utils.io import dump_json


def assert_file_exists(fn):
    if not os.path.exists(fn):
        raise ValueError("Missing file: %s" % fn)


def get_category_ratio(cat_wcounts):
    ratio = {}
    for p, pinfo in cat_wcounts.iteritems():
        ratio[p] = {}
        for c, cinfo in pinfo.iteritems():
            ratio[p][c] = 1.0 / cinfo

    return ratio


def overall_validator(weights, src_weights, rec_wcounts):
    nwins_list = []
    weights_list = []
    for p, pinfo in weights.iteritems():
        for chan, chaninfo in pinfo.iteritems():
            comp = chan.split(".")[-1]
            weights_list.append(chaninfo["weight"] * src_weights)
            nwins_list.append(rec_wcounts[p][comp][chan])

    sumv = np.dot(nwins_list, weights_list)
    print("Overall weights validator sum: %f" % sumv)
    if not np.isclose(sumv, 1.0):
        raise ValueError("Overall validator failed")


def analyze(weights, rec_wcounts, cat_wcounts, src_weights):
    overall_validator(weights, src_weights, rec_wcounts)

    results = {}
    for p, pinfo in weights.iteritems():
        results[p] = {}
        for chan, chaninfo in pinfo.iteritems():
            comp = chan.split(".")[-1]
            if comp not in results[p]:
                results[p][comp] = 0.0
            results[p][comp] += \
                chaninfo["weight"] * rec_wcounts[p][comp][chan] * src_weights

    print("=" * 20)
    print("The sum of weights for windows in each category:")
    pprint(results)


def dump_weights(weights, path):
    for p, pinfo in weights.iteritems():
        outputfile = path[p]["output_file"]
        dump_json(weights[p], outputfile)
