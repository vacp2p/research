# !!! THIS IS WIP (analyze the code structure at your own risk ^.^')
# the scope of this is still undefined; we want to avoid premature generalization
# - todo: separate the part on latency
# based on ../whisper_scalability/whisper.py

import matplotlib.pyplot as plt
import numpy as np
import math
import typer

# Util and format functions
#-----------------------------------------------------------

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def sizeof_fmt(num):
    return "%.1f%s" % (num, "MB")

def sizeof_fmt_kb(num):
    return "%.2f%s" % (num*1024, "KB")

def magnitude_fmt(num):
    for x in ['','k','m']:
        if num < 1000:
            return "%2d%s" % (num, x)
        num /= 1000

# Color format based on daily bandwidth usage
# <10mb/d = good, <30mb/d ok, <100mb/d bad, 100mb/d+ fail.
def load_color_prefix(load):
    if load < (10):
        color_level = bcolors.OKBLUE
    elif load < (30):
        color_level = bcolors.OKGREEN
    elif load < (100):
        color_level = bcolors.WARNING
    else:
        color_level = bcolors.FAIL
    return color_level

def load_color_fmt(load, string):
    return load_color_prefix(load) + string + bcolors.ENDC

def print_header(string):
    print(bcolors.HEADER + string + bcolors.ENDC + "\n")

def print_assumptions(xs):
    print("Assumptions/Simplifications:")
    for x in xs:
        print(x)
    print("")

def usage_str(load_users_fn, n_users):
    load = load_users_fn(n_users)
    return load_color_fmt(load, "For " + magnitude_fmt(n_users) + " users, receiving bandwidth is " + sizeof_fmt(load_users_fn(n_users)) + "/hour")

def print_usage(load_users):
    print(usage_str(load_users, 100))
    print(usage_str(load_users, 100 * 100))
    print(usage_str(load_users, 100 * 100 * 100))

def latency_str(latency_users_fn, n_users, degree):
    latency =  latency_users_fn(n_users, degree)
    return load_color_fmt(latency, "For " + magnitude_fmt(n_users) + " the average latency is " + ("%.3f" % latency_users_fn(n_users, degree)) + " s")

def print_latency(latency_users):
    print(latency_str(latency_users, 100, average_node_degree))
    print(latency_str(latency_users, 100 * 100, average_node_degree))
    print(latency_str(latency_users, 100 * 100 * 100, average_node_degree))

def num_edges_dregular(num_nodes, degree):
    # we assume and even d; d-regular graphs with both where both n and d are odd don't exist
    return num_nodes * (degree/2)

def avg_node_distance_upper_bound(n_users, degree):
    return math.log(n_users, degree)

# Assumptions
#-----------------------------------------------------------

# Users sent messages at a constant rate
# The network topology is a d-regular graph (gossipsub aims at achieving this).

# general / topology
average_node_degree = 6  # has to be even
message_size = 0.002 # in MB (Mega Bytes)
messages_sent_per_hour = 5 # ona a single pubsub topic / shard

# gossip
gossip_message_size = 0.00005 # 50Bytes in MB (see https://github.com/libp2p/specs/pull/413#discussion_r1018821589 )
d_lazy = 6 # gossip out degree
mcache_gossip = 3 # Number of history windows to use when emitting gossip (see https://github.com/libp2p/specs/blob/master/pubsub/gossipsub/gossipsub-v1.0.md)
avg_ratio_gossip_replys = 0.01 # -> this is a wild guess! (todo: investigate)

# multi shard
avg_nodes_per_shard = 10000 # average number of nodes that a part of a single shard
avg_shards_per_node = 3    # average number of shards a given node is part of

# latency
average_delay_per_hop = 0.1 #s

# TODO: load case for status control messages (note: this also introduces messages by currently online, but not active users.)
# TODO: spread in the latency distribution (the highest 10%ish of latencies might be too high)

