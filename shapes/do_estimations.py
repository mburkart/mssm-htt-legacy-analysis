#!/usr/bin/env python3
import argparse
import logging

import ROOT


logger = logging.getLogger("")

_dataset_map = {
    "data": "data",
    "ZTT": "DY",
    "ZL": "DY",
    "ZJ": "DY",
    "TTT": "TT",
    "TTL": "TT",
    "TTJ": "TT",
    "VVT": "VV",
    "VVL": "VV",
    "VVJ": "VV",
    "EMB": "EMB",
    "W": "W",
}

_process_map = {
    "data": "data",
    "ZTT": "DY-ZTT",
    "ZL": "DY-ZL",
    "ZJ": "DY-ZJ",
    "TTT": "TT-TTT",
    "TTL": "TT-TTL",
    "TTJ": "TT-TTJ",
    "VVT": "VV-VVT",
    "VVL": "VV-VVL",
    "VVJ": "VV-VVJ",
    "EMB": "Embedded",
    "W": "W",
}

_name_string = "{dataset}#{channel}{process}{selection}#{variation}#{variable}"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="Input root file.")
    parser.add_argument("-e", "--era", required=True, help="Experiment era.")
    parser.add_argument("--emb-tt", action="store_true",
                        help="Add embedded ttbar contamination variation to file.")
    return parser.parse_args()


def setup_logging(output_file, level=logging.INFO):
    logger.setLevel(level)
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    file_handler = logging.FileHandler(output_file, "w")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return



def fake_factor_estimation(rootfile, channel, selection, variable, variation="Nominal", is_embedding=True):
    if is_embedding:
        procs_to_subtract = ["EMB", "ZL", "TTL", "VVL"]
    else:
        procs_to_subtract = ["ZTT", "ZL", "TTT", "TTL", "VVT", "VVL"]
    logger.debug("Trying to get object {}".format(
                            _name_string.format(dataset="data",
                                                channel=channel,
                                                process="",
                                                selection="-" + selection if selection != "" else "",
                                                variation=variation,
                                                variable=variable)))
    base_hist = rootfile.Get(_name_string.format(
                                dataset="data",
                                channel=channel,
                                process="",
                                selection="-" + selection if selection != "" else "",
                                variation=variation,
                                variable=variable
        )).Clone()
    for proc in procs_to_subtract:
        logger.debug("Trying to get object {}".format(
                            _name_string.format(dataset=_dataset_map[proc],
                                                channel=channel,
                                                process="-" + _process_map[proc],
                                                selection="-" + selection if selection != "" else "",
                                                variation=variation,
                                                variable=variable)))
        base_hist.Add(rootfile.Get(_name_string.format(
                                        dataset=_dataset_map[proc],
                                        channel=channel,
                                        process="-" + _process_map[proc],
                                        selection="-" + selection if selection !="" else "",
                                        variation=variation,
                                        variable=variable)), -1.0)
    proc_name = "jetFakes" if is_embedding else "jetFakesMC"
    if variation in ["anti_iso"]:
        ff_variation = "Nominal"
    else:
        ff_variation = variation.replace("anti_iso", "CMS")
    variation_name = base_hist.GetName().replace("data", proc_name) \
                                        .replace(variation, ff_variation) \
                                        .replace(channel, "-".join([channel, proc_name]), 1)
    base_hist.SetName(variation_name)
    base_hist.SetTitle(variation_name)
    return base_hist


