import matplotlib
matplotlib.use('Agg')   # NOQA
import os
from pprint import pprint
from pytomo3d.window.window_weights import \
    calculate_receiver_weights_interface, \
    calculate_category_weights_interface, \
    combine_receiver_and_category_weights
from utils import assert_file_exists, get_category_ratio, analyze, \
    dump_weights


def construct_path_info():
    period = ["17_40", "40_100", "90_250"]
    datadir = "../data"
    eventname = "C201001122153A"

    path = {}
    for p in period:
        station_file = os.path.join(datadir, "stations", "%s.stations.json"
                                    % (eventname))
        assert_file_exists(station_file)
        window_file = os.path.join(datadir, "windows", "%s.%s.windows.json"
                                   % (eventname, p))
        assert_file_exists(window_file)
        output_file = os.path.join(".", "weights", "%s.%s"
                                   % (eventname, p), "weight.json")
        path[p] = {"station_file": station_file, "window_file": window_file,
                   "output_file": output_file}

    return path


def get_receiver_weights(src_info, path, param):
    """
    In the schema, the receiver weights are normlized to number
    of receivers
    """
    rec_weights = {}
    rec_wcounts = {}
    cat_wcounts = {}
    for p, pinfo in path.iteritems():
        results = calculate_receiver_weights_interface(
            src_info, pinfo, param)
        rec_weights[p] = results["rec_weights"]
        rec_wcounts[p] = results["rec_wcounts"]
        cat_wcounts[p] = results["cat_wcounts"]

    # hack: normalize to number of recievers
    for p, pinfo in rec_weights.iteritems():
        for c, cinfo in pinfo.iteritems():
            print("------------")
            print("Period and component: %s, %s" % (p, c))
            nrecs = len(cinfo)
            vsum = 0
            for chan, chaninfo in cinfo.iteritems():
                vsum += chaninfo
            factor = nrecs / vsum
            print("number of receivers, sum and norm factor: %d, %f, %f"
                  % (nrecs, vsum, factor))
            for chan in cinfo:
                cinfo[chan] *= factor

    return rec_weights, rec_wcounts, cat_wcounts


def get_category_weights(cat_wcounts):
    """
    Just normalize the sum of category weights to 1
    """
    print("category window counts:")
    pprint(cat_wcounts)
    cat_ratio = get_category_ratio(cat_wcounts)
    print("category weight ratio")
    pprint(cat_ratio)

    param = {"flag": True, "ratio": cat_ratio}
    cat_weights = calculate_category_weights_interface(
        param, cat_wcounts)

    pprint(cat_weights)
    # hack: normalize to 1
    vsum = 0
    for p, pinfo in cat_weights.iteritems():
        for c, cinfo in pinfo.iteritems():
            vsum += cinfo
    factor = 1.0 / vsum
    print("vsum and factor for category: %f, %f" % (vsum, factor))
    for p, pinfo in cat_weights.iteritems():
        for c in pinfo:
            pinfo[c] *= factor

    print("category final weights")
    pprint(cat_weights)

    return cat_weights


def get_source_weights(cat_wcounts):
    """
    Only one source so the value is 1
    """
    return 1.0


def get_overall_norm_factor(rec_wcounts, rec_weights, cat_weights,
                            src_weights):

    vsum = 0
    for p, pinfo in rec_weights.iteritems():
        for c, cinfo in pinfo.iteritems():
            for chan, chaninfo in cinfo.iteritems():
                vsum += rec_wcounts[p][c][chan] * rec_weights[p][c][chan] * \
                    cat_weights[p][c] * src_weights
    factor = 1 / vsum
    print("overall sum and factor: %f, %f" % (vsum, factor))
    return factor


def main():

    src_info = {"latitude": 0.0, "longitude": 0.0, "depth_in_m": 10000.0}
    param = {"flag": True, "plot": True, "search_ratio": 0.3}
    path = construct_path_info()
    pprint(path)
    # get receiver weighting
    rec_weights, rec_wcounts, cat_wcounts = \
        get_receiver_weights(src_info, path, param)

    cat_weights = get_category_weights(cat_wcounts)

    src_weights = get_source_weights(cat_wcounts)

    alpha = get_overall_norm_factor(rec_wcounts, rec_weights, cat_weights,
                                    src_weights)

    weights = combine_receiver_and_category_weights(
        rec_weights, cat_weights)

    analyze(weights, rec_wcounts, cat_wcounts, src_weights * alpha)

    dump_weights(weights, path)


if __name__ == "__main__":
    main()
