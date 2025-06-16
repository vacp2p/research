# !!! THIS IS WIP (analyze the code structure at your own risk ^.^')
# the scope of this is still undefined; we want to avoid premature generalization
# - todo: separate the part on latency
# based on ../whisper_scalability/whisper.py

from typing import List
import matplotlib.pyplot as plt
import numpy as np

from cases import (
    Case,
    Case1,
    Case2,
    Case3,
    Case4,
    LatencyCase1,
    ShardingCase1,
    ShardingCase2,
    ShardingCase3,
)
from utils import bcolors

# Run cases
# -----------------------------------------------------------

# Print goals
print("")
print(
    bcolors.HEADER
    + "Waku relay theoretical model results (single shard and multi shard scenarios)."
    + bcolors.ENDC
)

cases: List[Case] = [
    Case1(),
    Case2(),
    Case3(),
    Case4(),
    ShardingCase1(),
    ShardingCase2(),
    ShardingCase3(),
    LatencyCase1(),
]

for case in cases:
    print(case.description)

# Plot
# -----------------------------------------------------------


def plot_load(caption: str, cases: List[Case], file_path: str):
    plt.clf()  # clear current plot

    n_users = np.logspace(2, 6, num=5)
    print(n_users)

    plt.xlim(100, 10**4)
    plt.ylim(1, 10**4)

    for case in cases:
        plt.plot(n_users, case.load(n_users), label=case.label, linewidth=4, linestyle="dashed")

    plt.xlabel("number of users (log)")
    plt.ylabel("mb/hour (log)")
    plt.legend(cases, loc="upper left")
    plt.xscale("log")
    plt.yscale("log")

    plt.axhspan(0, 10, facecolor="0.2", alpha=0.2, color="blue")
    plt.axhspan(10, 100, facecolor="0.2", alpha=0.2, color="green")
    plt.axhspan(
        100, 3000, facecolor="0.2", alpha=0.2, color="orange"
    )  # desktop nodes can handle this; load comparable to streaming (but both upload and download, and with spikes)
    plt.axhspan(3000, 10**6, facecolor="0.2", alpha=0.2, color="red")

    plt.figtext(0.5, 0.01, caption, wrap=True, horizontalalignment="center", fontsize=12)

    # plt.show()

    figure = plt.gcf()  # get current figure
    figure.set_size_inches(16, 9)
    # plt.savefig("waku_scaling_plot.svg")
    plt.savefig(file_path, dpi=300, orientation="landscape")


plot_load(
    caption="Plot 1: single shard.",
    cases=[Case1(), Case2(), Case3(), Case4()],
    file_path="waku_scaling_single_shard_plot.png",
)

plot_load(
    caption="Plot 2: multi shard.",
    cases=[
        Case1(
            label="sharding store",
            legend="Sharding store load; participate in all shards; top: 6-regular",
        ),
        ShardingCase1(),
        ShardingCase2(),
        ShardingCase3(),
    ],
    file_path="",
)
