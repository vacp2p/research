# !!! THIS IS WIP (analyze the code structure at your own risk ^.^')
# the scope of this is still undefined; we want to avoid premature generalization
# - todo: separate the part on latency
# based on ../whisper_scalability/whisper.py

import matplotlib.pyplot as plt
import numpy as np
import math
from pathlib import Path

import sys
import json
import typer
import logging as log
from enum import Enum, EnumMeta


# we do not currently use these - for future extensions
class networkType(Enum):
    NEWMANWATTSSTROGATZ = "newmanwattsstrogatz"  # mesh, smallworld
    REGULAR = "regular"  # d_lazy


#JSON/YAML keys: for consistency and avoid stupid bugs
class Keys:
    GENNET  =   "gennet"
    GENLOAD =   "wls"
    JSON    =   "json"
    YAML    =   "yaml"
    BATCH   =   "batch"
    RUNS    =   "runs"


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


    def usage_str(self, load_users_fn, n_users):
        load = load_users_fn(n_users)
        return self.load_color_fmt(load, "For " + self.magnitude_fmt(n_users) + " users, receiving bandwidth is " + self.sizeof_fmt(load_users_fn(n_users)) + "/hour")


    def print_usage(self, load_users):
        print(self.usage_str(load_users, 100))
        print(self.usage_str(load_users, 100 * 100))
        print(self.usage_str(load_users, 100 * 100 * 100))


    def latency_str(self, latency_users_fn, n_users, degree):
        latency =  latency_users_fn(n_users, degree)
        return self.load_color_fmt(latency, "For " + self.magnitude_fmt(n_users) + " the average latency is " + ("%.3f" % latency_users_fn(n_users, degree)) + " s")


    def print_latency(self, latency_users, average_node_degree):
        print(self.latency_str(latency_users, 100, average_node_degree))
        print(self.latency_str(latency_users, 100 * 100, average_node_degree))
        print(self.latency_str(latency_users, 100 * 100 * 100, average_node_degree))


    # Print goals
    def print_goal(self):
        print("")
        print(self.HEADER + "Waku relay theoretical model results (single shard and multi shard scenarios)." + self.ENDC)