def qcd_estimation(rootfile, channel, selection, variable, variation="Nominal", is_embedding=True,
                   extrapolation_factor=1.):
    if is_embedding:
        procs_to_subtract = ["EMB", "ZL", "ZJ", "TTL", "TTJ", "VVL", "VVJ", "W"]
        if "em" in channel:
            procs_to_subtract = ["EMB", "ZL", "TTL", "VVL", "W"]
    else:
        procs_to_subtract = ["ZTT", "ZL", "ZJ", "TTT", "TTL", "TTJ", "VVT", "VVL", "VVJ", "W"]
        if "em" in channel:
            procs_to_subtract = ["ZTT", "ZL", "TTT", "TTL", "VVT", "VVL", "W"]

    logger.debug("Trying to get object {}".format(
                                    _name_string.format(dataset="data",
                                                        channel=channel,
                                                        process="",
                                                        selection="-" + selection if selection != "" else "",
                                                        variation=variation,
                                                        variable=variable)))
    base_hist = rootfile.Get(_name_string.format(
                                dataset="data",
                                channel=channel,
                                process="",
                                selection="-" + selection if selection != "" else "",
                                variation=variation,
                                variable=variable
        )).Clone()
    for proc in procs_to_subtract:
        logger.debug("Trying to get object {}".format(
                                    _name_string.format(dataset=_dataset_map[proc],
                                                        channel=channel,
                                                        process="-" + _process_map[proc],
                                                        selection="-" + selection if selection != "" else "",
                                                        variation=variation,
                                                        variable=variable)))
        base_hist.Add(rootfile.Get(_name_string.format(
                                        dataset=_dataset_map[proc],
                                        channel=channel,
                                        process="-" + _process_map[proc],
                                        selection="-" + selection if selection != "" else "",
                                        variation=variation,
                                        variable=variable)), -1.0)

    proc_name = "QCD" if is_embedding else "QCDMC"
    if variation in ["same_sign"]:
        qcd_variation = "Nominal"
    else:
        qcd_variation = variation.replace("same_sign", "CMS")
    logger.debug("Use extrapolation_factor factor with value %.2f to scale from ss to os region.",
                  extrapolation_factor)
    base_hist.Scale(extrapolation_factor)
    variation_name = base_hist.GetName().replace("data", proc_name) \
                                        .replace(variation, qcd_variation) \
                                        .replace(channel, "-".join([channel, proc_name]), 1)
    base_hist.SetName(variation_name)
    base_hist.SetTitle(variation_name)
    return base_hist


def emb_ttbar_contamination_estimation(rootfile, channel, category, variable, sub_scale=0.1):
    procs_to_subtract = ["TTT"]
    logger.debug("Trying to get object {}".format(
                            _name_string.format(dataset=_dataset_map["EMB"],
                                                channel=channel,
                                                process="-" + _process_map["EMB"],
                                                selection=category,
                                                variation="Nominal",
                                                variable=variable)))
    base_hist = rootfile.Get(_name_string.format(
                            dataset=_dataset_map["EMB"],
                            channel=channel,
                            process="-" + _process_map["EMB"],
                            selection=category,
                            variation="Nominal",
                            variable=variable)).Clone()
    for proc in procs_to_subtract:
        logger.debug("Trying to fetch root histogram {}".format(
                                        _name_string.format(dataset=_dataset_map[proc],
                                                            channel=channel,
                                                            process="-" + _process_map[proc],
                                                            selection=category,
                                                            variation="Nominal",
                                                            variable=variable)))
        base_hist.Add(rootfile.Get(_name_string.format(
                                        dataset=_dataset_map[proc],
                                        channel=channel,
                                        process="-" + _process_map[proc],
                                        selection=category,
                                        variation="Nominal",
                                        variable=variable)), -sub_scale)
        if sub_scale > 0:
            variation_name = base_hist.GetName().replace("Nominal", "CMS_htt_emb_ttbarDown")
        else:
            variation_name = base_hist.GetName().replace("Nominal", "CMS_htt_emb_ttbarUp")
        base_hist.SetName(variation_name)
        base_hist.SetTitle(variation_name)
    return base_hist


