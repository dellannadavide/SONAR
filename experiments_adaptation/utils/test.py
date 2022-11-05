import utils.constants as Constants
from sar.agent.worker.normadapter2SIM import NormAdapter2SIM
from sar.norm.fuzzysocialinterpreter import FuzzySocialInterpreter
from utils.utils import joinStrings

import pandas as pd


def main():
    fuzzy_sets_file = "data/fuzzy_rules/social_interpretation2sim/fuzzy_sets_multiple.xlsx"
    ling_vars_file = "data/fuzzy_rules/social_interpretation2sim/ling_var_multiple.xlsx"
    rules_file = "data/fuzzy_rules/social_interpretation2sim/rules_DIAMONDS_multiple_AUSTRIA.xlsx"
    fsi = FuzzySocialInterpreter(fuzzy_sets_file, ling_vars_file, rules_file, 0.2)
    fsq = {}
    # for a in Constants.ACTUATION_ASPECTS:
    #     fsq[a] = FuzzySocialQualifier(a, fuzzy_sets_file, ling_vars_file, rules_file)

    norm_adapter = NormAdapter2SIM(Constants.NORM_ADAPTER_JID, Constants.NORM_ADAPTER_PWD, fsi=fsi, fsq=fsq)
    # norm_adapter = NormAdapter2SIM(Constants.NORM_ADAPTER_JID, Constants.NORM_ADAPTER_PWD, fsi=fsi)
    future = norm_adapter.start(auto_register=True)
    future.result()

    dynamic_lv = ["DIST", "VOLUME", "MOVEMENTS"]

    df_results = {
        'STEP/DATAPOINT': []
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


    dataset_file = "data/societies_sociality_norms/S0_02.xlsx"
    dataset_file = "data/societies_sociality_norms/S0_02_onlypositive.xlsx"
    dataset_file = "data/societies_norms/data.xlsx"
    dataset_df = pd.read_excel(dataset_file, engine='openpyxl')
    df = dataset_df.loc[dataset_df['Society'].isin(["Austria"])]
    max_ds_size = 99999999
    for i in df.index: # This loop simulates data being received from the sensors
        print(i)
        if i<max_ds_size:
            data = {}
            for socialcue in Constants.LV_SOCIAL_CUES:
                data[socialcue] = float(df[socialcue][i])

            for dynamic_var in dynamic_lv:
                data[dynamic_var] = float(df[dynamic_var][i])

            """ The following is taken from the data collector, and is meant to create a proper data point for the norm adapter """
            social_values = None
            best_social_interpr = None
            nr_social_cues = len(data)
            if nr_social_cues > 0:
                # if there is some data, then I fill all the rest with "off" values
                for social_cue in Constants.LV_SOCIAL_CUES:
                    if not social_cue in data:
                        data[social_cue] = 0.0
                # print("data: " + str(data))
                social_values, best_social_interpr = fsi.getBestSocialInterpretation(data)

            # print(social_values)
            # print(best_social_interpr)

            if (not best_social_interpr is None):
                # print("best social interpretation: " + str(best_social_interpr))
                if nr_social_cues > 1:
                    msg_to_norm_adapter = [Constants.TOPIC_SOCIAL_INTERPR, str(best_social_interpr)]
                    if not social_values is None:
                        for s in social_values:
                            msg_to_norm_adapter.extend([str(s), str(social_values[s])])
                    for d in data:
                        msg_to_norm_adapter.extend([str(d), str(data[d])])

                    # send_msg_to_norm_adapter = self.SendMsgToBehaviour(Constants.NORM_ADAPTER_JID, msg_to_norm_adapter)
                    # print("DATACOLLECTOR: Created new sendmsgtoBehavior at " + str(time.time()))
                    # self.add_behaviour(send_msg_to_norm_adapter)
                    """ I'm replacing sending a message with a direct call"""
                    msg = joinStrings(msg_to_norm_adapter)
                    norm_adapter.collectDataPointFromMessage(msg)
            """ Until here """

            b = norm_adapter.AdaptNorms()
            norm_adapter.add_behaviour(b)
            b.join() #waiting for the behavior to finish

            df_results['STEP/DATAPOINT'].append(i)

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

        else:
            break

    print(df_results)
    pandas_df = pd.DataFrame(df_results)
    # pd.set_option('display.max_columns', None)
    # display(pandas_df)
    pandas_df.to_csv('out.csv', index=True)


if __name__ == '__main__':
    main()