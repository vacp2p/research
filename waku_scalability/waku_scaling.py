# !!! THIS IS WIP (analyze the code structure at your own risk ^.^')
# the scope of this is still undefined; we want to avoid premature generalization
# - todo: separate the part on latency
# based on ../whisper_scalability/whisper.py

import matplotlib.pyplot as plt
import numpy as np
import math
from pathlib import Path

import sys
import json, ast
import typer
import logging as log

from scipy.stats import truncnorm
from enum import Enum, EnumMeta


# we currently support the following two network types
class networkType(Enum):
    NEWMANWATTSSTROGATZ = "newmanwattsstrogatz"  # mesh, small-world
    REGULAR = "regular"  # d_lazy


#JSON/YAML keys: for consistency and avoid stupid bugs
class Keys:
    GENNET  =   "gennet"
    GENLOAD =   "wls"
    JSON    =   "json"
    YAML    =   "yaml"
    BATCH   =   "batch"
    RUNS    =   "runs"
    EXPLORE =   "explore"
    PER_NODE =  "per_node"
    BMARK   =   "benchmark"
    OPREFIX =   "out"
#    MSGPHR  =   "msgphr"
#    SIZE    =   "size"


# Util and format functions
#-----------------------------------------------------------

class IOFormats:
    def __init__(self):
        self.HEADER = '\033[95m'
        self.OKBLUE = '\033[94m'
        self.OKGREEN = '\033[92m'
        self.WARNING = '\033[93m'
        self.FAIL = '\033[91m'
        self.ENDC = '\033[0m'
        self.BOLD = '\033[1m'
        self.UNDERLINE = '\033[4m'

    def sizeof_fmt(self, num):
        return "%.1f%s" % (num, "MB")

    def sizeof_fmt_kb(self, num):
        return "%.2f%s" % (num*1024, "KB")

    def magnitude_fmt(self, num):
        for x in ['','k','m']:
            if num < 1000:
                return "%2d%s" % (num, x)
            num /= 1000

    # Color format based on daily bandwidth usage
    # <10mb/d = good, <30mb/d ok, <100mb/d bad, 100mb/d+ fail.
    def load_color_prefix(self, load):
        if load < (10):
            color_level = self.OKBLUE
        elif load < (30):
            color_level = self.OKGREEN
        elif load < (100):
            color_level = self.WARNING
        else:
            color_level = self.FAIL
        return color_level

    def load_color_fmt(self, load, string):
        return self.load_color_prefix(load) + string + self.ENDC

    def print_header(self, string):
        print(self.HEADER + string + self.ENDC + "\n")

    # Print goals
    def print_goal(self):
        print("")
        print(self.HEADER + "Waku relay theoretical model results (single shard and multi shard scenarios)." + self.ENDC)



