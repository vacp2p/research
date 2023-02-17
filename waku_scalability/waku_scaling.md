# Waku Scaling

> *Note:* This analysis (and the underlying model) is concerned with currently *active* users.
The total number of users of an app's multicast group using Waku relay could be factor 10 to 100 higher
(estimated based on @Menduist Discord checks).

> *Note*: The analysis focus on ingress traffic per node.
For Waku relay nodes, the egress traffic is (almost exactly) the same as this ingress traffic.
So, to consider both ingress and egress load on relay nodes, we need to multiply results by 2.

> *Note*: In this analysis we assume nodes to be part of a protocol stack that has an app layer (e.g. Status Desktop), which originates messages.
We simply say: "a node sends messages", even though it is not the gossipsub layer itself, but the app layer using the gossipsub node.



*Many thanks to @Menduist for the helpful discussions, input, and feedback.*

## Analysis

We first look at the scaling properties of a single pubsub topic, which corresponds to a single shard.
This is relevant for the scaling the number of nodes within a single multicast group,
and by extension the number of active users in a single Status Community.
We also look at scaling properties of a Waku network as a whole, including sharing.

### Single Shard

The load on nodes scales linearly with the number of nodes in a shard.
So, there is a limit of nodes (which we currently see at around 10k nodes) that can feasibly be active in a single shard.
The degree `d` of the assumed regular topology graph adds to the scaling factor.
While this is asymptotically irrelevant, it has a significant practical impact.

* The (constant) degree `d` limits ingress load growth per node to $O(n)$.
* A higher `d` adds load but reduces latency.
* Unbound `d` yields best latency but infeasible load.
* Gossip reduces latency at the cost of load.

#### Topology and Duplicate Messages

We assume a `d`-regular graph topology.
The topology effects the number of duplicate message transmissions, as well as the latency.

Duplicate messages cause significant additional load.
Gossipsub reduces the number of duplicate messages by

* not sending a message back to the sender
* not relaying a message if it has already been relayed (using a seen cache)

