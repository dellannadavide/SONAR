import math

import pandas as pd
from sklearn import tree

#Reading the data
society = "US"
dataset_file = "../../data/societies_norms/data_USAustria_8000dp_v11_simple.xlsx"
dataset_df = pd.read_excel(dataset_file, engine='openpyxl')
df = dataset_df.loc[dataset_df['Society'].isin([society])]
print(df.head)
df = df.drop(["Society", "DIST", "MOVEMENTS", "VOLUME"],axis=1)
# splitting data into training and test set for independent attributes
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test =train_test_split(df.drop('SocialInterpretation',axis=1), df['SocialInterpretation'], test_size=.3,
                                                   random_state=22)
X_train.shape,X_test.shape
#developing a model
clf_pruned = tree.DecisionTreeClassifier(max_depth=15, min_samples_leaf=100)
clf_pruned.fit(X_train, y_train)
import matplotlib.pyplot as plt
xvar = df.drop('SocialInterpretation', axis=1)
feature_cols = xvar.columns
# plt.figure(figsize=(12,12))
# tree.plot_tree(clf_pruned, feature_names=feature_cols, class_names=sorted(df['SocialInterpretation'].unique()), fontsize=6)
# # tree.plot_tree(dt, feature_names=features_names, class_names=target_names, filled = True)
# plt.show()
# plt.savefig('tree_high_dpi', dpi=100)


# from sklearn.tree import export_text
# tree_rules = export_text(clf_pruned, feature_names=list(X_train.columns))
# print(tree_rules)

from sklearn.tree import _tree
import numpy as np

def findClosestFS(fs_df, corr_val):
    closest = str(fs_df["Label"][0])
    closest_dist = 99999
    for fs_index in fs_df.index:
        dist = abs(corr_val-float(fs_df["b"][fs_index]))
        if dist<closest_dist:
            closest = str(fs_df["Label"][fs_index])
            closest_dist = dist
    return closest
si_rules = "../data/societies_norms/cues-to-diamonds-fs-all.xlsx"

fs_df = pd.read_excel(si_rules, engine='openpyxl', sheet_name="FuzzySets")


def get_rules(tree, feature_names, class_names):
    tree_ = tree.tree_
    feature_name = [
        feature_names[i] if i != _tree.TREE_UNDEFINED else "undefined!"
        for i in tree_.feature
    ]

    paths = []
    path = []

    def recurse(node, path, paths):

        if tree_.feature[node] != _tree.TREE_UNDEFINED:
            name = feature_name[node]
            threshold = tree_.threshold[node]
            p1, p2 = list(path), list(path)
            p1 += [f"({name} <= {np.round(threshold, 3)})"]
            recurse(tree_.children_left[node], p1, paths)
            p2 += [f"({name} > {np.round(threshold, 3)})"]
            recurse(tree_.children_right[node], p2, paths)
        else:
            path += [(tree_.value[node], tree_.n_node_samples[node])]
            paths += [path]

    recurse(0, path, paths)

    # sort by samples count
    samples_count = [p[-1][1] for p in paths]
    ii = list(np.argsort(samples_count))
    paths = [paths[i] for i in reversed(ii)]

    rules = []
    for path in paths:
        rule = "IF "

        for p in path[:-1]:
            if rule != "IF ":
                rule += " AND "
            rule += str(p)
        rule += " THEN "
        if class_names is None:
            rule += "response: " + str(np.round(path[-1][0][0][0], 3))
        else:
            classes = path[-1][0][0]
            l = np.argmax(classes)

            proba = (classes[l] / np.sum(classes))
            if not math.isnan(proba):
                fuzzy_set = findClosestFS(fs_df, proba)
            rule += f"({class_names[l]} IS {str(fuzzy_set)})"# (proba: {np.round(classes[l] / np.sum(classes), 2)} , {str(fuzzy_set)})"
        # rule += f" | based on {path[-1][1]:,} samples"
        rule = rule.replace("<= 0.5", "IS low").replace("> 0.5", "IS high")
        rules += [rule]

    return rules

rules = get_rules(clf_pruned, feature_names=feature_cols, class_names=sorted(df['SocialInterpretation'].unique()))
for r in rules:
    print(r)

# print(clf_pruned)
# #
# #visualizing the tree
# import io
# from io import StringIO
# from sklearn.tree import export_graphviz, DecisionTreeClassifier
# # from sklearn.externals.six import StringIO
# from IPython.display import Image
# import pydotplus
# import graphviz
# xvar = df.drop('SocialInterpretation', axis=1)
# feature_cols = xvar.columns
# dot_data = StringIO()
# export_graphviz(clf_pruned, out_file=dot_data,
#                 filled=True, rounded=True,
#                 special_characters=True,feature_names = feature_cols)
# from pydot import graph_from_dot_data
# (graph, ) = graph_from_dot_data(dot_data.getvalue())
# Image(graph.create_png())