# Config holds the data for the individual runs. Every analysis instance is a Config instance
class Config:

    # We need 12 params to fully instantiate Config. Set the defaults for the missing
    def __init__(self,
            num_nodes=4, fanout=6,
            network_type=networkType.REGULAR.value,
            messages='{\"topic1\":{\"size\":0.002,\"msgpsec\":0.001389}}',
            #_size=0.002, msgpsec=0.00139,
            per_hop_delay=0.001,
            gossip_msg_size=0.002, gossip_window_size=3, gossip2reply_ratio=0.01,
            nodes_per_shard=10000, shards_per_node=3, pretty_print=IOFormats()):
        # set the current Config values
        self.num_nodes = num_nodes                      # number of wakunodes
        self.fanout = fanout                            # generative fanout
        self.network_type = network_type                # regular, small world etc

        '''
        self.msg_size = msg_size                        # avg message size in MBytes
        self.msgpsec = msgpsec                          # avg # of messages per user per sec
        '''
        self.messages = messages

        self.per_hop_delay = per_hop_delay              # per-hop delay = 0.01 sec
        self.gossip_msg_size = gossip_msg_size          # avg gossip msg size in MBytes
        self.gossip_window_size = gossip_window_size    # max gossip history window size
        self.gossip2reply_ratio = gossip2reply_ratio    # fraction of replies/hits to a gossip msg
        self.nodes_per_shard = nodes_per_shard          # max number of nodes per shard
        self.shards_per_node = shards_per_node          # avg number of shards a node is part of

        # secondary parameters, derived from primary
        msg_size_sum, self.peruser_message_load, self.total_msgphr = 0, 0, 0
        for k, v in self.messages.items():
            m = self.messages[k]
            m["msgphr"] = m["msgpsec"]*60*60
            msg_size_sum += m["size"]
            self.peruser_message_load += m["msgphr"]*m["size"]
            self.total_msgphr += m["msgphr"]
        self.avg_msg_size = msg_size_sum / len(self.messages)

        '''
        self.msgphr = msgpsec*60*60                     # msgs per hour derived from msgpsec
        '''
        self.d = 1.5 * self.fanout if network_type == networkType.NEWMANWATTSSTROGATZ.value else self.fanout
        self.d_lazy = self.d - 6  if self.d > 6 else 0 # avg degree for gossip
        if self.d > 6:
            self.d = 6
        self.base_assumptions = ["a1", "a2", "a3", "a4"]
        self.pretty_print = pretty_print
        # Assumption strings (general/topology)
        self.Assumptions = {
           # "a1"  :  "- A01. Message size (static): " + self.pretty_print.sizeof_fmt_kb(self.msg_size),
            "a1"  :  "- A01. Message size (static): " +  str(self.messages),
            #"a2"  : "- A02. Messages sent per node per hour (static) (assuming no spam; but also no rate limiting.): " + str(self.msgphr),
            "a2"  : "- A02. Messages sent per node per hour (static) (assuming no spam; but also no rate limiting.): " +  str(self.messages),
            "a3"  : "- A03. The network topology is a d-regular graph of degree (static): " + str(int(self.d)),
            "a4"  : "- A04. Messages outside of Waku Relay are not considered, e.g. store messages.",
            "a5"  : "- A05. Messages are only sent once along an edge. (requires delays before sending)",
            "a6"  : "- A06. Messages are sent to all d-1 neighbours as soon as receiving a message (current operation)", # Thanks @Mmenduist
            "a7"  : "- A07. Single shard (i.e. single pubsub mesh)",
            "a8"  : "- A08. Multiple shards; mapping of content topic (multicast group) to shard is 1 to 1",
            "a9"  : "- A09. Max number of nodes per shard (static) " + str(self.nodes_per_shard),
            "a10" : "- A10. Number of shards a given node is part of (static) " + str(self.shards_per_node),
            "a11" : "- A11. Number of nodes in the network is variable.\n\
                    These nodes are distributed evenly over " + str(self.shards_per_node) + " shards.\n\
                    Once all of these shards have " + str(self.nodes_per_shard) + " nodes, new shards are spawned.\n\
                    These new shards have no influcene on this model, because the nodes we look at are not part of these new shards.",
            "a12" : "- A12. Including 1:1 chat. Messages sent to a given user are sent into a 1:1 shard associated with that user's node.\n\
                    Effectively, 1:1 chat adds a receive load corresponding to one additional shard a given node has to be part of.",
            #"a13" : "- A13. 1:1 chat messages sent per node per hour (static): " + str(self.msgphr), # could introduce a separate variable here
            "a13" : "- A13. 1:1 chat messages sent per node per hour (static): " + str(self.messages), # could introduce a separate variable here
            "a14" : "- A14. 1:1 chat shards are filled one by one (not evenly distributed over the shards).\n\
                    This acts as an upper bound and overestimates the 1:1 load for lower node counts.",
            "a15" : "- A15. Naive light node. Requests all messages in shards that have (large) 1:1 mapped multicast groups the light node is interested in.",

            # Assumption strings (store)
            "a21" : "- A21. Store nodes do not store duplicate messages.",

            # Assumption strings (gossip)
            "a31" : "- A21. Gossip is not considered.",
            "a32" : "- A32. Gossip message size (IHAVE/IWANT) (static):" + self.pretty_print.sizeof_fmt_kb(self.gossip_msg_size),
            "a33" : "- A33. Ratio of IHAVEs followed-up by an IWANT (incl. the actual requested message):" + str(self.gossip2reply_ratio),

            # Assumption strings (delay)
            "a41" : "- A41. Delay is calculated based on an upper bound of the expected distance.",
            "a42" : "- A42. Average delay per hop (static): " + str(self.per_hop_delay) + "s."
        }
        self.display()
        self.pretty_print.print_goal()

    # display the Config
    def display(self):
        print(f'Config = {self.num_nodes}, {self.fanout} -> {(self.d, self.d_lazy)}, {self.network_type}, '
              #f'{self.msg_size}MBytes, {self.msgpsec}/sec({self.msgphr}/hr), '
              f'messages={str(self.messages)}, '
              f'{self.gossip_msg_size}MBytes, {self.gossip_window_size}, {self.gossip2reply_ratio},'
              f' {self.nodes_per_shard}, {self.shards_per_node}, {self.per_hop_delay}secs')


    # Print assumptions : with a base set
    def print_assumptions1(self, xs):
        print("Assumptions/Simplifications:")
        alist = self.base_assumptions + xs
        for a in alist:
            if a in self.Assumptions:
                print(self.Assumptions[a])
            else:
                log.error(f'Unknown assumption: ' + a)
                sys.exit(0)
        print("")


    # Print assumptions: all
    def print_assumptions(self, xs):
        print("Assumptions/Simplifications:")
        for a in xs:
            if a in self.Assumptions:
                print(self.Assumptions[a])
            else:
                log.error(f'Unknown assumption: ' + a)
                sys.exit(0)
        print("")



