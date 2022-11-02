---
layout: post
name:  ""
title: ""
date: 2022-10-18 10:00:00
author: sanaztaheri
published: true
permalink: /waku-rln-relay-journey
categories: research
summary: Private spam-protected gossip-based routing of WAKU-RLN-RELAY: academic publications, PoC implementation, cross-client testnet, technical specs, and future state.
image: 
discuss: 
_includes: [math]
---

In this post, we would like to shed light on the current state of the research and development of the WAKU-RLN-RELAY project as well as its future direction and the areas of work to which the readers of this post may wish to contribute.

# WAKU-RLN-RELAY: Why and How

**Why**: The WAKU-RLN-RELAY project was started more than two years ago to protect the open p2p messaging protocol of [WAKU-RELAY](https://rfc.vac.dev/spec/11/) against spam and DDoS attacks.
However, the use case of WAKU-RLN-RELAY is not limited to the WAKU-RELAY protocol and can be adopted by any open p2p routing system.
It is worth mentioning that WAKU-RELAY is a minor extension of [Libp2p Gossipsub protocol](https://github.com/libp2p/specs/blob/master/pubsub/gossipsub/README.md), hence the spam protection property of WAKU-RLN-RELAY is directly applicable to the libp2p Gossipsub protocol too. 
In a nutshell, spam protection is achieved by limiting the messaging rate of every network participant so that no user can flood the network with a large number of messages and congest/DDoS relayers.
One special focus of WAKU-RLN-RELAY is user privacy which is aligned with the WAKU-RELAY privacy objectives.
That is, it does not rely on any personally identifiable information of users like IP address or peer ID to control their messaging rate.  
This makes it superior in terms of privacy guarantees compared to centralized systems where users are asked to share some PII like a phone number, or an email address for network participation.
Moreover, WAKU-RLN-RELAY is superior to existing privacy-preserving counterparts e.g., proof-of-work in terms of performance.
The computational overhead imposed by proof-of-work is not suitable for resource-limited devices like mobile phones whereas the computational overhead incurred by the WAKU-RLN-RELAY protocol is minimal and at the time of writing this post is approximately less than half a second. 


**How**: 
Network participants which want to send messages in the network should be registered in the RLN group.
The state of the group is moderated by a smart contract which holds a list of enrolled members.
Each participant has a secret identity key and registers a commitment of that to the membership smart contract and deposits some funds.
The key to withdraw the locked funds is the user's secret identity key, so if someone knows someone else's secret identity key, they can withdraw the associated funds.
Messaging rate is enforced per some time interval called an epoch.
For each epoch, the user sends a message by proving that it knows the opening to one of the commitments registered in the RLN group as well as it reveals a [Shamir](https://en.wikipedia.org/wiki/Shamir%27s_Secret_Sharing)'s share of its secret id key. 
The share is derived in such a way that two of them when computed in the same epoch, allow the construction of the corresponding secret id key. 
Shares are computed using also an application-defined identifier i.e., the RLN identifier that binds them to the application employing RLN-RELAY.
That is, if a user wants to use the same RLN membership credential for messaging in two or more different applications, then they can do so without being worried to get slashed by combining the shares of its identity key published in those applications.

## Current State

**Specifications**: The specification of the WAKU-RLN-RELAY protocol is currently in draft mode and available in [17/WAKU2-RLN-RELAY](https://rfc.vac.dev/spec/17/).
In a separate effort, as part of a collaboration with the PSE group, the specification of the RLN construct, as a stand-alone primitive, has been standardized and published in [32/RLN](https://rfc.vac.dev/spec/32/).


**Academic publications**: The results of this project are published as 2 academic research articles in two prestigious conferences, namely, [ICDCS](https://icdcs2022.icdcs.org/programs/) and [DINPS](https://research.protocol.ai/sites/dinps/programme/) 2022.
They are accessible at [WAKU-RLN-RELAY: Privacy-Preserving Peer-to-Peer Economic Spam Protection (full paper)](https://arxiv.org/pdf/2207.00117.pdf) and [Privacy-Preserving Spam-Protected Gossip-Based Routing (poster)](https://ieeexplore.ieee.org/abstract/document/9912176/). 


**Testnets**: Two testnets are launched so far:
- Testnet1: In this testnet, we implemented the PoC of WAKU-RLN-RELAY in Nim and integrated it into a sample chat application. More on this can be found in [testnet1 tutorial](https://github.com/status-im/nwaku/blob/master/docs/tutorial/rln-chat2-live-testnet.md).
The testnet launched successfully and we got great feedback from the participants to improve upon user experience and resolved identified concerns and comments. 

- Testnet2: This testnet aimed to integrate WAKU-RLN-RELAY into all 3 Waku clients namely, Nim-Waku (nwaku), Go-Waku, and js-Waku and test their interoperability over the Waku network. 
All three clients consumed the [Zerokit RLN module](https://github.com/vacp2p/zerokit/tree/master/rln) to handle the zkSNARKs proof generation and verification logic. 
This testnet is still up and running and instructions on the participation can be found in the following tutorial: [WAKU-RLN-RELAY testnet2: cross-client](https://github.com/status-im/nwaku/blob/master/docs/tutorial/rln-chat-cross-client.md).
Should you be interested in taking part in the testnet, or have any questions, let us know in our dedicated discord channel [WAKU-RLN-RELAY dogfooding](https://discord.com/channels/864066763682218004/945761301156753448).

**Zerokit**: The use of zero-knowledge proofs and zkSNARKs to provide privacy-enhanced service is not limited to the WAKU-RLN-RELAY protocol. 
The design and development of all the Waku protocols are centered around privacy protection and anonymity. 
This made us realize the need to develop our zero-knowledge toolings to embrace this need.
The [Zerokit library](https://github.com/vacp2p/zerokit) was born out of this desire to build a self-hosted library to do research and exploration in the zkp field.
Zerokit currently comprises the RLN module and is going to be extended by other novel relevant constructs.
One of the driving factors of Zerokit is to facilitate the use of certain Zero Knowledge modules from other environments, namely, systems programming environments, command-line, and mobile environments. 
More on the Zerokit positioning is available in [Zerokit positioning](UAFvOj1tTQ6uW2li0ZeXfw).
  

**Incentivization**: Spam protection will not be realized unless a sufficient number of relayers choose to run WAKU-RLN-RELAY and protect the p2p messaging network against spammers.
Since spam activities and DDoS attacks directly target and exhaust network resources, it is conceivable that relayers would be naturally incentivized to run WAKU-RLN-RELAY to prevent their local resources from being drained by attackers. 
Nevertheless, WAKU-RLN-RELAY comes with built-in economic incentives where 
relayers who detect spammers are rewarded with the ability to withdraw the spammer's staked funds from the membership contract.
However, not every node gets to find a spammer and be rewarded for that.
Indeed, due to the cryptographically solid economic punishment in place, fewer spam activities are expected to be observed.
This led us to introduce the service fee option to the RLN membership contract to compensate relayers for their spam-protection service (regardless of whether they spot any spamming activity or not).
That is, a portion of the membership registration fee goes towards a non-refundable service fee.
The distribution of the collected service fee is still a work in progress and its current state can be seen in the [rln contract](https://github.com/vacp2p/rln-contract) GitHub repository.

**Support for ERC20 tokens as RLN membership fee**: It is conceivable that many applications desire to have their tokens and want their RLN group membership fee to be paid in that token.
To enable this, we are working towards updating the RLN contract interface to support the ERC20 token for the membership fee. 
The ERC20 support is in progress and its current state can be tracked in the [rln contract](https://github.com/vacp2p/rln-contract) GitHub repository.

**Evaluating storage overhead of membership Merkle tree**:
In WAKU-RLN-RELAY, the relayers construct and maintain the membership Merkle tree locally.
This is in favor of attaining more cost-efficient group management, compared to storing the Merkle tree on-chain and dealing with the associated gas cost for every update. 
The feasibility of this design choice concerning the storage overhead for resource-limited devices remained questionable until we conducted our study and simulation to address this concern. 
The result of our simulation and measurements are published in the following forum post [evaluating storage overhead of membership Merkle tree](https://forum.vac.dev/t/WAKU-RLN-RELAY-evaluating-storage-overhead-of-membership-merkle-tree/151).
The outcome of this study proved to us the feasibility of this design choice even for resource-restricted environments.
Nevertheless, for scalable production usage and as future work, we would still like to look into some disk-based tweaks for Merkle tree storage management.


## Future work
The WAKU-RLN-RELAY has multiple active working areas as explained below. 
If you are interested in any of these, or if you have further research ideas, we strongly encourage you to [contact us](#contact-us) and let us know!

**Zerokit RLN module improvements**: Zerokit library is undertaking multiple improvements including but not limited to the following areas. For more on this track, watch the [Zerokit repository](https://github.com/vacp2p/Zerokit). 
* Enabling WASM support to use Zerokit directly through browsers.
* Optimizing the library size
* Improving performance of the RLN module by enabling multi-threading in RLN-wasm
* Compiling Zerokit to mobile architectures
* Implementing a command-line interface for common operations of the Zerokit RLN module 

**Next testnets**: Multiple other testnets are on the way, one of which would be focused on secure slashing. 
In such testnet, the goal is to build and examine the slashing part of WAKU-RLN-RELAY where network participants not only detect spam activities but also can slash spammers and claim their rewards from the contract. 
Further testnets can be potentially on consuming and testing the new features of the RLN membership contract e.g., service fee option, and ERC20 integration.

**Security audit**: We are planning to perform a security audit of the RLN membership group smart contract and the RLN module of the Zerokit lib. 
This will happen once they both get more mature in terms of functionality as well as a couple of rounds of internal tests and examinations.

**RLN trusted setup**: Down the line, we will conduct the MPC ceremony to generate parameters specific to the RLN circuit.

**Hybrid architecture for the membership Merkle tree storage management (super-peer/light-peer)**: In the current design of RLN-relay, every peer needs to persist and maintain the membership Merkle tree locally. 
While the storage overhead of Merkle tree is reasonable as discussed in the [WAKU-RLN-RELAY current state](#current-state), 
many applications may still wish to save that storage space in favor of other critical functionalities.
To allow this, we are looking into a hybrid architecture in which only a subset of peers namely, super peers persist and maintain the membership Merkle tree.
Other peers namely light peers fetch their necessary information from the super peers via a request/response protocol.
Note that as in any request/response protocol, privacy should be carefully addressed as the service providers may be able to infer the position of the requester's id commitment in the membership Merkle tree from requests' patterns. 

**Zero-entry**: Some applications may want to allow their users to benefit from a spam-protected network and publish messages without having any crypto assets. 
This can be realized through a request/response protocol e.g., an extension of [WAKU2-LIGHTPUSH](https://rfc.vac.dev/spec/19/).
That is, the lightpush service provider registers multiple accounts in the RLN group 
in order to obtain a higher messaging rate i.e., one message per membership registration.
Peers without RLN membership can then request the lightpush service provider to publish their messages using its batch of registered identity commitments.
This is one way to realize the zero-entry feature, and other possibilities should be explored further.

# Contact us
If you are interested in being involved in the development or research side of WAKU-RLN-RELAY, please let us know:
- Participate in the [Waku-RLN-Relay testnet2](https://github.com/status-im/nwaku/blob/master/docs/tutorial/rln-chat-cross-client.md)
- Track or open issues on [nwaku GitHub repository](https://github.com/status-im/nwaku) or in [Zerokit library](https://github.com/vacp2p/zerokit)
- Suggest improvements or propose new ideas on the specification through [RFC repository](https://github.com/vacp2p/rfc)
- Discord channels: [RLN channel](https://discord.com/channels/864066763682218004/905333924476108800) and [WAKU-RLN-RELAY dogfooding](https://discord.com/channels/864066763682218004/945761301156753448)

## References

* [10/WAKU2](https://rfc.vac.dev/spec/10/)
* [11/WAKU2-RELAY](https://rfc.vac.dev/spec/11/)
* [17/WAKU-RLN-RELAY](https://rfc.vac.dev/spec/17/)
* [19/WAKU2-LIGHTPUSH](https://rfc.vac.dev/spec/19/)
* [32/RLN](https://rfc.vac.dev/spec/32/)
* [nwaku GitHub repository](https://github.com/status-im/nwaku)
* [WAKU RFC repository](https://github.com/vacp2p/rfc)
* [libp2p GossipSub](https://github.com/libp2p/specs/blob/master/pubsub/gossipsub/README.md)
* [WAKU-RLN-RELAY testnet1](https://github.com/status-im/nwaku/blob/master/docs/tutorial/rln-chat2-live-testnet.md)
* [Waku-RLN-Relay testnet2: cross-client](https://github.com/status-im/nwaku/blob/master/docs/tutorial/rln-chat-cross-client.md)
* [Evaluating storage overhead of membership Merkle tree](https://forum.vac.dev/t/waku-rln-relay-evaluating-storage-overhead-of-membership-merkle-tree/151)
* [Zerokit library](https://github.com/vacp2p/zerokit)
* [Zerokit positioning](UAFvOj1tTQ6uW2li0ZeXfw)
* [Zerokit RLN module](https://github.com/vacp2p/zerokit/tree/master/rln)
* [RLN contract repository](https://github.com/vacp2p/rln-contract)
