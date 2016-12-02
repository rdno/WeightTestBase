# -*- coding: utf-8 -*-
from __future__ import division, absolute_import
from __future__ import print_function, unicode_literals

import argparse
import json
import os
from collections import defaultdict, namedtuple
from pprint import pprint

from spaceweight import SphereDistRel, SpherePoint


# Data types

Station = namedtuple("Station",
                     ["network", "name", "component",
                      "location", "window_count"])
Category = namedtuple("Category",
                      ["period", "component"])

# Global variables

components = "ZRT"
periods = ["17_40", "40_100", "90_250"]

categories = []
for period in periods:
    for component in components:
        categories.append(Category(period, component))

# Utility functions


def station_str(station):
    return ".".join([station.network, station.name, "BH"+station.component])


def construct_path_info():
    period = ["17_40", "40_100", "90_250"]
    datadir = "../data"
    eventname = "C201001122153A"

    path = {}
    for p in period:
        station_file = os.path.join(datadir, "stations", "%s.stations.json"
                                    % (eventname))
        window_file = os.path.join(datadir, "windows", "%s.%s.windows.json"
                                   % (eventname, p))
        output_file = os.path.join(".", "weights", "%s.%s"
                                   % (eventname, p), "weight.json")
        path[p] = {"station_file": station_file, "window_file": window_file,
                   "output_file": output_file}

    return path


def load_weights(path, period):
    with open(path[period]["output_file"]) as f:
        weights = json.load(f)
    return weights


def write_weights(path, weights):
    for period, data in weights.iteritems():
        with open(path[period]["output_file"], "w") as f:
            json.dump(data, f, sort_keys=True, indent=2)


def find_station_location(name, sta_data):
    for comp in sta_data:
        if comp.startswith(name):
            return SpherePoint(sta_data[comp]["latitude"],
                               sta_data[comp]["longitude"],
                               tag=name)


def get_stations(path, category):
    period = category.period
    component = category.component

    window_file = path[period]["window_file"]
    sta_file = path[period]["station_file"]
    with open(window_file) as f:
        window_data = json.load(f)

    with open(sta_file) as f:
        sta_data = json.load(f)

    stations = []
    for name in window_data:
        for station in window_data[name]:
            if station.endswith(component):
                net, sta, _, _ = station.split(".")
                location = find_station_location(".".join([net, sta]),
                                                 sta_data)
                stations.append(Station(net, sta, component,
                                        location,
                                        len(window_data[name][station])))
    return stations


def get_category_measurement_counts(all_stations):
    n_meas = {}
    for category in all_stations:
        n_meas[category] = sum([station.window_count
                                for station in all_stations[category]])
    return n_meas


# Weight calculations


def calc_receiver_weights(all_stations, weights={}):
    for category, stations in all_stations.iteritems():
        points = [station.location
                  for station in all_stations[category]]
        src = SpherePoint(0, 0, tag="src")
        sphere_dist = SphereDistRel(points, center=src)
        ref_distance, cond_number = sphere_dist.smart_scan(
            max_ratio=0.3, start=0.5, gap=0.5,
            drop_ratio=0.95)

        if category not in weights:
            weights[category] = [{} for station in all_stations[category]]

        for weight, station in zip(weights[category], all_stations[category]):
            weight["receiver"] = station.location.weight
            weight["n_measurements"] = station.window_count

    return weights


def normalize_receiver_weights(weights):
    n_meas = defaultdict(lambda: 0)
    n_weighted_meas = defaultdict(lambda: 0)
    for category in weights:
        for weight in weights[category]:
            w_count = weight["n_measurements"]
            n_meas[category] += w_count
            n_weighted_meas[category] += weight["receiver"]*w_count

    norm_factors = {}
    for cat in weights:
        norm_factors[cat] = n_meas[cat] / n_weighted_meas[cat]

    for category in weights:
        for weight in weights[category]:
            weight["receiver"] *= norm_factors[category]

    return weights


