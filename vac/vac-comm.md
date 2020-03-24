# [WIP] vac.comm aka waku/next

*This document is an early work in progress, and largely consists of notes that will be used to fill out a more thorough document such as [[WIP] Dagger: A Distributed Storage Network](https://hackmd.io/CDg3GXyTSbSmBQjL93hooA?both) and/or [vacp2p.Communication - System Design & Technical Architecture](https://docs.google.com/document/d/1OkltbPr9jF1cx9O38evw-VarfKQ5L2LOsadCvV7xpZw/edit?ts=5e29c00d&pli=1#).*

vac.comm provides private and decentralized communication, and is part of the Vac communication/storage/compute umbrella.

## Motivation and challenges

**Challenges being addressed:**
- scalability of the network
- incentived infrastructure and spam-resistance
- build with resource restricted devices in mind, including nodes being mostly offline

## System design, technical architecture and rationale

These are rough notes of things we currently know and don't know. They should be reformulated as a more coherent narrative.

**Relation between storage and communication:**
- We'll use the same building blocks (Nim, libp2p and many its more basic protocols, etc)
- We don't want to force a solution that fits for communication but not storage, and vice versa
- That said, we'll continuously look and strive for overlap between the two when it comes to routing, incentivization, etc

**On message routing:**
- Current Whisper-based routing fundamentally doesn't scale
- For structured approaches, Kademlia for full nodes is the leading candidate
- For unstructured approaches, gossipsub and episub are worth looking into more as complementary approaches

**On Kademlia routing:**
- This provides point to point and point to neighborhood capabilities
- Neighborhood routing is provided for with partial addressing a la PSS, and needs more experimental research to confirm feasibility
- As a fallback, an unstructured gossip mechanism can be used for neighborhood messaging

**On classical vs forwarding Kademlia:**
- Trade-off between classical and forwarding Kademlia: what's faster, opening new connections or re-using them?
- Classical Kademlia better studied, and also more tractable when it comes to who is doing the work
- We can likely provide both as options to keep flexibility, e.g. for heavy TCP forwarding might make more sense

**On incentivization:**
- Structured and more direct approaches like classical Kademlia more tractable in terms of who does what
- Incentivization in an unstructured routing setup a la gossip currently unproven
- More ideas need to be explored and falsified aggressively in this area, e.g. see Block.Science effort, Swarm postage stamps, etc

**On adaptive nodes:**
- Nodes with limited battery and short connection windows won't relay messages, and will instead likely rely on an emergent service network
- In this emergent service network, lighter nodes can have a simple cryptoeconomic game with fuller nodes in a simple request/response manner
- For semi-powered nodes, they can seamlessly join the DHT (e.g.) and provide some form of routing/storage

**On security, spam protection and availability:**
- S/Kademlia can be used as anextension with some form of registration cost
- Spam protection mechanisms needs further experimentation, e.g. stake based priority queue, postage stamps, zkSnarks rate limiting
- Node uptime assumptions and replication factors are fairly well-studied in Kademlia and can be leveraged statistically

**On privacy:**
- Transport privacy will be developed as a modular approach since not all use cases require it, and there are fundamental performance limitations
- With pseudoanonymity, spam protection and E2EE a lot of privacy guarantees are achieved over current state of things
- Offloading a lot of research to Nym et al, can also be complemented by making it easy to run over existing mixnet/Tor-like stacks, a la Briar

## Timeline and milestones

### February - March 2020

**Ongoing:**

1. Write an experimental Kademlia implementation for nim-libp2p, with the goal of
  - increasing tacit knowledge of Kademlia/libp2p/Nim
  - acting as a base layer for upcoming applied research work

2. Do research in conjunction with Dagger priorities as outlined below

**Outstanding:**

1. Get consensus on strategy, direction for most immediate users (Vac meetup, Dagger and Status Core)

2. Create a detailed timeline for implementing the project as a deliverable

**Overlap / in conjunction with Dagger priorities:**

1. Research existing projects such as:
        Swarm
        IPFS/Filecoin
        BitTorrent

2. Research relevant academic literature

3. Validating existing economic models as well as exploring our own

### March - June 2020

As an initial goal, we will focus on building an MVP with a limited subset of features such as:

- Send messages to a single point
- Send messages to a neighborhood
- Find nodes and content

This will require a few components in place:

**Completed:**

- p2p networking stack
    we have an initial implementation of libp2p in Nim, this should be enough to start development, but it will be improved and augmented with new features on an ongoing basis

**Outstanding:**

- A wire protocol to
    Coordinate with other nodes
    Send and receive messages to one and multiple nodes

- Feasibility study of neighborhood routing

- Accounting and incentivization simulation for adaptive nodes

- PoC for offline/storage interface

- Node capabilities and discovery beyond DNS