# Assumption strings (general/topology)
a1  = "- A01. Message size (static): " + sizeof_fmt_kb(message_size)
a2  = "- A02. Messages sent per node per hour (static) (assuming no spam; but also no rate limiting.): " + str(messages_sent_per_hour)
a3  = "- A03. The network topology is a d-regular graph of degree (static): " + str(average_node_degree)
a4  = "- A04. Messages outside of Waku Relay are not considered, e.g. store messages."
a5  = "- A05. Messages are only sent once along an edge. (requires delays before sending)"
a6  = "- A06. Messages are sent to all d-1 neighbours as soon as receiving a message (current operation)" # Thanks @Mmenduist
a7  = "- A07. Single shard (i.e. single pubsub mesh)"
a8  = "- A08. Multiple shards; mapping of content topic (multicast group) to shard is 1 to 1"
a9  = "- A09. Max number of nodes per shard (static) " + str(avg_nodes_per_shard)
a10 = "- A10. Number of shards a given node is part of (static) " + str(avg_shards_per_node)
a11 = "- A11. Number of nodes in the network is variable.\n\
       These nodes are distributed evenly over " + str(avg_shards_per_node) + " shards.\n\
       Once all of these shards have " + str(avg_nodes_per_shard) + " nodes, new shards are spawned.\n\
       These new shards have no influcene on this model, because the nodes we look at are not part of these new shards."
a12 = "- A12. Including 1:1 chat. Messages sent to a given user are sent into a 1:1 shard associated with that user's node.\n\
        Effectively, 1:1 chat adds a receive load corresponding to one additional shard a given node has to be part of."
a13 = "- A13. 1:1 chat messages sent per node per hour (static): " + str(messages_sent_per_hour) # could introduce a separate variable here
a14 = "- A14. 1:1 chat shards are filled one by one (not evenly distributed over the shards).\n\
        This acts as an upper bound and overestimates the 1:1 load for lower node counts."
a15 = "- A15. Naive light node. Requests all messages in shards that have (large) 1:1 mapped multicast groups the light node is interested in."


# Assumption strings (store)
a21 = "- A21. Store nodes do not store duplicate messages."

# Assumption strings (gossip)
a31 = "- A21. Gossip is not considered."
a32 = "- A32. Gossip message size (IHAVE/IWANT) (static):" + sizeof_fmt_kb(gossip_message_size)
a33 = "- A33. Ratio of IHAVEs followed-up by an IWANT (incl. the actual requested message):" + str(avg_ratio_gossip_replys)

# Assumption strings (delay)
a41 = "- A41. Delay is calculated based on an upper bound of the expected distance."
a42 = "- A42. Average delay per hop (static): " + str(average_delay_per_hop) + "s."


# Cases Load Per Node
#-----------------------------------------------------------

# Case 1 :: singe shard, unique messages, store
def load_case1(n_users):
    return message_size * messages_sent_per_hour * n_users

def print_load_case1():
    print("")
    print_header("Load case 1 (store load; corresponds to received load per naive light node)")
    print_assumptions([a1, a2, a3, a4, a7, a21])
    print_usage(load_case1)
    print("")
    print("------------------------------------------------------------")

# Case 2 :: single shard, (n*d)/2 messages
def load_case2(n_users):
    return message_size * messages_sent_per_hour * num_edges_dregular(n_users, average_node_degree)

def print_load_case2():
    print("")
    print_header("Load case 2 (received load per node)")
    print_assumptions([a1, a2, a3, a4, a5, a7, a31])
    print_usage(load_case2)
    print("")
    print("------------------------------------------------------------")

# Case 3 :: single shard n*(d-1) messages
def load_case3(n_users):
    return message_size * messages_sent_per_hour * n_users * (average_node_degree-1)

def print_load_case3():
    print("")
    print_header("Load case 3 (received load per node)")
    print_assumptions([a1, a2, a3, a4, a6, a7, a31])
    print_usage(load_case3)
    print("")
    print("------------------------------------------------------------")


# Case 4:single shard n*(d-1) messages, gossip
def load_case4(n_users):
    messages_received_per_hour =  messages_sent_per_hour * n_users * (average_node_degree-1) # see case 3
    messages_load =  message_size * messages_received_per_hour
    num_ihave = messages_received_per_hour * d_lazy * mcache_gossip
    ihave_load  = num_ihave * gossip_message_size
    gossip_response_load  = (num_ihave * (gossip_message_size + message_size)) * avg_ratio_gossip_replys # reply load contains both an IWANT (from requester to sender), and the actual wanted message (from sender to requester)
    gossip_total = ihave_load + gossip_response_load

    return messages_load + gossip_total

def print_load_case4():
    print("")
    print_header("Load case 4 (received load per node incl. gossip)")
    print_assumptions([a1, a2, a3, a4, a6, a7, a32, a33])
    print_usage(load_case4)
    print("")
    print("------------------------------------------------------------")

