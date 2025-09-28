from abc import ABC, abstractmethod
import io
import math
from typing import Any, Callable, List
import numpy as np
from pydantic import BaseModel, Field, PositiveInt

from assumptions import (
    a1,
    a2,
    a3,
    a4,
    a5,
    a6,
    a7,
    a8,
    a9,
    a10,
    a11,
    a12,
    a13,
    a14,
    a15,
    a16,
    a17,
    a21,
    a31,
    a32,
    a33,
    a41,
    a42,
    a34,
    a35,
    a36,
    a37,
)

from assumptions import (
    message_size,
    messages_sent_per_hour,
    average_node_degree,
    d_lazy,
    mcache_gossip,
    gossip_message_size,
    avg_ratio_gossip_replys,
    avg_nodes_per_shard,
    avg_shards_per_node,
    average_delay_per_hop,
    ratio_of_big_messages,
    idontwant_message_size,
    big_message_size,
    small_message_size,
    idontwant_too_late,
)

from utils import load_color_fmt, magnitude_fmt, get_header, sizeof_fmt


def get_assumptions_str(xs) -> str:
    with io.StringIO() as builder:
        builder.write("Assumptions/Simplifications:\n")
        for x in xs:
            builder.write(f"{x}\n")
        return builder.getvalue()


def usage_str(load_users_fn: Callable[[PositiveInt, Any], object], n_users: PositiveInt):
    load = load_users_fn(
        n_users,
    )
    return load_color_fmt(
        load,
        "For "
        + magnitude_fmt(n_users)
        + " users, receiving bandwidth is "
        + sizeof_fmt(load_users_fn(n_users))
        + "/hour",
    )


def get_usages_str(load_users) -> str:
    usages = [
        usage_str(load_users, n_users)
        for n_users in [
            100,
            100 * 100,
            100 * 100 * 100,
        ]
    ]
    return "\n".join(usages)


def latency_str(latency_users_fn, n_users, degree):
    latency = latency_users_fn(n_users, degree)
    return load_color_fmt(
        latency,
        "For "
        + magnitude_fmt(n_users)
        + " the average latency is "
        + ("%.3f" % latency_users_fn(n_users, degree))
        + " s",
    )


def get_latency_str(latency_users):
    latencies = [
        latency_str(latency_users, n_users, average_node_degree)
        for n_users in [
            100,
            100 * 100,
            100 * 100 * 100,
        ]
    ]
    with io.StringIO() as builder:
        latencies_strs = "\n".join(latencies)
        builder.write(f"{latencies_strs}\n")
        return builder.getvalue()


def num_edges_dregular(num_nodes, degree):
    # we assume and even d; d-regular graphs with both where both n and d are odd don't exist
    assert (
        num_nodes % 2 == 0 if isinstance(num_nodes, int) else all(n % 2 == 0 for n in num_nodes)
    ), f"Broken assumption: Expected num_nodes to be even. Instead n = {num_nodes}"
    assert (
        degree % 2 == 0 if isinstance(degree, int) else all(d % 2 == 0 for d in degree)
    ), f"Broken assumption: Expected degree should be even. Instead d = {degree}"

    return num_nodes * (degree / 2)


def avg_node_distance_upper_bound(n_users, degree):
    return math.log(n_users, degree)


# Cases Load Per Node
# -----------------------------------------------------------


class Case(ABC, BaseModel):
    label: str = Field(description="String to use as label on plot.")
    legend: str = Field(description="String to use in legend of plot.")

    @abstractmethod
    def load(self, n_users, **kargs) -> object:
        pass

    @property
    @abstractmethod
    def header(self) -> str:
        pass

    @property
    @abstractmethod
    def assumptions(self) -> List[str]:
        pass

    @property
    def description(self) -> str:
        return "\n".join(
            [
                "",
                get_header(self.header),
                get_assumptions_str(self.assumptions),
                get_usages_str(self.load),
                "",
                "------------------------------------------------------------",
            ]
        )