# Config holds the data for the individual runs. Every analysis instance is a Config instance
class Config:
    '''
    def __init__(self):                 # the defaults
        self.num_nodes = 4              # number of wakunodes = 4
        self.fanout = 6                 # 'average' node degree = 6
        self.network_type = networkType.REGULAR.value   # regular nw: avg node degree is 'exact'
        self.msg_size = 0.002           # msg size in MBytes
        self.msgpsec = 0.00139          # msgs per sec in single pubsub topic/shard = 5 msgs/hr
        self.gossip_msg_size = 0.05     # gossip message size in KBytes = 50 bytes
        self.gossip_window_size = 3     # the history window for gossips = 3
        self.gossip2reply_ratio = 0.01  # fraction of gossips that elicit a reply = 0.01 (guess)
        self.nodes_per_shard = 10000    # avg number of nodes online and part of single shard
        self.shards_per_node = 3        # avg number of shards a wakunode participates
        self.per_hop_delay = 100        # avg delay per hop = 0.1 sec / 100 msec

        self.d_lazy = self.fanout        # gossip degree = 6
    '''

    # We need 12 params to correctly instantiate Config. Set the defaults for the missing
    def __init__(self,
            num_nodes=4, fanout=6,
            network_type=networkType.REGULAR.value,
            msg_size=0.002, msgpsec=0.00139, per_hop_delay=100,
            gossip_msg_size=0.002, gossip_window_size=3, gossip2reply_ratio=0.01,
            nodes_per_shard=10000, shards_per_node=3, pretty_print=IOFormats()):
        # set the current Config values
        self.num_nodes = num_nodes                      # number of nodes
        self.fanout = fanout                            # avg degree
        self.network_type = network_type                # regular, small world etc
        self.msg_size = msg_size                        # avg message size in MBytes
        self.msgpsec = msgpsec                          # avg # of messages per sec
        self.per_hop_delay = per_hop_delay              # per-hop delay = 0.01 sec
        self.gossip_msg_size = gossip_msg_size          # avg gossip msg size in MBytes
        self.gossip_window_size = gossip_window_size    # max gossip history window size
        self.gossip2reply_ratio = gossip2reply_ratio    # fraction of replies/hits to a gossip msg
        self.nodes_per_shard = nodes_per_shard          # max number of nodes per shard
        self.shards_per_node = shards_per_node          # avg number of shards a node is part of

        # secondary parameters, derived from primary
        self.msgphr = msgpsec*60*60                     # msgs per hour derived from msgpsec
        self.d_lazy = self.fanout                       # gossip degree = 6

        self.base_assumptions = ["a1", "a2", "a3", "a4"]
        self.pretty_print = pretty_print
        # Assumption strings (general/topology)
        self.Assumptions = {
            "a1"  :  "- A01. Message size (static): " + self.pretty_print.sizeof_fmt_kb(self.msg_size),
            "a2"  : "- A02. Messages sent per node per hour (static) (assuming no spam; but also no rate limiting.): " + str(self.msgphr),
            "a3"  : "- A03. The network topology is a d-regular graph of degree (static): " + str(self.fanout),
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
            "a13" : "- A13. 1:1 chat messages sent per node per hour (static): " + str(self.msgphr), # could introduce a separate variable here
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
        print( "Config = ", self.num_nodes, self.fanout, self.network_type,
                self.msg_size, self.msgpsec, self.msgphr,
                self.gossip_msg_size, self.gossip_window_size, self.gossip2reply_ratio,
                self.nodes_per_shard, self.shards_per_node, self.per_hop_delay, self.d_lazy)


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

    # Case 1 :: singe shard, unique messages, store
    # sharding case 1: multi shard, n*(d-1) messages, gossip
    def load_sharding_case1(self, n_users):
        load_per_node_per_shard = self.load_case4(np.minimum(n_users/3, self.nodes_per_shard))
        return self.shards_per_node * load_per_node_per_shard

    def load_case1(self, n_users):
        return self.msg_size * self.msgphr * n_users

    def print_load_case1(self):
        print("")
        self.pretty_print.print_header("Load case 1 (store load; corresponds to received load per naive light node)")
        self.print_assumptions1(["a7", "a21"])
        self.pretty_print.print_usage(self.load_case1)
        print("")
        print("------------------------------------------------------------")

    # Case 2 :: single shard, (n*d)/2 messages
    def load_case2(self, n_users):
        return self.msg_size * self.msgphr * self.num_edges_dregular(n_users, self.fanout)

    def print_load_case2(self):
        print("")
        self.pretty_print.print_header("Load case 2 (received load per node)")
        self.print_assumptions1(["a5", "a7", "a31"])
        self.pretty_print.print_usage(self.load_case2)
        print("")
        print("------------------------------------------------------------")

    # Case 3 :: single shard n*(d-1) messages
    def load_case3(self, n_users):
        return self.msg_size * self.msgphr * n_users * (self.fanout-1)

    def print_load_case3(self):
        print("")
        self.pretty_print.print_header("Load case 3 (received load per node)")
        self.print_assumptions1(["a6", "a7", "a31"])
        self.pretty_print.print_usage(self.load_case3)
        print("")
        print("------------------------------------------------------------")

    # Case 4:single shard n*(d-1) messages, gossip
    def load_case4(self, n_users):
        messages_received_per_hour =  self.msgphr * n_users * (self.fanout-1) # see case 3
        messages_load =  self.msg_size * messages_received_per_hour
        num_ihave = messages_received_per_hour * self.d_lazy * self.gossip_window_size
        ihave_load  = num_ihave * self.gossip_msg_size
        gossip_response_load  = (num_ihave * (self.gossip_msg_size + self.msg_size)) * self.gossip2reply_ratio # reply load contains both an IWANT (from requester to sender), and the actual wanted message (from sender to requester)
        gossip_total = ihave_load + gossip_response_load

        return messages_load + gossip_total

    def print_load_case4(self):
        print("")
        self.pretty_print.print_header("Load case 4 (received load per node incl. gossip)")
        self.print_assumptions1(["a6", "a7", "a32", "a33"])
        self.pretty_print.print_usage(self.load_case4)
        print("")
        print("------------------------------------------------------------")

    # latency cases
    def latency_case1(self, n_users, degree):
        return self.avg_node_distance_upper_bound(n_users, degree) * self.per_hop_delay

    def print_latency_case1(self):
        print("")
        self.pretty_print.print_header("Latency case 1 :: Topology: 6-regular graph. No gossip (note: gossip would help here)")
        self.print_assumptions(["a3", "a41", "a42"])
        self.pretty_print.print_latency(self.latency_case1, self.fanout)
        print("")
        print("------------------------------------------------------------")


    def print_load_sharding_case1(self):
        print("")
        self.pretty_print.print_header("load sharding case 1 (received load per node incl. gossip)")
        self.print_assumptions1(["a6", "a8", "a9", "a10", "a11", "a32", "a33"])
        self.pretty_print.print_usage(self.load_sharding_case1)
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
        self.pretty_print.print_usage(self.load_sharding_case2)
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
        self.pretty_print.print_usage(self.load_sharding_case3)
        print("")
        print("------------------------------------------------------------")

    def run(self):
        self.print_load_case1()
        self.print_load_case2()
        self.print_load_case3()
        self.print_load_case4()

        self.print_latency_case1()

        self.print_load_sharding_case1()
        self.print_load_sharding_case2()
        self.print_load_sharding_case3()


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

    def num_edges_dregular(self, num_nodes, degree):
        # we assume and even d; d-regular graphs with both where both n and d are odd don't exist
        return num_nodes * (degree/2)

    def avg_node_distance_upper_bound(self, n_users, degree):
        return math.log(n_users, degree)

def _sanity_check(fname, keys, ftype=Keys.JSON):
    print(f'sanity check: {fname}, {keys}, {ftype}')
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
    log.debug(f'sanity check: All Ok')

app = typer.Typer()

@app.command()
def kurtosis(ctx: typer.Context, config_file: Path):
    json = _sanity_check(config_file, [Keys.GENNET, Keys.GENLOAD], Keys.JSON)
    analysis = Analysis(
            json["gennet"]["num_nodes"],
            json["gennet"]["fanout"],
            json["gennet"]["network_type"],
            (json["wls"]["min_packet_size"] + json["wls"]["max_packet_size"])/2,
            json["wls"]["message_rate"],
            per_hop_delay=0.01) # pick up from kurtosis
    analysis.run()

    print(f'kurtosis: done')

@app.command()
def batch(ctx: typer.Context, batch_file: Path):
    json = _sanity_check(batch_file, [Keys.BATCH], Keys.JSON)
    runs = json[Keys.BATCH][Keys.RUNS]
    for run in runs:
        print(runs[run])
        analysis = Analysis(**runs[run])
        analysis.run()
    print(f'batch: done')

@app.command()
def shadow(ctx: typer.Context, config_file: Path):
    yaml = _sanity_check(config_file, [], Keys.YAML)
    print("shadow: done {yaml}")

@app.command()
def cli(ctx: typer.Context,
         num_nodes: int = typer.Option(4,
             help="Set the number of nodes"),
         fanout: int = typer.Option(6,
             help="Set the arity"),
         network_type: networkType = typer.Option(networkType.REGULAR.value,
             help="Set the network type"),
         msg_size: float = typer.Option(2,
             help="Set message size in KBytes"),
         msgpsec: float = typer.Option(0.083,
             help="Set message rate per second on a shard/topic"),
         gossip_msg_size: float = typer.Option(0.05,
             help="Set gossip message size in KBytes"),
         gossip_window_size: int = typer.Option(3,
             help="Set gossip history window size"),
         gossip2reply_ratio: float = typer.Option(0.01,
             help="Set the Gossip to reply ratio"),
         nodes_per_shard: int = typer.Option(10000,
             help="Set the number of nodes per shard/topic"),
         shards_per_node: int = typer.Option(3,
             help="Set the number of shards a node is part of"),
         per_hop_delay: float = typer.Option(0.1,
             help="Set the delay per hop")):

    analysis = Analysis(num_nodes, fanout, network_type,
                        msg_size, msgpsec, per_hop_delay,
                        **{"gossip_msg_size" : gossip_msg_size,
                        "gossip_window_size":gossip_window_size,
                        "gossip2reply_ratio":gossip2reply_ratio,
                        "nodes_per_shard":nodes_per_shard,
                        "shards_per_node":shards_per_node})
    analysis.run()
    print("cli: done")

if __name__ == "__main__":
    app()

"""
# general / topology
average_node_degree = 6  # has to be even
message_size = 0.002 # in MB (Mega Bytes)
self.msgphr = 5 # ona a single pubsub topic / shard

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
