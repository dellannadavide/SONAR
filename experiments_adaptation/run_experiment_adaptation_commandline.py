from normadapter2SIMnoagent import NormAdapter2SIMnoagent
from sar.norm.fuzzysocialinterpreter import FuzzySocialInterpreter
from sar.norm.fuzzysocialqualifier import FuzzySocialQualifier
from utils.utils import joinStrings
import utils.constants as Constants
import pandas as pd
from datetime import datetime
import sys


def main(argv):
    param_types = {
        'society': str,
        'dataset_file': str,
        'max_dataset_size': int,
        'fuzzy_sets_file': str,
        'ling_vars_file': str,
        'rules_file_id': str,
        'interpretability_index': str,
        'min_nr_datapoints': int,
        'min_certainty_threshold': float,
        'use_correct_interpretation': bool,
        'consider_past_experience': bool,
        'genetic_algo': str,
        'ga_nr_gen': int,
        'pop_size': int,
        'contextualize': bool,
        'min_nr_adaptations_for_contextualizing': int,
        'trial': int
    }

    allNames = sorted(param_types)

    if len(argv) != len(param_types) + 4:
        print("ERROR in the input arguments. Given " + str(argv))
        print("Expected <exp_id>, " + str(allNames) + "<results_folder>, <all_experiments_timestamp>, <verbose>")
        exit()

    """ Decoding the script arguments into parameters of the simulation """
    exp_id = str(datetime.now().strftime("%Y%m%d%H%M%S"))  # + '_' + id_generator()
    exp_param = {}
    exp_param_list = []
    results_folder = ""
    all_experiments_timestamp = ""
    verbose = False
    for arg in argv:
        k = arg.split("=")[0]
        v = arg.split("=")[1]
        if k == "exp_id":
            exp_id = exp_id + "_" + str(v)
        if k in param_types.keys():
            if (v == 'True') or (v == 'False'):
                bv = (v == 'True')
                # print(bv)
                exp_param[k] = bv
                exp_param_list.append(bv)
            else:
                exp_param[k] = param_types[k](v)
                exp_param_list.append(param_types[k](v))
        else:
            if k == "results_folder":
                results_folder = str(v)
            if k == "all_experiments_timestamp":
                all_experiments_timestamp = str(v)
            if k == "verbose":
                verbose = int(v)


    fuzzy_sets_file = "../data/fuzzy_rules/social_interpretation2sim/{}".format(exp_param["fuzzy_sets_file"])
    ling_vars_file = "../data/fuzzy_rules/social_interpretation2sim/{}".format(exp_param["ling_vars_file"])
    rules_file = "../data/fuzzy_rules/social_interpretation2sim/rules_DIAMONDS_multiple_"+exp_param["society"]+exp_param["rules_file_id"]+".xlsx"
    # rules_file = "../data/fuzzy_rules/social_interpretation2sim/rules_DIAMONDS_multiple_"+exp_param["society"]+"_ref.xlsx"
    # rules_file = "../data/fuzzy_rules/social_interpretation2sim/rules_DIAMONDS_ONLYDIST_"+exp_param["society"]+".xlsx"
    fsi = FuzzySocialInterpreter(fuzzy_sets_file, ling_vars_file, rules_file, exp_param["min_certainty_threshold"])
    fsq = {}
    # for a in Constants.ACTUATION_ASPECTS:
    #     fsq[a] = FuzzySocialQualifier(a, fuzzy_sets_file, ling_vars_file, rules_file)
    fsq[Constants.ACTUATION_ASPECT_POSITION] = FuzzySocialQualifier(Constants.ACTUATION_ASPECT_POSITION, fuzzy_sets_file, ling_vars_file, rules_file)

    norm_adapter = NormAdapter2SIMnoagent(fsi=fsi, fsq=fsq, params=exp_param)

    dynamic_lv = ["DIST", "VOLUME", "MOVEMENTS"]
    # dynamic_lv = ["DIST"]



    df_results = {
        'society': [],
        'dataset_file': [],
        'max_dataset_size': [],
        'fuzzy_sets_file': [],
        'ling_vars_file': [],
        'rules_file_id': [],
        'interpretability_index': [],
        'min_nr_datapoints': [],
        'min_certainty_threshold': [],
        'genetic_algo': [],
        'ga_nr_gen': [],
        'pop_size': [],
        'trial': [],
        'STEP/DATAPOINT': [],
        'use_correct_interpretation': [],
        'consider_past_experience': [],
        'contextualize': [],
        'min_nr_adaptations_for_contextualizing': [],
        'correct_interpretation': [],
        'social_interpretation': [],
        'certainty_interpretation': []
    }
    # for socialcue in Constants.LV_SOCIAL_CUES:
    #     df_results[socialcue] = []
    # for dynamic_var in dynamic_lv:
    #     df_results[dynamic_var] = []

    for lv in dynamic_lv:
        try:
            for mf in fsi.fuzzyRuleBase.fs._lvs[lv]._FSlist:
                df_results["_".join(['FSI', lv, mf._term, "a"])] = []
                df_results["_".join(['FSI', lv, mf._term, "b"])] = []
                df_results["_".join(['FSI', lv, mf._term, "c"])] = []
                df_results["_".join(['FSI', lv, mf._term, "d"])] = []
                # df_results["_".join(['FSI', lv, mf._term, "k_GP"])] = []
                # df_results["_".join(['FSI', lv, mf._term, "theta"])] = []
        except:
            # print("Variable", lv, "not in FSI")
            pass
        for qualifier in fsq.keys():
            try:
                for mf in fsq[qualifier].fuzzyRuleBase.fs._lvs[lv]._FSlist:
                    df_results["_".join(['FSQ', qualifier, lv, mf._term, "a"])] = []
                    df_results["_".join(['FSQ', qualifier, lv, mf._term, "b"])] = []
                    df_results["_".join(['FSQ', qualifier, lv, mf._term, "c"])] = []
                    df_results["_".join(['FSQ', qualifier, lv, mf._term, "d"])] = []
                    # df_results["_".join(['FSQ', qualifier, lv, mf._term, "k_GP"])] = []
                    # df_results["_".join(['FSQ', qualifier, lv, mf._term, "theta"])] = []
            except:
                # print("Variable", lv, "not in ", qualifier)
                pass

    dataset_file = "../data/societies_norms/"+exp_param["dataset_file"]
    dataset_df = pd.read_excel(dataset_file, engine='openpyxl')
    df = dataset_df.loc[dataset_df['Society'].isin([exp_param["society"]])]
    max_ds_size = exp_param["max_dataset_size"]
    processed_inputs = 0
    for i in df.index: # This loop simulates data being received from the sensors
        print(i)
        if processed_inputs<max_ds_size:
            data = {}

            for socialcue in Constants.LV_SOCIAL_CUES:
                data[socialcue] = float(df[socialcue][i])

            for dynamic_var in dynamic_lv:
                data[dynamic_var] = float(df[dynamic_var][i])

            """ The following is taken from the data collector, and is meant to create a proper data point for the norm adapter """
            social_values = None
            best_social_interpr = None
            nr_info = len(data)
            if nr_info > 0: #isn't this always true, given the fact that above you are populating data?? yes but it's just taken as it is from the data collector, where instead it is not the case
                # if there is some data, then I fill all the rest with "off" values
                for social_cue in Constants.LV_SOCIAL_CUES:
                    if not social_cue in data.keys():
                        data[social_cue] = 0.0
                # print("data: " + str(data))
                social_values, best_social_interpr = fsi.getBestSocialInterpretation(data)

            # print(social_values)
            # print(best_social_interpr)
            if exp_param["use_correct_interpretation"]:
                best_social_interpr = str(df["SocialInterpretation"][i])

            if (not best_social_interpr is None):
                # print("best social interpretation: " + str(best_social_interpr))
                if nr_info > 0:
                    msg_to_norm_adapter = [Constants.TOPIC_SOCIAL_INTERPR, str(best_social_interpr)]
                    if not social_values is None:
                        for s in social_values.keys():
                            msg_to_norm_adapter.extend([str(s), str(social_values[s])])
                    for d in data:
                        msg_to_norm_adapter.extend([str(d), str(data[d])])

                    # send_msg_to_norm_adapter = self.SendMsgToBehaviour(Constants.NORMADAPTER_JID, msg_to_norm_adapter)
                    # print("DATACOLLECTOR: Created new sendmsgtoBehavior at " + str(time.time()))
                    # self.add_behaviour(send_msg_to_norm_adapter)
                    """ I'm replacing sending a message with a direct call"""
                    msg = joinStrings(msg_to_norm_adapter)
                    norm_adapter.collectDataPointFromMessage(msg)
            """ Until here """

            """ Also here replacing adaptation as a behavior with direct calls"""
            # b = norm_adapter.AdaptNorms()
            # norm_adapter.add_behaviour(b)
            # b.join() #waiting for the behavior to finish
            norm_adapter.adaptNorms()


            df_results['society'].append(exp_param["society"])
            df_results['dataset_file'].append(exp_param["dataset_file"])
            df_results['max_dataset_size'].append(exp_param["max_dataset_size"])
            df_results['fuzzy_sets_file'].append(exp_param["fuzzy_sets_file"])
            df_results['ling_vars_file'].append(exp_param["ling_vars_file"])
            df_results['rules_file_id'].append(exp_param["rules_file_id"])
            df_results['interpretability_index'].append(exp_param["interpretability_index"])
            df_results['min_nr_datapoints'].append(exp_param['min_nr_datapoints'])
            df_results['min_certainty_threshold'].append(exp_param["min_certainty_threshold"])
            df_results['genetic_algo'].append(exp_param["genetic_algo"])
            df_results['ga_nr_gen'].append(exp_param["ga_nr_gen"])
            df_results['pop_size'].append(exp_param["pop_size"])
            df_results['trial'].append(exp_param["trial"])

            df_results['STEP/DATAPOINT'].append(i)
            df_results['use_correct_interpretation'].append(exp_param["use_correct_interpretation"])
            df_results['consider_past_experience'].append(exp_param["consider_past_experience"])
            df_results['contextualize'].append(exp_param["contextualize"])
            df_results['min_nr_adaptations_for_contextualizing'].append(exp_param["min_nr_adaptations_for_contextualizing"])
            df_results['correct_interpretation'].append(str(df["SocialInterpretation"][i]))
            df_results['social_interpretation'].append(best_social_interpr if not best_social_interpr is None else "None")
            # df_results['certainty_interpretation'].append(social_values[best_social_interpr] if ((not social_values is None) and (not best_social_interpr is None)) else "None")
            df_results['certainty_interpretation'].append(str(social_values))
            # for socialcue in Constants.LV_SOCIAL_CUES:
            #     df_results[socialcue].append(float(df[socialcue][i]))
            #
            # for dynamic_var in dynamic_lv:
            #     df_results[dynamic_var].append(float(df[dynamic_var][i]))




            for lv in dynamic_lv:
                try:
                    for mf in fsi.fuzzyRuleBase.fs._lvs[lv]._FSlist:
                        a, b, c, d, k_GP, theta = mf.get_params()
                        df_results["_".join(['FSI', lv, mf._term, "a"])].append(a)
                        df_results["_".join(['FSI', lv, mf._term, "b"])].append(b)
                        df_results["_".join(['FSI', lv, mf._term, "c"])].append(c)
                        df_results["_".join(['FSI', lv, mf._term, "d"])].append(d)
                        # df_results["_".join(['FSI', lv, mf._term, "k_GP"])].append(k_GP)
                        # df_results["_".join(['FSI', lv, mf._term, "theta"])].append(theta)
                except:
                    # print("Variable", lv, "not in FSI")
                    pass
                for qualifier in fsq.keys():
                    try:
                        for mf in fsq[qualifier].fuzzyRuleBase.fs._lvs[lv]._FSlist:
                            a, b, c, d, k_GP, theta = mf.get_params()
                            df_results["_".join(['FSQ', qualifier, lv, mf._term, "a"])].append(a)
                            df_results["_".join(['FSQ', qualifier, lv, mf._term, "b"])].append(b)
                            df_results["_".join(['FSQ', qualifier, lv, mf._term, "c"])].append(c)
                            df_results["_".join(['FSQ', qualifier, lv, mf._term, "d"])].append(d)
                            # df_results["_".join(['FSQ', qualifier, lv, mf._term, "k_GP"])].append(k_GP)
                            # df_results["_".join(['FSQ', qualifier, lv, mf._term, "theta"])].append(theta)
                    except:
                        # print("Variable", lv, "not in ", qualifier)
                        pass

            processed_inputs = processed_inputs + 1
        else:
            break

    # print(df_results)
    pandas_df = pd.DataFrame(df_results)
    # pd.set_option('display.max_columns', None)
    # display(pandas_df)
    pandas_df.to_csv(results_folder+'res_' + all_experiments_timestamp + '_' + exp_id+".csv", index=False)


if __name__ == "__main__":
    main(sys.argv[1:])