# DRAFT: Different approaches to data sync

**WARNING: This is an early draft, and likely contains errors.**

*Written March 29, 2019 by Oskar.*

This document compares various forms of data sync protocols and applications, along various dimensions, with the goal of making it easier for you to choose which one is for you.

Let's start with some definitions.

## Table of contents

- TODO: Introduction
- Definitions
    - Further work
- Methodology
    - Compared dimensions
        - Further work
    - Compared technologies
        - Further work
- TODO: Consider adding description here
- Comparison
    - Further work
- Summary
- References

## Introduction

TODO

## Definitions

*Node*: Some process that is able to store data, do processing and communicate with other nodes.

*Peer*: The other nodes that a peer is connected to.

*Peer-to-peer (P2P)*: Protocols where resources are divided among multiple peers, without the need of central coordination.

*Device*: A node capable of storing some data locally.

*User*: A (human) end-user that may have multiple *devices*.

*Data replication*: Storing the same piece of data in multiple locations, in order to improve availability and performance.

*Data sync*: Achieving *consistency* among a set of nodes storing data

*Mobile-friendly*: Multiple factors that together make a solution suitable for mobile. These are things such as dealing with *mostly-offline* scenarios, *network churn*, *limited resources* (such as bandwidth, battery, storage or compute).

*Replication object*: Also known as the minimal unit of replication, the thing that we are replicating.

*Friend-to-friend network (F2F)*: A private P2P network where there are only connections between mutually trusted peers.

*Content addressable storage (CAS)*: Storing information such that it can be retrieved by its content, not its location. Commonly performed by the use of cryptographic hash functions.

*Consistency model*: ...
*Mostly-offline:* ...
*Network churn:* ...
*Light node:* ...

*Private P2P*: ...
*Structured P2P network*: ...
*Unstructed P2P network*: ...
*Super-peer P2P network*: ...
*Group-based P2P network*: ...

*Cryptographic hash function*: ...


### Further work

- Is minimal unit of replication necessarily the right abstraction? E.g. messages but you care about conversation, chunks vs files, etc.
  
## Methodology

We look at generally established dimensions in the literature [TODO] [TODO], and evaluate protocols and applications based on these. Specifically the focus is on p2p applications that perform some form of data synchronization, with a bias towards secure messaging applications.

All notes are tentative and are based on the provided documentation and specification. Code is generally not looked into, nor has any empirical simulations been performed. These results have yet to be reviewed so take them with a grain of salt.

### Compared dimensions

These dimensions are largely taken from the survey paper [TODO].

- Minimal unit of replication
- Read-only or read and write
- Single-master vs multi-master
- Synchronous vs asynchronous
- Asynchronous optimistic or not
- Eager or lazy updates
- Full vs partical replication
- Consistency model
- Active vs full replication
- P2P type/topology

## Notes on single-master vs multi-master

For single-master, there's only a single node that writes to a specific piece of data. The other peers purely replicate it and don't change it.

For many of the studied systems, *content addressable storage* is used. This means the replication object is usually immutable, and it is only written to once. As a side effect, many systems are naturally single-master from this point of view.

This is in comparison with the survey paper, where they are more interested in update-in-place programming through replicating SQL DBs and other "rich" data structures.

However, if we look at what is semantically interesting for the user, this is usually not an individual message or chunk of a file. Instead it is usually a conversation or a file. Seen from that point of view, we often employ some form of linear or DAG-based version history. In this case, many participants might update the relevant sync scope. Thus, the system is better seen as a multi-master one. To capture this notion I've modified single-master dimension to be w.r.t. replication object or user scope point of view. I suspect the latter is more informative for most cases.

TODO: Tighten up above paragraph with better definitions.

### Further breakdown

TODO: Add definitions of below
TODO: Add more relevant dimension
TODO: Possibly decompose into further subproblems
TODO: Possibly re-structure as who-what-when-where-how-withwhat

- linear/dag version history?
- framing - support for nosync messages?
- privacy-preservation (~wrt p2p layer?)

## Compared technologies

This includes both applications and specification. The level of rigor and nomenclature varies between projects.

- Briar and its associated Bramble protocol stack [TODO]

- Matrix and its specification [TODO]

- Secure Scuttlebutt [TODO]

(- Tox and its Tok Tok specification [TODO])

- Swarm [TODO]

### Further research

- Apples to apples: Does it really make sense to compare Matrix with something like Swarm directly? This also depends on how decomplected protocols are and to what extent they can be studied in isolation.

- More technologies: Bittorrent, Git, Tribler, IPFS. Whisper, Status.

- Similarities and differences: Since a lot of protocols make the same choices, it might make sense to break similarities apart and focus on differences. Similar to what is done in Whisper vs PSS [TODO].

...

## Comparison

| Dimension | Bramble | Matrix | SSB | Swarm |
| ---------- | -------- | -------- | --- |--- | 
| Replication object | Message (DAG) | Message* (DAG/*) | Messages (?) (Log) | Chunks (File/Manifest) |
| Single-master? (object) | Single-master | Depends* | Single-master |  |
| Single-master? (scope) | Multi-master | Multi-master | Single-master | | 
| Asynchronous? |Yes  | Partial | Yes | Yes | Yes |
| Asynchronous optimistic? | Yes | Yes | Yes | Yes |
| Full vs partial replication? | Partial | Partial | Partial? | Partial |
| Consistency model | Casual consistency | Casual | Eventual / Casual |
| Active replication? | No | Yes | Yes | Yes |
| P2P Topology | F2F Network | Super-peer | Group-based | Structured |


- Read-only or read and write
- Single-master vs multi-master
- Synchronous/eager vs asynchronous/lazy
- Asynchronous optimistic or not
- Full vs partical replication
- Consistency model
- Active vs full replication
- P2P type/topology

### Further work

- This dimension is a bit hairy: `| Read-only? | Read&Write | Read&Write | Read&Write | Read&Write |` - it depends on what we see as the minimal object of replication, and I'm not satifised with the  current separation

- Maybe it makes more sense to have two replication objects, e.g. chunks and DAG or log, as opposed to changing notion of single-master etc

- Matrix depends: should capture auth state semantics

- How deal with other things that are kind of replicated but differently? E.g. metadata, etc. Auth state, ephemeral, manifests, feeds, etc.

## Summary

TODO

## References

TODO
