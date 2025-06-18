# Assumptions
# -----------------------------------------------------------

# Users sent messages at a constant rate
# The network topology is a d-regular graph (gossipsub aims at achieving this).

# general / topology
from utils import sizeof_fmt_kb


average_node_degree = 6  # has to be even
message_size = 0.002  # in MB (Mega Bytes)
messages_sent_per_hour = 5  # ona a single pubsub topic / shard

# Here we've chosen assumptions that keep the average message size the same.
# (big_message_size * ratio_of_big_messages) + (small_message_size * (1-ratio_of_big_messages)) == message_size
small_message_size = 0.001
big_message_size = 0.006  # in MB (Mega Bytes)
ratio_of_big_messages = .2 # ratio of number of big messages / number of other messages

idontwant_too_late = 0.6 # ratio of number of big messages that are sent to a node after that node has received them

# gossip
gossip_message_size = (
    0.00005  # 50Bytes in MB (see https://github.com/libp2p/specs/pull/413#discussion_r1018821589 )
)
idontwant_message_size = 0.00005
d_lazy = 6  # gossip out degree
mcache_gossip = 3  # Number of history windows to use when emitting gossip (see https://github.com/libp2p/specs/blob/master/pubsub/gossipsub/gossipsub-v1.0.md)
avg_ratio_gossip_replys = 0.01  # -> this is a wild guess! (todo: investigate)

# multi shard
avg_nodes_per_shard = 10000  # average number of nodes that a part of a single shard
avg_shards_per_node = 3  # average number of shards a given node is part of

# latency
average_delay_per_hop = 0.1  # s

# TODO: load case for status control messages (note: this also introduces messages by currently online, but not active users.)
# TODO: spread in the latency distribution (the highest 10%ish of latencies might be too high)

# Assumption strings (general/topology)
a1  = "- A01. Message size (static): " + sizeof_fmt_kb(message_size)
a2  = "- A02. Messages sent per node per hour (static) (assuming no spam; but also no rate limiting.): " + str(messages_sent_per_hour)
a3  = "- A03. The network topology is a d-regular graph of degree (static): " + str(average_node_degree)
a16 = "- A16. There exists at most one peer edge between any two nodes."
a17 = "- A17. The peer network is connected."
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
a34 = "- A34. Gossip message size for IDONTWANT (static): " + sizeof_fmt_kb(idontwant_message_size)
a35 = "- A35. Ratio of messages that are big enough to trigger a IDONTWANT response: " + str(ratio_of_big_messages)
a36 = "- A36. Ratio of big messages that are avoided due to IDONTWANT: " + str(1/idontwant_too_late)
a37 = "- A37. Size of messages large enough to trigger IDONTWANT (static): " + sizeof_fmt_kb(big_message_size)

# Assumption strings (delay)
a41 = "- A41. Delay is calculated based on an upper bound of the expected distance."
a42 = "- A42. Average delay per hop (static): " + str(average_delay_per_hop) + "s."