# Analysis performs the runs. It creates a Config object and runs the analysis on it
class Analysis(Config):
    # accept variable number of parameters with missing values set to defaults
    def __init__(self, **kwargs):
        Config.__init__(self, **kwargs)

    def pretty_print_usage(self, load_fn, num_nodes):
        load = load_fn(num_nodes)
        print (self.pretty_print.load_color_fmt(load, "For " + self.pretty_print.magnitude_fmt(num_nodes) + " users, receiving bandwidth is " + self.pretty_print.sizeof_fmt(load) + "/hour"))

    def print_usage(self, load_fn, num_nodes, explore=True):
        if explore:
            self.pretty_print_usage(load_fn, 100)
            self.pretty_print_usage(load_fn, 1000)
            self.pretty_print_usage(load_fn, 1000 * 10)
        else:
            self.pretty_print_usage(load_fn, num_nodes)

    def pretty_print_latency(self, latency_fn, num_nodes, degree):
        latency =  latency_fn(num_nodes, degree)
        print(self.pretty_print.load_color_fmt(latency, "For " + self.pretty_print.magnitude_fmt(num_nodes) + " the average latency is " + ("%.5f" % latency) + " s"))


    def print_latency(self, latency_fn, average_node_degree, explore=True):
        if explore:
            self.pretty_print_latency(latency_fn, 100, average_node_degree)
            self.pretty_print_latency(latency_fn, 1000, average_node_degree)
            self.pretty_print_latency(latency_fn, 1000 * 10, average_node_degree)
        else:
            self.pretty_print_latency(latency_fn, self.num_nodes, average_node_degree)


    # Case 1 :: singe shard, unique messages, store
    # sharding case 1: multi shard, n*(d-1) messages, gossip
    def load_sharding_case1(self, n_users):
        load_per_node_per_shard = self.load_case4(np.minimum(n_users/3, self.nodes_per_shard))
        return self.shards_per_node * load_per_node_per_shard

    def load_case1(self, n_users):
        return self.peruser_message_load * n_users
        #return  self.msg_size *self.msgphr * n_users

    def print_load_case1(self):
        print("")
        self.pretty_print.print_header("Load case 1 (store load; corresponds to received load per naive light node)")
        self.print_assumptions1(["a7", "a21"])
        self.print_usage(self.load_case1, self.num_nodes)
        print("")
        print("------------------------------------------------------------")

    # Case 2 :: single shard, (n*d)/2 messages
    def load_case2(self, n_users):
        return self.peruser_message_load * self.num_edges(self.network_type, self.fanout)
        #return self.msg_size * self.msgphr * self.num_edges(self.network_type, self.fanout)

    def print_load_case2(self, explore=True):
        print("")
        self.pretty_print.print_header("Load case 2 (received load per node)")
        self.print_assumptions1(["a5", "a7", "a31"])
        self.print_usage(self.load_case2, self.num_nodes, explore)
        print("")
        print("------------------------------------------------------------")

    def load_case2point1(self, n_users):
        print(f"case 2.1 {self.num_nodes, n_users, self.num_edges(self.network_type, self.fanout)}")
        return self.peruser_message__load * n_users\
                * self.num_edges(self.network_type, self.fanout)
        #return self.msg_size * self.msgphr * n_users\
        #        * self.num_edges(self.network_type, self.fanout)

    def print_load_case2point1(self, explore=True):
        print("")
        self.pretty_print.print_header("Load case 2.1 (received load per node)")
        self.print_assumptions1(["a5", "a7", "a31"])
        self.print_usage(self.load_case2point1, self.num_nodes, explore)
        print("")
        print("------------------------------------------------------------")

    # Case 3 :: single shard n*(d-1) messages
    def load_case3(self, n_users):
        return self.peruser_message_load * n_users * (self.d-1)
        #return self.msg_size * self.msgphr * n_users * (self.d-1)

    def print_load_case3(self):
        print("")
        self.pretty_print.print_header("Load case 3 (received load per node)")
        self.print_assumptions1(["a6", "a7", "a31"])
        self.print_usage(self.load_case3, self.num_nodes)
        print("")
        print("------------------------------------------------------------")

    # Case 4:single shard n*(d-1) messages, gossip
    def load_case4(self, n_users):
        num_msgsphour =  self.total_msgphr * n_users * (self.d-1) # see case 3
        #messages_load =  self.msg_size * num_msgsphour
        messages_load =  self.peruser_message_load * n_users * (self.d-1)
        num_ihave = num_msgsphour * self.d_lazy * self.gossip_window_size
        ihave_load  = num_ihave * self.gossip_msg_size
        gossip_response_load  = (num_ihave * (self.gossip_msg_size + self.avg_msg_size)) * self.gossip2reply_ratio  # reply load contains both an IWANT (from requester to sender), and the actual wanted message (from sender to requester)
        gossip_total = ihave_load + gossip_response_load
        #print(f"bandwidth {(messages_load,  gossip_total,self.d, self.d_lazy)} = {messages_load + gossip_total}")
        return messages_load + gossip_total

    def print_load_case4(self, explore=True):
        print("")
        self.pretty_print.print_header("Load case 4 (received load per node incl. gossip)")
        self.print_assumptions1(["a6", "a7", "a32", "a33"])
        self.print_usage(self.load_case4, self.num_nodes, explore=explore)
        print("")
        print("------------------------------------------------------------")


    def load_case5(self, n_users):
        nedges = self.num_edges(self.network_type, self.fanout)
        nedges_regular = self.num_edges(networkType.REGULAR.value, 6)
        edge_diff = nedges - nedges_regular

        eager_fraction = 1 if self.d_lazy <= 0 or edge_diff <= 0 else nedges_regular / nedges
        lazy_fraction = 1 - eager_fraction

        eager_edges, lazy_edges = nedges * eager_fraction , nedges * lazy_fraction

        #print(f"{(nedges, nedges_regular)} = {eager_fraction, lazy_fraction} {self.gossip2reply_ratio}")
        total_load =  eager_edges * n_users * self.peruser_msg_load \
                      + lazy_edges * 60 * self.gossip_window_size \
                            * (self.gossip_msg_size + self.gossip2reply_ratio * self.avg_msg_size)
        #print(f"{n_users} users = {total_load}, {eager_edges * self.msgphr * n_users * self.msg_size}")
        return total_load


    def print_load_case5(self, explore=True):
        print("")
        self.pretty_print.print_header("Load case 5 (received load per node incl. gossip)")
        self.print_assumptions1(["a6", "a7", "a32", "a33"])
        self.print_usage(self.load_case5, self.num_nodes, explore=explore)
        print("")
        print("------------------------------------------------------------")

    # latency cases
    def latency_case1(self, n_users, degree):
        return self.avg_node_distance_upper_bound() * self.per_hop_delay

    def print_latency_case1(self, explore=True):
        print("")
        self.pretty_print.print_header("Latency case 1 :: Topology: 6-regular graph. No gossip (note: gossip would help here)")
        self.print_assumptions(["a3", "a41", "a42"])
        self.print_latency(self.latency_case1, self.fanout, explore=explore)
        print("")
        print("------------------------------------------------------------")

    def print_load_sharding_case1(self):
        print("")
        self.pretty_print.print_header("load sharding case 1 (received load per node incl. gossip)")
        self.print_assumptions1(["a6", "a8", "a9", "a10", "a11", "a32", "a33"])
        self.print_usage(self.load_sharding_case1, self.num_nodes)
        print("")
        print("------------------------------------------------------------")

    # sharding case 2: multi shard, n*(d-1) messages, gossip, 1:1 chat
    def load_sharding_case2(self, n_users):
        load_per_node_per_shard = self.load_case4(np.minimum(n_users/3, self.nodes_per_shard))
        load_per_node_1to1_shard = self.load_case4(np.minimum(n_users, self.nodes_per_shard))
        return (self.shards_per_node * load_per_node_per_shard) + load_per_node_1to1_shard

    def print_load_sharding_case2(self):
        print("")
        self.pretty_print.print_header("load sharding case 2 (received load per node incl. gossip and 1:1 chat)")
        self.print_assumptions1(["a6", "a8", "a9", "a10", "a11", "a12", "a13", "a14", "a32", "a33"])
        self.print_usage(self.load_sharding_case2, self.num_nodes)
        print("")
        print("------------------------------------------------------------")

    # sharding case 3: multi shard, naive light node
    def load_sharding_case3(self, n_users):
        load_per_node_per_shard = self.load_case1(np.minimum(n_users/3, self.nodes_per_shard))
        return self.shards_per_node * load_per_node_per_shard

    def print_load_sharding_case3(self):
        print("")
        self.pretty_print.print_header("load sharding case 3 (received load naive light node.)")
        self.print_assumptions1(["a6", "a8", "a9", "a10", "a15", "a32", "a33"])
        self.print_usage(self.load_sharding_case3, self.num_nodes)
        print("")
        print("------------------------------------------------------------")

    def run(self, explore=True):
        if explore :
            self.print_load_case1()
            self.print_load_case2()
            self.print_load_case3()
            self.print_load_case4()

            self.print_latency_case1()

            self.print_load_sharding_case1()
            self.print_load_sharding_case2()
            self.print_load_sharding_case3()
        else:
            #self.print_load_case2(explore=explore)
            self.print_load_case2point1(explore=explore)
            self.print_load_case4(explore=explore)
            self.print_load_case5(explore=explore)
            #self.print_latency_case1(explore=explore)

    def plot_load(self):
        plt.clf() # clear current plot

        n_users = np.logspace(2, 6, num=5)
        print(n_users)

        plt.xlim(100, 10**4)
        plt.ylim(1, 10**4)

        plt.plot(n_users, load_case1(n_users), label='case 1', linewidth=4, linestyle='dashed')
        plt.plot(n_users, load_case2(n_users), label='case 2', linewidth=4, linestyle='dashed')
        plt.plot(n_users, load_case3(n_users), label='case 3', linewidth=4, linestyle='dashed')
        plt.plot(n_users, load_case4(n_users), label='case 4', linewidth=4, linestyle='dashed')

        case1 = "Case 1. top: 6-regular;  store load (also: naive light node)"
        case2 = "Case 2. top: 6-regular;  receive load per node, send delay to reduce duplicates"
        case3 = "Case 3. top: 6-regular;  receive load per node, current operation"
        case4 = "Case 4. top: 6-regular;  receive load per node, current operation, incl. gossip"

        plt.xlabel('number of users (log)')
        plt.ylabel('mb/hour (log)')
        plt.legend([case1, case2, case3, case4], loc='upper left')
        plt.xscale('log')
        plt.yscale('log')

        plt.axhspan(0, 10, facecolor='0.2', alpha=0.2, color='blue')
        plt.axhspan(10, 100, facecolor='0.2', alpha=0.2, color='green')
        plt.axhspan(100, 3000, facecolor='0.2', alpha=0.2, color='orange') # desktop nodes can handle this; load comparable to streaming (but both upload and download, and with spikes)
        plt.axhspan(3000, 10**6, facecolor='0.2', alpha=0.2, color='red')

        caption = "Plot 1: single shard."
        plt.figtext(0.5, 0.01, caption, wrap=True, horizontalalignment='center', fontsize=12)

        plt.show()

        figure = plt.gcf() # get current figure
        figure.set_size_inches(16, 9)
        # plt.savefig("waku_scaling_plot.svg")
        #plt.savefig("waku_scaling_single_shard_plot.png", dpi=300, orientation="landscape")

    def plot_load_sharding(self):
        plt.clf() # clear current plot

        n_users = np.logspace(2, 6, num=5)
        print(n_users)

        plt.xlim(100, 10**6)
        plt.ylim(1, 10**5)

        plt.plot(n_users, load_case1(n_users), label='sharding store', linewidth=4, linestyle='dashed') # same as without shardinig, has to store *all* messages
        plt.plot(n_users, load_sharding_case1(n_users), label='case 1', linewidth=4, linestyle='dashed')
        plt.plot(n_users, load_sharding_case2(n_users), label='case 2', linewidth=4, linestyle='dashed')
        plt.plot(n_users, load_sharding_case3(n_users), label='case 3', linewidth=4, linestyle='dashed')

        case_store = "Sharding store load; participate in all shards; top: 6-regular"
        case1 = "Sharding case 1. sharding: top: 6-regular;  receive load per node, incl gossip"
        case2 = "Sharding case 2. sharding: top: 6-regular;  receive load per node, incl gossip and 1:1 chat"
        case3 = "Sharding case 3. sharding: top: 6-regular;  regular load for naive light node"

        plt.xlabel('number of users (log)')
        plt.ylabel('mb/hour (log)')
        plt.legend([case_store, case1, case2, case3], loc='upper left')
        plt.xscale('log')
        plt.yscale('log')

        plt.axhspan(0, 10, facecolor='0.2', alpha=0.2, color='blue')
        plt.axhspan(10, 100, facecolor='0.2', alpha=0.2, color='green')
        plt.axhspan(100, 3000, facecolor='0.2', alpha=0.2, color='orange') # desktop nodes can handle this; load comparable to streaming (but both upload and download, and with spikes)
        plt.axhspan(3000, 10**6, facecolor='0.2', alpha=0.2, color='red')

        caption = "Plot 2: multi shard."
        plt.figtext(0.5, 0.01, caption, wrap=True, horizontalalignment='center', fontsize=12)

        plt.show()

        figure = plt.gcf() # get current figure
        figure.set_size_inches(16, 9)
        # plt.savefig("waku_scaling_plot.svg")
        #plt.savefig("waku_scaling_multi_shard_plot.png", dpi=300, orientation="landscape")

    def plot(self):
        self.plot_load()
        self.plot_load_sharding()

    def num_edges(self, network_type, fanout):
        # we assume and even d; d-regular graphs with both where both n and d are odd don't exist
        num_edges = self.num_nodes * fanout/2
        if network_type == networkType.REGULAR.value:
            return num_edges
        elif network_type == networkType.NEWMANWATTSSTROGATZ.value:
            # NEWMANWATTSSTROGATZ starts as a regular graph
            #   0. rewire random edged
            #   1. add additional ~ \beta * num_nodes*degree/2 edges to shorten the paths
            #       # \beta used = 0.5
            # this is a relatively tight estimate
            return num_edges + 0.5 * self.num_nodes * fanout/2
        else:
            log.error(f'num_edges: Unknown network type {network_type}')
            sys.exit(0)

    def avg_node_distance_upper_bound(self):
        if self.network_type == networkType.REGULAR.value:
            return math.log(self.num_nodes, self.fanout)
        elif self.network_type == networkType.NEWMANWATTSSTROGATZ.value:
            # NEWMANWATTSSTROGATZ is small world and random
            # a tighter estimate
            return 2*math.log(self.num_nodes/self.fanout, self.fanout)
        else:
            log.error(f'avg_node_distance: Unknown network type {self.network_type}')
            sys.exit(0)