# Case 1 :: single shard, unique messages, store
class Case1(Case):
    label: str = "case 1"
    legend: str = "Case 1. top: 6-regular;  store load (also: naive light node)"

    def load(self, n_users, **kwargs):
        return message_size * messages_sent_per_hour * n_users

    @property
    def header(self) -> str:
        return "Load case 1 (store load; corresponds to received load per naive light node)"

    @property
    def assumptions(self) -> List[str]:
        return [a1, a2, a3, a4, a7, a21]


# Case 2 :: single shard, (n*d)/2 messages
class Case2(Case):
    label: str = "case 2"
    legend: str = "Case 2. top: 6-regular;  receive load per node, send delay to reduce duplicates"

    def load(self, n_users, **kwargs):
        return (
            message_size * messages_sent_per_hour * num_edges_dregular(n_users, average_node_degree)
        )

    @property
    def header(self) -> str:
        return "Load case 2 (received load per node)"

    @property
    def assumptions(self):
        return [a1, a2, a3, a4, a5, a7, a31]


# Case 3 :: single shard n*(d-1) messages
class Case3(Case):
    label: str = "case 3"
    legend: str = "Case 3. top: 6-regular;  receive load per node, current operation"

    def load(self, n_users, **kwargs):
        return message_size * messages_sent_per_hour * (n_users * (average_node_degree - 1) +1)

    @property
    def header(self) -> str:
        return "Load case 3 (received load per node)"

    @property
    def assumptions(self):
        return [a1, a2, a3, a4, a6, a7, a31]


# Case 4:single shard n*(d-1) messages, gossip
class Case4(Case):
    label: str = "case 4"
    legend: str = "Case 4. top: 6-regular;  receive load per node, current operation, incl. gossip"

    def load(self, n_users, **kwargs):
        messages_received_per_hour = (
            messages_sent_per_hour * (n_users * (average_node_degree - 1) + 1)
        )  # see case 3
        messages_load = message_size * messages_received_per_hour
        num_ihave = messages_sent_per_hour * n_users * d_lazy * mcache_gossip
        ihave_load = num_ihave * gossip_message_size
        gossip_response_load = (
            num_ihave * message_size  #receive load only, IWANT load not included
        ) * avg_ratio_gossip_replys  # reply load contains both an IWANT (from requester to sender), and the actual wanted message (from sender to requester)
        gossip_total = ihave_load + gossip_response_load

        return messages_load + gossip_total

    @property
    def header(self) -> str:
        return "Load case 4 (received load per node incl. gossip)"

    @property
    def assumptions(self):
        return [a1, a2, a3, a4, a6, a7, a32, a33]


# Case 5:single shard n*(d-1) messages, IDONTWANT
class Case5(Case):
    label: str = "case 5"
    legend: str = (
        "Case 5. top: 6-regular;  receive load per node, incl. IDONTWANT without IHAVE/IWANT"
    )

    def load(self, n_users, **kwargs):
        # Of all messages in the graph, the ratio of relayed messages from another node
        # Derived from the fact that "per-node messages" = xd - x, where x = messages_sent_per_hour.
        portion_not_originator = (average_node_degree - 1) / average_node_degree

        # Of the messages a node sees, the ratio of seeing for the first time.
        # Let d = average_node_degree
        # For each `d` entrances to the node,
        # we first see the message through edge 1
        # then we see message from the other `d - 1` edges.
        portion_seen_first = 1 / average_node_degree

        # Start per-node calculations.
        total_small_messages = (
            messages_sent_per_hour
            * average_node_degree
            * (1 - ratio_of_big_messages)
            * portion_not_originator
        )
        total_big_messages = (
            messages_sent_per_hour
            * average_node_degree
            * ratio_of_big_messages
            * portion_not_originator
        )
        num_big_seen_first = total_big_messages * portion_seen_first
        # Number of messages (per node) which come after the first seen message of its type.
        # In other words: count(2nd, 3rd, 4th... instance of a big message).
        num_big_after = total_big_messages * (1 - portion_seen_first)
        # Not all of the above messages come into existence (see `idontwant_too_late`).
        num_big_seen_after = num_big_after * idontwant_too_late

        # Factor in message sizes.
        small_message_load = small_message_size * total_small_messages
        big_message_load = big_message_size * (num_big_seen_first + num_big_seen_after)

        # End of per-node calculations. Factor in `n_users`.
        dontwant_load = n_users * num_big_seen_first * idontwant_message_size
        messages_load = n_users * (big_message_load + small_message_load)

        return messages_load + dontwant_load

    @property
    def header(self) -> str:
        return "Load case 5 (received load per node with IDONTWANT messages)"

    @property
    def assumptions(self):
        return [a1, a2, a3, a4, a6, a7, a16, a17, a34, a35, a36, a37]