while this is very helpful, there are duplicate messages that cannot be avoided with these techniques.
Assume node A is connected to B and C, and B and C are connected to D.
A relays a message to both B and C, both of which will relay the message to D, so D receives the message twice.
With local routing decisions (and no additional control messages),
the number of edges in the graph is a lower bound for the number of hop-to-hop transmissions of a single message.
A d-regular graph has $(n * d)/2$ edges (proof [here](https://proofwiki.org/wiki/Number_of_Edges_of_Regular_Graph)).

However, there is another practical problem (thanks @Menduist for pointing this out):
Two nodes that both just got the message might relay the message to each other before either of them registers the receipt.

So, practically a message can go twice over the same edge.
Each node actually sends the message to `d-1` peers, which leads to a duplication factor of $n * (d-1)$ hop-to-hop transmissions per message.
Waiting before transmitting can lower this bound to somewhere between $(n * d)/2$ and $n * (d-1)$.

#### gossip

Gossip is sent once per heartbeat interval (1s) in the form of an IHAVE message, indicating a node has a certain message.
IHAVEs regarding messages are sent if the respective message is in one of the last `mcache_gossip = 3` windows.
The window length corresponds to the heartbeat time.
So, effectively, each relayed message triggers `mcache_gossip = 3` many IHAVE messages.
Each IHAVE is transmitted to `d_lazy = 6` many peers.
So each relayed message triggers `3*6 = 18` IHAVE messages; [estimation of the size of an IHAVE](https://github.com/libp2p/specs/pull/413#discussion_r1018821589).
If a receiving node actually wants the message, it sends an IWANT, and receives the actual message.
In the model, we introduce `avg_ratio_gossip_replys` as the ratio of IHAVEs that are followed by an IWANT.
The follow-up causes an additional load of: `(gossip_message_size + message_size) * avg_ratio_gossip_replys`


### Multi Shard

Sharding allows to bind the maximum load a node/user is exposed to.
Instead of scaling with the number of nodes in the network, the load scales with the number of nodes in all shards the node is part of.

### Latency

In our first analysis based on an upper bound of inter-node distance in d-regular graphs, latency properties are good (see results below).
However, this needs further investigation, especially in regards to worst case and the upper percentile etc...
Future work comprises a latency distribution (most likely, we will focus on other parts for the scaling MVP).


## Model Calculations

(generated with `./waku_scaling.py`)

Load case 1 (store load; corresponds to received load per naive light node)

Assumptions/Simplifications:
- A01. Message size (static): 2.05KB
- A02. Messages sent per node per hour (static) (assuming no spam; but also no rate limiting.): 5
- A03. The network topology is a d-regular graph of degree (static): 6
- A04. Messages outside of Waku Relay are not considered, e.g. store messages.
- A07. Single shard (i.e. single pubsub mesh)
- A21. Store nodes do not store duplicate messages.

For 100 users, receiving bandwidth is 1.0MB/hour
For 10k users, receiving bandwidth is 100.0MB/hour

------------------------------------------------------------

Load case 2 (received load per node)

Assumptions/Simplifications:
- A01. Message size (static): 2.05KB
- A02. Messages sent per node per hour (static) (assuming no spam; but also no rate limiting.): 5
- A03. The network topology is a d-regular graph of degree (static): 6
- A04. Messages outside of Waku Relay are not considered, e.g. store messages.
- A05. Messages are only sent once along an edge. (requires delays before sending)
- A07. Single shard (i.e. single pubsub mesh)
- A21. Gossip is not considered.

For 100 users, receiving bandwidth is 3.0MB/hour
For 10k users, receiving bandwidth is 300.0MB/hour

------------------------------------------------------------

Load case 3 (received load per node)

Assumptions/Simplifications:
- A01. Message size (static): 2.05KB
- A02. Messages sent per node per hour (static) (assuming no spam; but also no rate limiting.): 5
- A03. The network topology is a d-regular graph of degree (static): 6
- A04. Messages outside of Waku Relay are not considered, e.g. store messages.
- A06. Messages are sent to all d-1 neighbours as soon as receiving a message (current operation)
- A07. Single shard (i.e. single pubsub mesh)
- A21. Gossip is not considered.

For 100 users, receiving bandwidth is 5.0MB/hour
For 10k users, receiving bandwidth is 500.0MB/hour

------------------------------------------------------------

Load case 4 (received load per node incl. gossip)

Assumptions/Simplifications:
- A01. Message size (static): 2.05KB
- A02. Messages sent per node per hour (static) (assuming no spam; but also no rate limiting.): 5
- A03. The network topology is a d-regular graph of degree (static): 6
- A04. Messages outside of Waku Relay are not considered, e.g. store messages.
- A06. Messages are sent to all d-1 neighbours as soon as receiving a message (current operation)
- A07. Single shard (i.e. single pubsub mesh)
- A32. Gossip message size (IHAVE/IWANT) (static):0.05KB
- A33. Ratio of IHAVEs followed-up by an IWANT (incl. the actual requested message):0.01

For 100 users, receiving bandwidth is 8.2MB/hour
For 10k users, receiving bandwidth is 817.2MB/hour

------------------------------------------------------------

load sharding case 1 (received load per node incl. gossip)

Assumptions/Simplifications:
- A01. Message size (static): 2.05KB
- A02. Messages sent per node per hour (static) (assuming no spam; but also no rate limiting.): 5
- A03. The network topology is a d-regular graph of degree (static): 6
- A04. Messages outside of Waku Relay are not considered, e.g. store messages.
- A06. Messages are sent to all d-1 neighbours as soon as receiving a message (current operation)
- A08. Multiple shards; mapping of content topic (multicast group) to shard is 1 to 1
- A09. Max number of nodes per shard (static) 10000
- A10. Number of shards a given node is part of (static) 3
- A11. Number of nodes in the network is variable.
       These nodes are distributed evenly over 3 shards.
       Once all of these shards have 10000 nodes, new shards are spawned.
       These new shards have no influcene on this model, because the nodes we look at are not part of these new shards.
- A32. Gossip message size (IHAVE/IWANT) (static):0.05KB
- A33. Ratio of IHAVEs followed-up by an IWANT (incl. the actual requested message):0.01

For 100 users, receiving bandwidth is 8.2MB/hour
For 10k users, receiving bandwidth is 817.3MB/hour
For  1m users, receiving bandwidth is 2451.8MB/hour

------------------------------------------------------------

load sharding case 2 (received load per node incl. gossip and 1:1 chat)

Assumptions/Simplifications:
- A01. Message size (static): 2.05KB
- A02. Messages sent per node per hour (static) (assuming no spam; but also no rate limiting.): 5
- A03. The network topology is a d-regular graph of degree (static): 6
- A04. Messages outside of Waku Relay are not considered, e.g. store messages.
- A06. Messages are sent to all d-1 neighbours as soon as receiving a message (current operation)
- A08. Multiple shards; mapping of content topic (multicast group) to shard is 1 to 1
- A09. Max number of nodes per shard (static) 10000
- A10. Number of shards a given node is part of (static) 3
- A11. Number of nodes in the network is variable.
       These nodes are distributed evenly over 3 shards.
       Once all of these shards have 10000 nodes, new shards are spawned.
       These new shards have no influcene on this model, because the nodes we look at are not part of these new shards.
- A12. Including 1:1 chat. Messages sent to a given user are sent into a 1:1 shard associated with that user's node.
        Effectively, 1:1 chat adds a receive load corresponding to one additional shard a given node has to be part of.
- A13. 1:1 chat messages sent per node per hour (static): 5
- A14. 1:1 chat shards are filled one by one (not evenly distributed over the shards).
        This acts as an upper bound and overestimates the 1:1 load for lower node counts.
- A32. Gossip message size (IHAVE/IWANT) (static):0.05KB
- A33. Ratio of IHAVEs followed-up by an IWANT (incl. the actual requested message):0.01

For 100 users, receiving bandwidth is 16.3MB/hour
For 10k users, receiving bandwidth is 1634.5MB/hour
For  1m users, receiving bandwidth is 3269.0MB/hour

------------------------------------------------------------

load sharding case 3 (received load naive light node.)

Assumptions/Simplifications:
- A01. Message size (static): 2.05KB
- A02. Messages sent per node per hour (static) (assuming no spam; but also no rate limiting.): 5
- A03. The network topology is a d-regular graph of degree (static): 6
- A04. Messages outside of Waku Relay are not considered, e.g. store messages.
- A06. Messages are sent to all d-1 neighbours as soon as receiving a message (current operation)
- A08. Multiple shards; mapping of content topic (multicast group) to shard is 1 to 1
- A09. Max number of nodes per shard (static) 10000
- A10. Number of shards a given node is part of (static) 3
- A15. Naive light node. Requests all messages in shards that have (large) 1:1 mapped multicast groups the light node is interested in.
- A32. Gossip message size (IHAVE/IWANT) (static):0.05KB
- A33. Ratio of IHAVEs followed-up by an IWANT (incl. the actual requested message):0.01

For 100 users, receiving bandwidth is 1.0MB/hour
For 10k users, receiving bandwidth is 100.0MB/hour
For  1m users, receiving bandwidth is 300.0MB/hour

------------------------------------------------------------

Latency case 1 :: Topology: 6-regular graph. No gossip (note: gossip would help here)

Assumptions/Simplifications:
- A03. The network topology is a d-regular graph of degree (static): 6
- A41. Delay is calculated based on an upper bound of the expected distance.
- A42. Average delay per hop (static): 0.1s.

For 100 the average latency is 0.257 s
For 10k the average latency is 0.514 s (max with sharding)
For  1m the average latency is 0.771 s (even in a single shard)

------------------------------------------------------------

## vs old model

> We assume a node is not relaying messages, but only sending

This is useful for establishing a lower bound independent of network topology,
but underestimates the load by a factor (which is piratically relevant).
It ignores duplicate receives.

This is why we switch to
`messages_sent_per_day` instead of assuming a number of received messages.
The number of messages received depends on the topology.

## todo

* add case:
  - load: Status control messages
  - load: light node with selective requests

## Future Work

* new case class: peers per node (various cases)
    - this matters because too many peers -> too many connections
* generalize from averages to distributions (e.g. multicast group sizes, latency, ...)
* distributed store