def calc_category_weights(all_stations, weights={}):
    n_meas = get_category_measurement_counts(all_stations)
    for category in all_stations:
        n_meas[category] = sum([station.window_count
                                for station in all_stations[category]])

    for category in n_meas:
        if category not in weights:
            weights[category] = [{} for station in all_stations[category]]
        for weight in weights[category]:
            weight["category"] = 1.0/n_meas[category]

    return weights, n_meas


def normalize_category_weights(weights, n_meas, ratios):
    sumv = 0
    all_windows = 0
    for cat_nmeas, ratio in zip(n_meas.values(), ratios.values()):
        sumv += ratio*cat_nmeas
        all_windows += cat_nmeas

    normc = all_windows/sumv
    for category in weights:
        for weight in weights[category]:
            weight["category"] *= normc
    return weights


def simple_normalization(weights):
    sum_of_weights = 0
    for category in weights:
        for weight in weights[category]:
            sum_of_weights += weight["weight"]*weight["n_measurements"]

    alpha = 1 / sum_of_weights
    for category in weights:
        for weight in weights[category]:
            weight["weight"] *= alpha
    return weights


def simple_per_cat_normalization(weights):
    sum_of_weights = defaultdict(lambda: 0)
    for category in weights:
        for weight in weights[category]:
            sum_of_weights[category] += weight["weight"]*weight["n_measurements"]

    n_cat = len(weights.keys())

    for category in weights:
        for weight in weights[category]:
            weight["weight"] *= 1/sum_of_weights[category]/n_cat
    return weights


def calc_final_weights(weights):
    for category in weights:
        for weight in weights[category]:
            weight["weight"] = weight["receiver"]*weight["category"]
    return weights


# Analyzing function


def analyze_weights(path, src_weights=1):
    sums = dict([(period, dict([(component, 0)
                                for component in components]))
                 for period in periods])
    overall = 0
    for period in path:
        weights = load_weights(path, period)
        for name in weights:
            weight = weights[name]["weight"]
            n_meas = weights[name]["n_measurements"]
            t_weight = weight * n_meas * src_weights
            sums[period][name[-1]] += t_weight
            overall += t_weight

    pprint(sums)
    print("Overall weights sum:", overall)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Weight Calculator')
    subparsers = parser.add_subparsers(dest="command")
    calculate = subparsers.add_parser("calculate")
    calculate.add_argument("normalization", default="complex", nargs="?",
                           help="Normalization type",
                           choices=("complex", "simple",
                                    "simple_per_cat"))
    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("normalization", default="complex", nargs="?",
                         help="Normalization type",
                         choices=("complex", "simple"))
    args = parser.parse_args()

    path = construct_path_info()
    if args.command == "analyze":
        all_stations = {}
        for category in categories:
            all_stations[category] = get_stations(path, category)
        n_meas = get_category_measurement_counts(all_stations)
        if args.normalization == "complex":
            src_weights = 1 / sum([wcount for wcount in n_meas.values()])
        else:
            src_weights = 1
        analyze_weights(path, src_weights=src_weights)
    if args.command == "calculate":
        all_stations = {}
        for category in categories:
            all_stations[category] = get_stations(path, category)

        weights, n_meas = calc_category_weights(all_stations)
        weights = calc_receiver_weights(all_stations, weights=weights)

        if args.normalization == "complex":
            weights = normalize_receiver_weights(weights)
            ratios = dict([(cat, 1.0/n_meas[cat]) for cat in categories])
            weights = normalize_category_weights(weights, n_meas, ratios)

        weights = calc_final_weights(weights)

        if args.normalization == "simple":
            weights = simple_normalization(weights)
        if args.normalization == "simple_per_cat":
            weights = simple_per_cat_normalization(weights)

        period_weights = {}
        for category in categories:
            for station, weight in zip(all_stations[category],
                                       weights[category]):
                if category.period not in period_weights:
                    period_weights[category.period] = {}
                period_weights[category.period][station_str(station)] = weight

        write_weights(path, period_weights)