def main(args):
    input_file = ROOT.TFile(args.input, "read")
    # Loop over histograms in root file to find available FF inputs.
    ff_inputs = {}
    qcd_inputs = {}
    emb_categories = {}
    logger.info("Reading inputs from file {}".format(args.input))
    for key in input_file.GetListOfKeys():
        dataset, selection, variation, variable = key.GetName().split("#")
        if "anti_iso" in variation or "same_sign" in variation:
            sel_split = selection.split("-", maxsplit=1)
            # Set category to default since not present in control plots.
            category = ""
            # Treat data hists seperately because only channel selection is applied to data.
            if "data" in dataset:
                channel = sel_split[0]
                # Set category label for analysis categories.
                if len(sel_split) > 1:
                    category = sel_split[1]
                process = "data"
            else:
                channel = sel_split[0]
                #  Check if analysis category present in root file.
                if len(sel_split) > 2:
                    process = "-".join(sel_split[1].split("-")[:-1])
                    category = sel_split[1].split("-")[-1]
                else:
                    # Set only process if no categorization applied.
                    process = sel_split[1]
            if "anti_iso" in variation:
                if channel in ff_inputs:
                    if category in ff_inputs[channel]:
                        if variable in ff_inputs[channel][category]:
                            if variation in ff_inputs[channel][category][variable]:
                                ff_inputs[channel][category][variable][variation].append(process)
                            else:
                                ff_inputs[channel][category][variable][variation] = []
                        else:
                            ff_inputs[channel][category][variable] = {}
                    else:
                        ff_inputs[channel][category] = {}
                else:
                    ff_inputs[channel] = {}
            if "same_sign" in variation:
                if channel in qcd_inputs:
                    if category in qcd_inputs[channel]:
                        if variable in qcd_inputs[channel][category]:
                            if variation in qcd_inputs[channel][category][variable]:
                                qcd_inputs[channel][category][variable][variation].append(process)
                            else:
                                qcd_inputs[channel][category][variable][variation] = []
                        else:
                            qcd_inputs[channel][category][variable] = {}
                    else:
                        qcd_inputs[channel][category] = {}
                else:
                    qcd_inputs[channel] = {}
        #  Booking of necessary categories for embedded tt bar variation.
        if "Nominal" in variation:
            sel_split = selection.split("-", maxsplit=1)

            if "EMB" in dataset:
                channel = sel_split[0]
                category = sel_split[1].replace("Embedded", "").strip("-")
                if channel in emb_categories:
                    if category in emb_categories[channel]:
                        emb_categories[channel][category].append(variable)
                    else:
                        emb_categories[channel][category] = []
                else:
                    emb_categories[channel] = {}

    output_file = ROOT.TFile(args.input.replace(".root", "-estimations.root"), "recreate")
    # Loop over available ff inputs and do the estimations
    logger.info("Starting estimations for fake factors and their variations")
    for ch in ff_inputs:
        for cat in ff_inputs[ch]:
            for var in ff_inputs[ch][cat]:
                for variation in ff_inputs[ch][cat][var]:
                   estimated_hist = fake_factor_estimation(input_file, ch, cat, var, variation=variation)
                   estimated_hist.Write()
                   estimated_hist = fake_factor_estimation(input_file, ch, cat, var, variation=variation, is_embedding=False)
                   estimated_hist.Write()
    logger.info("Starting estimations for the QCD mulitjet process.")
    for ch in qcd_inputs:
        for cat in qcd_inputs[ch]:
            for var in qcd_inputs[ch][cat]:
                for variation in qcd_inputs[ch][cat][var]:
                    if args.era == "2016":
                        extrapolation_factor = 1.17
                    else:
                        extrapolation_factor = 1.0
                    estimated_hist = qcd_estimation(input_file, ch, cat, var, variation=variation)
                    estimated_hist.Write()
                    estimated_hist = qcd_estimation(input_file, ch, cat, var, variation=variation, is_embedding=False)
                    estimated_hist.Write()
    if args.emb_tt:
        logger.info("Producing embedding ttbar variations.")
        for ch in emb_categories:
            for cat in emb_categories[ch]:
                for var in emb_categories[ch][cat]:
                    estimated_hist = emb_ttbar_contamination_estimation(input_file, ch, cat, var, sub_scale=0.1)
                    estimated_hist.Write()
                    estimated_hist = emb_ttbar_contamination_estimation(input_file, ch, cat, var, sub_scale=-0.1)
                    estimated_hist.Write()
    logger.info("Successfully finished estimations.")

    # Clean-up.
    output_file.Close()
    input_file.Close()
    return


if __name__ == "__main__":
    args = parse_args()
    setup_logging("do_estimations.log", level=logging.INFO)
    main(args)