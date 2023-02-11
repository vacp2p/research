# !!! THIS IS WIP (analyze the code structure at your own risk ^.^')
# the scope of this is still undefined; we want to avoid premature generalization
# - todo: separate the part on latency
# based on ../whisper_scalability/whisper.py

import matplotlib.pyplot as plt
import numpy as np
import math

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
    print("")

def latency_str(latency_users_fn, n_users, degree):
    latency =  latency_users_fn(n_users, degree)
    return load_color_fmt(latency, "For " + magnitude_fmt(n_users) + " the average latency is " + ("%.3f" % latency_users_fn(n_users, degree)) + " s")

def print_latency(latency_users):
    print(latency_str(latency_users, 100, average_node_degree))
    print(latency_str(latency_users, 100 * 100, average_node_degree))
    print(latency_str(latency_users, 100 * 100 * 100, average_node_degree))
    print("")

def num_edges_dregular(num_nodes, degree):
    # we assume and even d; d-regular graphs with both where both n and d are odd don't exist
    return num_nodes * (degree/2)

def avg_node_distance_upper_bound(n_users, degree):
    return math.log(n_users, degree)

# Assumptions
#-----------------------------------------------------------

# Users sent messages at a constant rate
# The network topology is a d-regular graph (gossipsub aims at achieving this).
#
# Goal:
# - reasonable bw and fetch time
# ~1GB per month, ~ 30 MB per day, ~1 MB per hour

average_node_degree = 6  # has to be even

message_size = 0.002 # in MB (Mega Bytes)
messages_sent_per_hour = 5

gossip_message_size = 0.00005 # 50Bytes in MB (see https://github.com/libp2p/specs/pull/413#discussion_r1018821589 )
d_lazy = 6 # gossip out degree
mcache_gossip = 3 # Number of history windows to use when emitting gossip (see https://github.com/libp2p/specs/blob/master/pubsub/gossipsub/gossipsub-v1.0.md)
avg_ratio_gossip_replys = 0.01 # -> this is a wild guess! (todo: investigate)

average_delay_per_hop = 0.1 #s

# TODO: load case for status control messages (note: this also introduces messages by currently online, but not active users.)
# TODO: spread in the latency distribution (the highest 10%ish of latencies might be too high)

# Assumption strings (general/topology)
a1 = "- A01. Message size (static): " + sizeof_fmt_kb(message_size)
a2 = "- A02. Messages sent per node per hour (static) (assuming no spam; but also no rate limiting.): " + str(messages_sent_per_hour)
a3 = "- A03. The network topology is a d-regular graph of degree (static): " + str(average_node_degree)
a4 = "- A04. Messages outside of Waku Relay are not considered, e.g. store messages."
a5 = "- A05. Messages are only sent once along an edge. (requires delays before sending)"
a6 = "- A06. Messages are sent to all d-1 neighbours as soon as receiving a message (current operation)" # Thanks @Mmenduist

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

# Case 1
def load_case1(n_users):
    return message_size * messages_sent_per_hour * n_users

def print_load_case1():
    print_header("Load case 1 (store load)")
    print_assumptions([a1, a2, a3, a4, a21])
    print_usage(load_case1)
    print("")
    print("------------------------------------------------------------")

# Case 2
def load_case2(n_users):
    return message_size * messages_sent_per_hour * num_edges_dregular(n_users, average_node_degree)

def print_load_case2():
    print_header("Load case 2 (received load per node)")
    print("")
    print_assumptions([a1, a2, a3, a4, a5, a31])
    print_usage(load_case2)
    print("")
    print("------------------------------------------------------------")

# Case 3
def load_case3(n_users):
    return message_size * messages_sent_per_hour * n_users * (average_node_degree-1)

def print_load_case3():
    print_header("Load case 3 (received load per node)")
    print_assumptions([a1, a2, a3, a4, a6, a31])
    print_usage(load_case3)
    print("")
    print("------------------------------------------------------------")


# Case 4:
def load_case4(n_users):
    messages_received_per_hour =  messages_sent_per_hour * n_users * (average_node_degree-1) # see case 3
    messages_load =  message_size * messages_received_per_hour
    num_ihave = messages_received_per_hour * d_lazy * mcache_gossip
    ihave_load  = num_ihave * gossip_message_size
    gossip_response_load  = (num_ihave * (gossip_message_size + message_size)) * avg_ratio_gossip_replys # reply load contains both an IWANT (from requester to sender), and the actual wanted message (from sender to requester)
    gossip_total = ihave_load + gossip_response_load

    return messages_load + gossip_total

def print_load_case4():
    print_header("Load case 4 (received load per node incl. gossip)")
    print_assumptions([a1, a2, a3, a4, a6, a32, a33])
    print_usage(load_case4)
    print("")
    print("------------------------------------------------------------")



# Cases average latency
#-----------------------------------------------------------

def latency_case1(n_users, degree):
    return avg_node_distance_upper_bound(n_users, degree) * average_delay_per_hop

def print_latency_case1():
    print_header("Latency case 1 :: Topology: 6-regular graph. No gossip (note: gossip would help here)")
    print_assumptions([a3, a41, a42])
    print_latency(latency_case1)
    print("")
    print("------------------------------------------------------------")


# Run cases
#-----------------------------------------------------------

# Print goals
print("")
print(bcolors.HEADER + "Waku relay theoretical model (single shard). Attempts to encode characteristics of it." + bcolors.ENDC)
print("Note: this analysis is concerned with currently active users.")
print("The total number of users of an app using Waku relay could be factor 10 to 100 higher (estimated based on @Menduist Discord checks.)")
print("")
print("" + bcolors.ENDC)

print_load_case1()
print_load_case2()
print_load_case3()
print_load_case4()
print_latency_case1()

# Plot
#-----------------------------------------------------------

def plot():
  n_users = np.logspace(2, 6, num=5)
  print(n_users)

  plt.xlim(100, 10**6)
  plt.ylim(1, 10**6)

  plt.plot(n_users, load_case1(n_users), label='case 1', linewidth=4, linestyle='dashed')
  plt.plot(n_users, load_case2(n_users), label='case 2', linewidth=4, linestyle='dashed')
  plt.plot(n_users, load_case3(n_users), label='case 3', linewidth=4, linestyle='dashed')
  plt.plot(n_users, load_case4(n_users), label='case 4', linewidth=4, linestyle='dashed')

  case1 = "Case 1. top: 6-regular;  store load"
  case2 = "Case 2. top: 6-regular;  receive load per node, send delay to reduce duplicates"
  case3 = "Case 3. top: 6-regular;  receive load per node, current operation"
  case4 = "Case 4. top: 6-regular;  receive load per node, current operation, incl. gossip"

  plt.xlabel('number of users (log)')
  plt.ylabel('mb/hour (log)')
  plt.legend([case1, case2, case3, case4], loc='upper left')
  plt.xscale('log')
  plt.yscale('log')

  plt.axhspan(0, 10, facecolor='0.2', alpha=0.2, color='blue')
  plt.axhspan(10, 30, facecolor='0.2', alpha=0.2, color='green')
  plt.axhspan(30, 100, facecolor='0.2', alpha=0.2, color='orange')
  plt.axhspan(100, 10**6, facecolor='0.2', alpha=0.2, color='red')

  # plt.show()

  figure = plt.gcf() # get current figure
  figure.set_size_inches(16, 9)
  # plt.savefig("waku_scaling_plot.svg")
  plt.savefig("waku_scaling_plot.png", dpi=300, orientation="landscape")

plot()