def _sanity_check(fname, keys, ftype=Keys.JSON):
    if not fname.exists():
        log.error(f'The file "{fname}" does not exist')
        sys.exit(0)
    try:
        with open(fname, 'r') as f:     # Load config file
            if ftype == Keys.JSON:      # Both batch and kurtosis use json
                json_conf = json.load(f)
                for key in keys:
                    if key not in json_conf:
                        log.error(f'The json  key "{key}" not found in {fname}')
                        sys.exit(0)
                return json_conf
            elif ftype == "yaml":   # Shadow uses yaml
                log.error(f'YAML is not yet supported : {fname}')
                sys.exit(0)
                #yaml_conf = json.load(f)
                #return yaml_conf
    except Exception as ex:
        raise typer.BadParameter(str(ex))
    log.debug(f'Sanity check: All Ok')

app = typer.Typer()

@app.command()
def wakurtosis(ctx: typer.Context, config_file: Path,
                explore : bool = typer.Option(True,
                    help="Explore or not to explore")):
    wakurtosis_json = _sanity_check(config_file, [Keys.GENNET, Keys.GENLOAD], Keys.JSON)

    num_nodes = wakurtosis_json["gennet"]["num_nodes"]
    fanout = wakurtosis_json["gennet"]["fanout"]
    network_type = wakurtosis_json["gennet"]["network_type"]
    msg_size = 1.5 * (wakurtosis_json["wls"]["min_packet_size"] +
                                wakurtosis_json["wls"]["max_packet_size"])/(2*1024*1024)
    #msg_size = truncnorm.mean(wakurtosis_json["wls"]["min_packet_size"],
    #                            wakurtosis_json["wls"]["max_packet_size"])/(1024*1024)
    msgpsec = wakurtosis_json["wls"]["message_rate"]/wakurtosis_json["gennet"]["num_nodes"]

    messages = {}
    messages["topic1"] = {"size" : msg_size, "msgpsec" : msgpsec}
    analysis = Analysis(**{ "num_nodes" : num_nodes,
                            "fanout" : fanout,
                            "messages" : messages,
                            "network_type" : network_type,
                            "per_hop_delay" : 0.1 # TODO: pick from wakurtosis
                            })

    analysis.run(explore=explore)
    print(f'kurtosis: done')