# sharding case 1: multi shard, n*(d-1) messages, gossip
def load_sharding_case1(n_users):
    load_per_node_per_shard = load_case4(np.minimum(n_users/3, avg_nodes_per_shard))
    return avg_shards_per_node * load_per_node_per_shard

def print_load_sharding_case1():
    print("")
    print_header("load sharding case 1 (received load per node incl. gossip)")
    print_assumptions([a1, a2, a3, a4, a6, a8, a9, a10, a11, a32, a33])
    print_usage(load_sharding_case1)
    print("")
    print("------------------------------------------------------------")

# sharding case 2: multi shard, n*(d-1) messages, gossip, 1:1 chat
def load_sharding_case2(n_users):
    load_per_node_per_shard = load_case4(np.minimum(n_users/3, avg_nodes_per_shard))
    load_per_node_1to1_shard = load_case4(np.minimum(n_users, avg_nodes_per_shard))
    return (avg_shards_per_node * load_per_node_per_shard) + load_per_node_1to1_shard

def print_load_sharding_case2():
    print("")
    print_header("load sharding case 2 (received load per node incl. gossip and 1:1 chat)")
    print_assumptions([a1, a2, a3, a4, a6, a8, a9, a10, a11, a12, a13, a14, a32, a33])
    print_usage(load_sharding_case2)
    print("")
    print("------------------------------------------------------------")

# sharding case 3: multi shard, naive light node
def load_sharding_case3(n_users):
    load_per_node_per_shard = load_case1(np.minimum(n_users/3, avg_nodes_per_shard))
    return avg_shards_per_node * load_per_node_per_shard

def print_load_sharding_case3():
    print("")
    print_header("load sharding case 3 (received load naive light node.)")
    print_assumptions([a1, a2, a3, a4, a6, a8, a9, a10, a15, a32, a33])
    print_usage(load_sharding_case3)
    print("")
    print("------------------------------------------------------------")




# Cases average latency
#-----------------------------------------------------------

def latency_case1(n_users, degree):
    return avg_node_distance_upper_bound(n_users, degree) * average_delay_per_hop

def print_latency_case1():
    print("")
    print_header("Latency case 1 :: Topology: 6-regular graph. No gossip (note: gossip would help here)")
    print_assumptions([a3, a41, a42])
    print_latency(latency_case1)
    print("")
    print("------------------------------------------------------------")


# Run cases
#-----------------------------------------------------------

# Print goals
print("")
print(bcolors.HEADER + "Waku relay theoretical model results (single shard and multi shard scenarios)." + bcolors.ENDC)

print_load_case1()
print_load_case2()
print_load_case3()
print_load_case4()

print_load_sharding_case1()
print_load_sharding_case2()
print_load_sharding_case3()

print_latency_case1()

# Plot
#-----------------------------------------------------------

def plot_load():
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

  # plt.show()

  figure = plt.gcf() # get current figure
  figure.set_size_inches(16, 9)
  # plt.savefig("waku_scaling_plot.svg")
  plt.savefig("waku_scaling_single_shard_plot.png", dpi=300, orientation="landscape")

def plot_load_sharding():
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

  # plt.show()

  figure = plt.gcf() # get current figure
  figure.set_size_inches(16, 9)
  # plt.savefig("waku_scaling_plot.svg")
  plt.savefig("waku_scaling_multi_shard_plot.png", dpi=300, orientation="landscape")


def _config_file_callback(ctx: typer.Context, param: typer.CallbackParam, cfile: str):
    if cfile:
        typer.echo(f"Loading config file: {os.path.basename(cfile)}")
        ctx.default_map = ctx.default_map or {}  # Init the default map
        try:
            with open(cfile, 'r') as f:  # Load config file
                conf = json.load(f)
                if "network" not in conf:
                    print(
                        f"Network configuration not found in {cfile}. Skipping the analysis.")
                    sys.exit(0)
            ctx.default_map.update(conf["network"])  # Merge config and default_map
        except Exception as ex:
            raise typer.BadParameter(str(ex))
    return cfile

def main(ctx: typer.Context,
         num_nodes: int = typer.Option(4,
             help="Set the number of nodes"),
         fanout: int = typer.Option(6,
             help="Set the arity"),
         network_type: networkType = typer.Option(networkType.REGULAR.value,
             help="Set the network type"),
         config_file: str = typer.Option("", callback=_config_file_callback, is_eager=True,
             help="Set the input config file (JSON)")):
    plot_load()
    plot_load_sharding()
