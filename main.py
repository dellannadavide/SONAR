import argparse
import time
from sar.sar import SARBDIAgent
import multiprocessing as mp

import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.use('TkAgg')
import matplotlib.colors as mcolors


def worker(q):
    candidates = ["macosx", "qt5agg", "gtk3agg", "tkagg", "wxagg"]
    for candidate in candidates:
        try:
            plt.switch_backend(candidate)
            # print('Using backend: ' + candidate)
            break
        except (ImportError, ModuleNotFoundError):
            pass
    plt.ion()
    fig = plt.figure()
    axes = fig.add_subplot(111)
    plt.title("Experiment Norm adaptivity in different societies")
    colors = list(mcolors.TABLEAU_COLORS)
    nao_x = 0.5
    nao_y = 0.5
    norms_societies = [0.2, 0.1, 0.4]

    society_idx = 0
    person_idx = 0
    new_p_x = 0
    new_p_y = 0
    dist = -1
    person_norm = 0
    nao_norm_b = 0
    nao_norm_c = 0
    color = colors[0]
    person_greets = False
    nao_greets = False
    nao_greetings = ""

    plt.cla()
    plt.xlim([-0.05, 1.05])
    plt.ylim([-0.05, 1.05])
    axes.set_aspect(1)
    axes.plot(nao_x, nao_y, marker="s", color="red")
    fig.canvas.draw()
    fig.canvas.flush_events()

    fast = False

    while True:
        obj = list(q.get())
        if len(obj)>0:
            nao_greets = False
            if obj[0]=="PERSON_POSITION":
                new_p_x = float(obj[1])
                new_p_y = float(obj[2])
                dist =float(obj[3])
                color = colors[person_idx % len(colors)]
            elif obj[0]=="PERSON_INFO":
                society_idx = int(obj[1])
                person_idx = int(obj[2])
                person_norm = float(obj[3])
            elif obj[0]=="PERSON_GREETS":
                person_greets = str(obj[1])=="True"
            elif obj[0] == "NAO_GREETS":
                nao_greets = str(obj[1])=="True"
                if nao_greets:
                    nao_greetings = str(obj[2])
            elif obj[0] == "NAO_NORM":
                nao_norm_b = float(obj[1])
                nao_norm_c = float(obj[2])


            plt.cla()
            plt.xlim([-0.05, 1.05])
            plt.ylim([-0.05, 1.05])
            axes.set_aspect(1)

            axes.plot(nao_x, nao_y, marker="s", color="red")

            axes.scatter(new_p_x, new_p_y, marker="o", color=color)
            axes.plot(nao_x, nao_y, marker="s", color="red")

            if not fast:
                axes.plot([nao_x, new_p_x], [nao_y, new_p_y], linestyle='dashed', color=color,
                      label=str(round(dist, 3)))
                plt.legend(loc=4)

                # the "social" distance for the current person
                draw_circle = plt.Circle((new_p_x, new_p_y), person_norm, color=color, fill=False)
                axes.add_artist(draw_circle)

            # the current "social" distance for nao
            draw_circle2 = plt.Circle((nao_x, nao_y), nao_norm_b, color="red", fill=False)
            # axes.set_aspect(1)
            axes.add_artist(draw_circle2)
            draw_circle2b = plt.Circle((nao_x, nao_y), nao_norm_c, color="red", fill=False)
            # axes.set_aspect(1)
            axes.add_artist(draw_circle2b)

            # the average social distance for the current society (the distance to which nao should tend)
            draw_circle3 = plt.Circle((nao_x, nao_y), norms_societies[society_idx], color="red", linestyle='dotted', fill=False)
            axes.add_artist(draw_circle3)

            if person_greets:
                axes.text(new_p_x, new_p_y, "Hello Nao!", fontsize=12)
            if nao_greets:
                axes.text(nao_x, nao_y, nao_greetings, fontsize=12)

            fig.canvas.draw()
            fig.canvas.flush_events()




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='spade bdi basic example')
    parser.add_argument('--server', type=str, default="localhost", help='XMPP server address.')
    parser.add_argument('--name', type=str, default="sarbdiagent", help='XMPP name for the agent.')
    parser.add_argument('--password', type=str, default="bdipassword", help='XMPP password for the agent.')
    args = parser.parse_args()

    enable_gui = False #todo: to remove the guy stuff or move appropriately somewhere
    gui_queue = None
    if enable_gui:
        # for the plots
        gui_queue = mp.Queue()
        p = mp.Process(target=worker, args=(gui_queue,))
        p.start()

    print("Starting agent")
    workers_to_start = [
        # "sys_handler",
        "norm_adapter",
        "chatter",
        # "position_handler",
        # "vision_handler",
        # "posture_handler",
        "collector"
    ]
    a = SARBDIAgent("{}@{}".format(args.name, args.server), args.password, gui_queue=gui_queue, workers_to_start=workers_to_start)
    future = a.start()
    future.result()
    print("Startup ended")
    # a.web.start(hostname="127.0.0.1", port="10000")
    # wait until user interrupts with ctrl+C
    while not a.my_behav.is_killed():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
    a.stop()

# print("Initial beliefs")
# a.bdi_core.bdi.print_beliefs()
# time.sleep(1)
# print("Setting belief car azul big")
# a.bdi_core.bdi.set_belief("car", "azul", "big")
# time.sleep(1)
# print("New beliefs")
# a.bdi_core.bdi.print_beliefs()
# print("GETTING FIRST CAR BELIEF")
# print(a.bdi_core.bdi.get_belief("car"))
# a.bdi_core.bdi.print_beliefs()
# print("Removing car azul big belief")
# a.bdi_core.bdi.remove_belief("car", 'azul', "big")
# time.sleep(1)
# a.bdi_core.bdi.print_beliefs()
# print(a.bdi_core.bdi.get_beliefs())
# print("Setting belief car amarillo")
# a.bdi_core.bdi.set_belief("car", 'amarillo')
# time.sleep(1)
# a.bdi_core.bdi.print_beliefs()

# a.stop().result()
#
# quit_spade()