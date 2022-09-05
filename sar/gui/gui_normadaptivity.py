# Python code for 2D random walk.
from time import sleep

import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.use('TkAgg')  # or can use 'TkAgg', whatever you have/prefer
import random
import matplotlib.colors as mcolors
import numpy as np
import math
from labellines import labelLine, labelLines

import threading

class GUI_NormAdaptivity:

    def __init__(self) -> None:
        super().__init__()

        candidates = ["macosx", "qt5agg", "gtk3agg", "tkagg", "wxagg"]
        for candidate in candidates:
            try:
                plt.switch_backend(candidate)
                print('Using backend: ' + candidate)
                break
            except (ImportError, ModuleNotFoundError):
                pass

        plt.ion()
        self.fig = plt.figure()
        self.axes = self.fig.add_subplot(111)
        plt.title("Experiment Norm adaptivity in different societies")
        self.colors = list(mcolors.TABLEAU_COLORS)
        self.nao_x = 0.5
        self.nao_y = 0.5
        self.lock = threading.Lock()


    def update(self, person_idx, new_p_x, new_p_y, dist, person_norm, person_greets, nao_norm):
        self.lock.acquire()
        plt.cla()
        plt.xlim([-0.05, 1.05])
        plt.ylim([-0.05, 1.05])

        color = self.colors[person_idx % len(self.colors)]

        draw_circle = plt.Circle((new_p_x, new_p_y), person_norm, color=color, fill=False)
        self.axes.set_aspect(1)
        self.axes.add_artist(draw_circle)
        self.axes.scatter(new_p_x, new_p_y, marker="o", color=color)
        self.axes.plot(self.nao_x, self.nao_y, marker="s", color="red")
        # a = (self.nao_x, self.nao_y)
        # b = (new_p_x, new_p_y)
        # d = math.dist(a, b)
        d = dist
        if person_greets:
            self.axes.text(new_p_x, new_p_y, "Hello Nao!", fontsize=12)
        # if nao_greets:
        #     self.axes.text(nao_x, nao_y, "Hello Person "+str(person_idx), fontsize=12)

        self.axes.plot([self.nao_x, new_p_x], [self.nao_y, new_p_y], linestyle='dashed', color=color, label=str(round(d, 3)))
        plt.legend(loc=4)

        # self.axes.text(0, 0.99,
        #           "{} ({}, {}) - Person {}".format(society, norms_societies[society][0], norms_societies[society][1],
        #                                            str(person)), fontsize=10)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        self.lock.release()


    def updateNao(self, nao_greetings):
        self.lock.acquire()
        self.axes.text(self.nao_x, self.nao_y, nao_greetings, fontsize=12)
        # self.fig.canvas.draw()
        # self.fig.canvas.flush_events()
        self.lock.release()