@app.command()
def batch(ctx: typer.Context, batch_file: Path):
    batch_json = _sanity_check(batch_file, [ Keys.BATCH ], Keys.JSON)
    explore  = batch_json[Keys.BATCH][Keys.EXPLORE]
    per_node = batch_json[Keys.BATCH][Keys.PER_NODE]
    runs = batch_json[Keys.BATCH][Keys.RUNS]
    for r in runs:
        run = runs[r]
        run["per_hop_delay"] = 0.010
        if not per_node:
            run["msgpsec"] = run["msgpsec"] / run["num_nodes"]
        analysis = Analysis(**run)
        analysis.run(explore=explore)
    print(f'batch: done')

@app.command()
def shadow(ctx: typer.Context, config_file: Path):
    yaml = _sanity_check(config_file, [], Keys.YAML)
    print("shadow: done {yaml}")

@app.command()
def cli(ctx: typer.Context,
         num_nodes: int = typer.Option(4,
             help="Set the number of nodes"),
         fanout: float = typer.Option(6.0,
             help="Set the arity"),
         network_type: networkType = typer.Option(networkType.REGULAR.value,
             help="Set the network type"),
         messages: str = typer.Argument("{\"topic1\":{\"size\":0.002,\"msgpsec\":0.001389}}",
             callback=ast.literal_eval, help="Topics traffic spec"),
         #msg_size: float = typer.Option(0.002,
         #    help="Set message size in MBytes"),
         #msgphr: float = typer.Option(0.001389,
         #    help="Set message rate per second on a shard/topic"),
         gossip_msg_size: float = typer.Option(0.00005,
             help="Set gossip message size in MBytes"),
         gossip_window_size: int = typer.Option(3,
             help="Set gossip history window size"),
         gossip2reply_ratio: float = typer.Option(0.01,
             help="Set the Gossip to reply ratio"),
         nodes_per_shard: int = typer.Option(10000,
             help="Set the number of nodes per shard/topic"),
         shards_per_node: int = typer.Option(3,
             help="Set the number of shards a node is part of"),
         per_hop_delay: float = typer.Option(0.1,
             help="Set the delay per hop"),
         explore : bool = typer.Option(True,
             help="Explore or not to explore")):

    analysis = Analysis(**{ "num_nodes" : num_nodes,
                            "fanout" : fanout,
                            "network_type" : network_type.value,
                            "messages" : messages,
                            #"msgs" : f'{\"msg1\" : { \"msg_size\" : {msg_size}
                            #"msg_size" : msg_size,
                            #"msgpsec" : msgphr/(60*60),
                            "per_hop_delay" : 0.1, # TODO: pick from wakurtosis
                            "gossip_msg_size" : gossip_msg_size,
                            "gossip_window_size":gossip_window_size,
                            "gossip2reply_ratio":gossip2reply_ratio,
                            "nodes_per_shard":nodes_per_shard,
                            "shards_per_node":shards_per_node})
    analysis.run(explore=explore)
    print("cli: done")

if __name__ == "__main__":
    app()

"""
# general / topology
average_node_degree = 6  # has to be even
message_size = 0.002 # in MB (Mega Bytes)
self.msgphr = 5 # on a a single pubsub topic / shard / per node

# gossip
self.gossip_msg_size = 0.00005 # 50Bytes in MB (see https://github.com/libp2p/specs/pull/413#discussion_r1018821589 )
d_lazy = 6 # gossip out degree
mcache_gossip = 3 # Number of history windows to use when emitting gossip (see https://github.com/libp2p/specs/blob/master/pubsub/gossipsub/gossipsub-v1.0.md)
avg_ratio_gossip_replys = 0.01 # -> this is a wild guess! (todo: investigate)

# multi shard
avg_nodes_per_shard = 10000 # average number of nodes that a part of a single shard
avg_shards_per_node = 3    # average number of shards a given node is part of

# latency
average_delay_per_hop = 0.1 #s
"""