# sharding case 1: multi shard, n*(d-1) messages, gossip
class ShardingCase1(Case):
    label: str = "case 1"
    legend: str = "Sharding case 1. sharding: top: 6-regular;  receive load per node, incl gossip"

    def load(self, n_users, **kwargs):
        case_4 = Case4()
        load_per_node_per_shard = case_4.load(np.minimum(n_users / 3, avg_nodes_per_shard))
        return avg_shards_per_node * load_per_node_per_shard

    @property
    def header(self) -> str:
        return "load sharding case 1 (received load per node incl. gossip)"

    @property
    def assumptions(self):
        return [a1, a2, a3, a4, a6, a8, a9, a10, a11, a32, a33]


# sharding case 2: multi shard, n*(d-1) messages, gossip, 1:1 chat
class ShardingCase2(Case):
    label: str = "case 2"
    legend: str = (
        "Sharding case 2. sharding: top: 6-regular;  receive load per node, incl gossip and 1:1 chat"
    )

    def load(self, n_users, **kwargs):
        case_4 = Case4()
        load_per_node_per_shard = case_4.load(np.minimum(n_users / 3, avg_nodes_per_shard))
        load_per_node_1to1_shard = case_4.load(np.minimum(n_users, avg_nodes_per_shard))
        return (avg_shards_per_node * load_per_node_per_shard) + load_per_node_1to1_shard

    @property
    def header(self) -> str:
        return "load sharding case 2 (received load per node incl. gossip and 1:1 chat)"

    @property
    def assumptions(self):
        return [a1, a2, a3, a4, a6, a8, a9, a10, a11, a12, a13, a14, a32, a33]


# sharding case 3: multi shard, naive light node
class ShardingCase3(Case):
    label: str = "case 3"
    legend: str = "Sharding case 3. sharding: top: 6-regular;  regular load for naive light node"

    def load(self, n_users, **kwargs):
        case_1 = Case1()
        load_per_node_per_shard = case_1.load(np.minimum(n_users / 3, avg_nodes_per_shard))
        return avg_shards_per_node * load_per_node_per_shard

    @property
    def header(self) -> str:
        return "load sharding case 3 (received load naive light node.)"

    @property
    def assumptions(self):
        return [a1, a2, a3, a4, a6, a8, a9, a10, a15, a32, a33]


# Cases average latency
# -----------------------------------------------------------


class LatencyCase1(Case):
    label: str = "latency case 1"
    legend: str = "Latency case 1. topology: 6-regular graph. No gossip"

    def load(self, n_users, degree):
        return avg_node_distance_upper_bound(n_users, degree) * average_delay_per_hop

    @property
    def header(self) -> str:
        return (
            "Latency case 1 :: Topology: 6-regular graph. No gossip (note: gossip would help here)"
        )

    @property
    def description(self) -> str:
        return "\n".join(
            [
                "",
                get_header(self.header),
                get_assumptions_str(self.assumptions),
                get_latency_str(self.load),
                "------------------------------------------------------------",
            ]
        )

    @property
    def assumptions(self):
        return [a3, a41, a42]
