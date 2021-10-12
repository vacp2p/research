# Waku v1 vs Waku v2: bandwidth comparison

## Background

The [original plan](https://vac.dev/waku-v2-plan) for Waku v2 suggested theoretical improvements in resource usage over Waku v1, mainly as a result of the improved amplification factors provided by GossipSub. In its turn, [Waku v1 proposed improvements](https://vac.dev/fixing-whisper-with-waku) over its predecessor, Whisper.

Given that Waku v2 is aimed at resource restricted environments, we are specifically interested in its scalability and resource usage characteristics. However, the theoretical performance improvements of Waku v2 over Waku v1, has never been properly benchmarked and tested.

A full performance evaluation of Waku v2 would require significant planning and resources, if it were to simulate "real world" conditions faithfully and measure bandwidth and resource usage across different network connections, robustness against attacks/losses, message latencies, etc. (There already exists a fairly comprehensive [evaluation of GossipSub v1.1](https://research.protocol.ai/publications/gossipsub-v1.1-evaluation-report/vyzovitis2020.pdf), on which `11/WAKU2-RELAY` is based.)

As a more realistic starting point, this document contains a limited and local comparison of the _bandwidth_ profile (only) between Waku v1 and Waku v2. It reuses and adapts existing network simulations for [Waku v1](https://github.com/status-im/nim-waku/blob/master/waku/v1/node/quicksim.nim) and [Waku v2](https://github.com/status-im/nim-waku/blob/master/waku/v2/node/quicksim2.nim) and compares bandwidth usage for similar message propagation scenarios.

## Theoretical improvements in Waku v2

Messages are propagated in Waku v1 using [flood routing](https://en.wikipedia.org/wiki/Flooding_(computer_networking)). This means that every peer will forward every new incoming message to all its connected peers (except the one it received the message from). This necessarily leads to unnecessary duplication (termed _amplification factor_), wasting bandwidth and resources. What's more, we expect this effect to worsen the larger the network becomes, as each _connection_ will receive a copy of each message, rather than a single copy per peer.

Message routing in Waku v2 follows the `libp2p` _GossipSub_ protocol, which lowers amplification factors by only sending full message contents to a subset of connected peers. As a Waku v2 network grows, each peer will limit its number of full-message ("mesh") peerings - `libp2p` suggests a maximum of `12` such connections per peer. This allows much better scalability than a flood-routed network. From time to time, a Waku v2 peer will send metadata about the messages it has seen to other peers ("gossip" peers).

See [this explainer](https://hackmd.io/@vac/main/%2FYYlZYBCURFyO_ZG1EiteWg#11WAKU2-RELAY-gossipsub) for a more detailed discussion.

## Methodology

The results below contain only some scenarios that provide an interesting contrast between Waku v1 and Waku v2. For example, [star network topologies](https://www.techopedia.com/definition/13335/star-topology#:~:text=Star%20topology%20is%20a%20network,known%20as%20a%20star%20network.) do not show a substantial difference between Waku v1 and Waku v2. This is because each peer relies on a single connection to the central node for every message, which barely requires any routing: each connection receives a copy of every message for both Waku v1 and Waku v2. Hybrid topologies similarly show only a difference between Waku v1 and Waku v2 for network segments with [mesh-like connections](https://en.wikipedia.org/wiki/Mesh_networking), where routing decisions need to be made.

For this reason, the following approach applies to all scenarios:
1. Simulations are run **locally**. This limits the size of possible scenarios due to local resource constraints, but is a way to quickly get an approximate comparison.
2. Nodes are treated as a **blackbox** for which we only measure bandwidth, using an external bandwidth monitoring tool. In other words, we do not consider differences in the size of the envelope (for v1) or the message (for v2).
3. Messages are published at a rate of **50 new messages per second** to each network, except where explicitly stated otherwise.
4. Each message propagated in the network carries **8 bytes** of random payload, which is **encrypted**. The same symmetric key cryptographic algorithm (with the same keys) are used in both Waku v1 and v2.
5. Traffic in each network is **generated from 10 nodes** (randomly-selected) and published in a round-robin fashion to **10 topics** (content topics for Waku v2). In practice, we found no significant difference in _average_ bandwidth usage when tweaking these two parameters (the number of traffic generating nodes and the number of topics).
6. Peers are connected in a decentralized **full mesh topology**, i.e. each peer is connected to every other peer in the network. Waku v1 is expected to flood all messages across all existing connections. Waku v2 gossipsub will GRAFT some of these connections for full-message peerings, with the rest being gossip-only peerings.
7. After running each scenario, we **verify that messages propagated to all peers** (comparing the number of published messages to the metrics logged by each peer).

For Waku v1, nodes are configured as "full" nodes (i.e. with full bloom filter), while Waku v2 nodes are `relay` nodes, all subscribing and publishing to the same PubSub topic.

## Network size comparison

### Scenario 1: 10 nodes

Let's start with a small network of 10 nodes only and see how Waku v1 bandwidth usage compares to that of Waku v2. At this small scale we don't expect to see improved bandwidth usage in Waku v2 over Waku v1, since all connections, for both Waku v1 and Waku v2, will be full-message connections. The number of connections is low enough that Waku v2 nodes will likely GRAFT all connections to full-message peerings, essentially flooding every message on every connection in a similar fashion to Waku v1. If our expectations are confirmed, it helps validate our methodology, showing that it gives more or less equivalent results between Waku v1 and Waku v2 networks.

![](https://i.imgur.com/qffZkrn.png)

Sure enough, the figure shows that in this small-scale setup, Waku v1 actually has a lower per-peer bandwidth usage than Waku v2. One reason for this may be the larger overall proportion of control messages in a gossipsub-routed network such as Waku v2. These play a larger role when the total network traffic is comparatively low, as in this scenario. Also note that the average bandwidth remains more or less constant as long as the rate of published messages remains stable.

### Scenario 2: 30 nodes

Now, let's run the same scenario for a larger network of highly-connected nodes, this time consisting of 30 nodes. At this point, the Waku v2 nodes will start pruning some connections to limit the number of full-message peerings (to a maximum of `12`), while the Waku v1 nodes will continue flooding messages to all connected peers. We therefore expect to see a somewhat improved bandwidth usage in Waku v2 over Waku v1.

![](https://i.imgur.com/WpsHl3o.png)

Bandwidth usage in Waku v2 has increased only slightly from the smaller network of 10 nodes (hovering between 2000 and 3000 kbps). This is because there are only a few more full-message peerings than before. Compare this to the much higher increase in bandwidth usage for Waku v1, which now requires more than 4000 kbps on average.


### Scenario 3: 50 nodes

For an even larger network of 50 highly connected nodes, the divergence between Waku v1 and Waku v2 is even larger. The following figure shows comparative average bandwidth usage for a throughput of 50 messages per second.

![](https://i.imgur.com/xpMQiwC.png)

Average bandwidth usage (for the same message rate) has remained roughly the same for Waku v2, indicating that the number of full-message peerings per node has not increased.

### Scenario 4: 85 nodes

We already see a clear trend in the bandwidth comparisons above, so let's confirm by running the test once more for a network of 85 nodes. Due to local resource constraints, the effective throughput for Waku v1 falls to below 50 messages per second, so the v1 results below have been normalized and are therefore approximate. The local Waku v2 simulation maintains the message throughput rate without any problems.

![](https://i.imgur.com/3W9E7l8.png)

### Scenario 5: 150 nodes

Finally, we simulate message propagation in a network of 150 nodes. Due to local resource constraints, we run this simulation at a lower rate - 35 messages per second - and for a shorter amount of time. 

![](https://i.imgur.com/KW48ufF.png)

Notice how the Waku v1 bandwidth usage is now more than 10 times worse than that of Waku v2. This is to be expected, as each Waku v1 node will try to flood each new message to 149 other peers, while the Waku v2 nodes limit their full-message peerings to no more than 12.

### Scenarios 1 - 5: Analysis

Let's summarize average bandwidth growth against network growth for a constant message propagation rate. Since we are particularly interested in how Waku v1 compares to Waku v2 in terms of bandwidth usage, the results are normalised to the Waku v2 average bandwidth usage for each network size.

![](https://i.imgur.com/cX6jwQr.png)

Extrapolation is a dangerous game, but it's safe to deduce that the divergence will only grow for even larger network topologies. Although control signalling contributes more towards overall bandwidth for Waku v2 networks, this effect becomes less noticeable for larger networks. For network segments with more than ~18 densely connected nodes, the advantage of using Waku v2 above Waku v1 becomes clear.

## Network traffic comparison

The analysis above controls the average message rate while network size grows. In reality, however, active users (and therefore message rates) are likely to grow in conjunction with the network. This will have an effect on bandwidth for both Waku v1 and Waku v2, though not in equal measure. Consider the impact of an increasing rate of messages in a network of constant size:

![](https://i.imgur.com/B5wpNy0.png)

The _rate_ of increase in bandwidth for Waku v2 is slower than that for Waku v1 for a corresponding increase in message propagation rate. In fact, for a network of 30 densely-connected nodes, if the message propagation rate increases by 1 per second, Waku v1 requires an increased average bandwidth of almost 70kbps at each node. A similar traffic increase in Waku v2 requires on average 40kbps more bandwidth per peer, just over half that of Waku v1.

## Conclusions

- Waku v2 scales significantly better than Waku v1 in terms of average bandwidth usage, especially for densely connected networks.
- E.g. for a network consisting of **150** or more densely connected nodes, Waku v2 provides more than **10x** better average bandwidth usage rates than Waku v1.
- As the network continues to scale, both in absolute terms (number of nodes) and in network traffic (message rates) the disparity between Waku v2 and Waku v1 becomes even larger.

## References

- [Evaluation of GossipSub v1.1](https://research.protocol.ai/publications/gossipsub-v1.1-evaluation-report/vyzovitis2020.pdf)
- [Fixing Whisper with Waku](https://vac.dev/fixing-whisper-with-waku)
- [GossipSub vs flood routing](https://hackmd.io/@vac/main/%2FYYlZYBCURFyO_ZG1EiteWg#11WAKU2-RELAY-gossipsub)
- [Network topologies: star](https://www.techopedia.com/definition/13335/star-topology#:~:text=Star%20topology%20is%20a%20network,known%20as%20a%20star%20network.)
- [Network topologies: mesh](https://en.wikipedia.org/wiki/Mesh_networking)
- [Waku v2 original plan](https://vac.dev/waku-v2-plan)
