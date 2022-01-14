Below is the summary of my findings up until now. 

# Problem Definition

This document is going to provide a comparison between  Tor and Waku. The ["What is Tor"](#what-is-tor) section presents a quick overview of the Tor and can be skipped for those that are already familiar.  


# What is Tor

As stated in the [Tor specifications](https://gitweb.torproject.org/torspec.git/tree/tor-spec.txt#n142), Tor is a distributed overlay network designed to anonymize low-latency TCP-based applications such as web browsing, secure shell, and instant messaging. Clients choose a path through the network and build a `circuit`, in which each node (or `onion router `or `OR`) in the path knows its predecessor and successor, but no other nodes in the circuit.  Traffic flowing down the circuit is sent in **fixed-size** `cells`, which are unwrapped by a symmetric key at each node (like the layers of an onion) and relayed downstream. Tor only works for TCP streams and can be used by any application with SOCKS support.

## Workflow
- The Tor client fetches a list of Tor nodes (Onion routers) from a directory server. Onion routers are voluntarily operated servers around the world that are listed publicly in a directory and there is no concern finding out their identity.
- The Tor client picks a random path to the destination server. The path includes three hops. 
- The client negotiates a separate set of encryption keys for each hop along the circuit to ensure that each hop can't trace these connections as they pass through. The message is then encrypted through **3 layers of encryption**. 
  - For example, consider A sending message `M` to B through 3 routers R1, R2, and R3 i.e., A → R3 -> R2 -> R1 -> B, the message `M` is encrypted with 3 keys, in 3 layers as `E(k3, E(k2, E(k1, M)))` where each key is only known to one of the intermediate nodes.
- Each routing node decipher the message using the shared key, finds out who is next-hop, and passes it over. 
  
**Side Notes:**
- Tor's users employ this network by connecting through a series of **virtual tunnels** rather than making a direct connection, thus allowing both organizations and individuals to share information over public networks without compromising their privacy.
- Routing nodes only need to know their preceding and exceeding connection, but not the sender of the message. 
- Once a circuit has been established, many kinds of data can be exchanged and several different sorts of software applications can be deployed over the Tor network.
  - For efficiency, the Tor software uses the same circuit for connections that happen within the same ten minutes or so. Later requests are given a new circuit, to keep people from linking your earlier actions to the new ones.
- No header is added to the message, otherwise, it would be a lot easier to see how far the message is from its destination. 
- Tor is one implementation of Onion routing
- The more people use the Tor network the stronger it gets. As it is easier to hide in a crowd of people that look the same

## Security consideration
Tor is all about **Transport Security** and there is no anonymity guarantee about the data that is sent by the user over Tor e.g., an attacker may eavesdrop on the last connection in the Tor circuit to the destination server, and sees someone's username and password in clear. It is up to the user to use TLS or HTTPS for the connection. What is transported is exactly an HTTPS request and reply that goes through Tor instead of the ISP router.


## security features
Below is the list of  the security features that Tor provides, however, the essence of all these features is two things:
1. Tor hides (or make it difficult to know) the two ends of communication i.e., who is talking to whom
2. It has metadata protection that includes 
   - Users Real identity
   - Precise location 
   - OS
   - The browser used to surf the web
   
To make a fair comparison with waku, we need to know whether we can achieve these two major features or not and how.

Further on the features of the Tor:
- Protects against Traffic analysis by concealing headers of Internet data packets: How does traffic analysis work? Internet data packets have two parts: a data payload and a header used for routing. The data payload is whatever is being sent, whether that's an email message, a web page, or an audio file. Even if you encrypt the data payload of your communications, traffic analysis still reveals a great deal about what you're doing and, possibly, what you're saying. That's because it focuses on the header, which discloses source, destination, size, timing, and so on.
- **BROWSE FREELY** Tor is a censorship circumvention tool, allowing its users to reach otherwise blocked destinations or content. One reason for that is the pool of volunteer-run servers known as Tor relays.
- **DEFEND AGAINST SURVEILLANCE** Tor Browser prevents someone watching your connection from **knowing what websites you visit.** All anyone monitoring your browsing habits can see is that you're using Tor.
-  **MULTI-LAYERED ENCRYPTION**: The traffic is relayed and encrypted three times as it passes over the Tor network. The network is comprised of thousands of volunteer-run servers known as Tor relays. Though, this is not exactly for confidentiality but more for anonymity. The final data that is passed to the final destination may still be unencrypted and compromised privacy. 
- **BLOCK TRACKERS** Tor Browser isolates each website you visit so third-party trackers and **ads can't follow you**. Any **cookies automatically clear** when you're done browsing. Cannot compare this part with waku as I am not sure about the low-level details of performing advertising in waku.
- **RESIST FINGERPRINTING** Tor Browser aims to make all users look the same, making it **difficult** for you to be fingerprinted based on **your** **browser** and **device information**.



## Security Vulnerabilities

<!-- - If the adversary is the front node and the exit node on the circuit, then it can figure out what is going on. -->
- [ ] This is not an exhaustive list of attacks, but just a few of them. 

- End-to-end timing attack: Tor does not protect against end-to-end timing attacks: If your attacker can watch the traffic coming out of your computer, and also the traffic arriving at your chosen destination, he can use statistical analysis to discover that they are part of the same circuit.

- Traffic analysis: imagine you have got the time signature of the messages sent by a single client. The incoming traffic to the destination server will be a mess of lots of messages. But imagine that you can find the key points that match up with what the client sent in. Then it can be used to deanonymize that client.
  

## Performance Concerns

Tor routers may be distant and you may get delay till your message gets to the destination. 
- [ ] An empirical analysis of this is needed to make a fair comparison with waku.

# Anonymity levels
Anonymity can be analyzed at various levels. Below is a broad classification of such: 
- Communication anonymity against a third person, in this anonymity level, the communication must stay anonymous in the eyes of a third person. Nevertheless, the sender and receiver may know each other and have no concern in this regard.
- Sender anonymity (against the network and the receiver):  For example when you want to hide the fact you are visiting a website
<!-- You need to use **protocol-specific support software** if you don't want the sites you visit to see your identifying information. This exists in the Tor browser, For example, you can use Tor Browser while browsing the web to withhold some information about your computer's configuration. -->
- Receiver anonymity, where there is a publisher  with public identity lets say broadcasting political news, and the subscribers want to hide their interest in that topic yet be able to have access to the news

In the following, the focus will be providing anonymity against a third party as the baseline.
- [ ] later, we can also examine the feasibility of two other anonymity levels in Waku.

<!-- # Attack types -->
<!-- Targeted attacks, when the attacker is interested in the communication of two specific nodes -->
# Waku
In waku, the relay protocol constitutes the transport layer hence the end goal would be to preserve anonymity in this layer isolated from other available protocols. 
- [ ] As such, we rule out the anonymity concerns related to the filter or store protocols. As in those protocols, some level of trust is expected between the two participating peers as the service provider and the consumer.

In the following, we consider that the relay protocol consists of only full nodes i.e., those who act as a relayer and as a publisher. 
- [ ] Later, we can extend the security analysis for the light nodes and also consider the inclusion of other protocols e.g., filter.

**Transported Data**
One source of information for the attacker in breaking anonymity is the metadata that is included inside the transported data. Such information can be included to aid the transportation or can be some application-level information that is embedded in the message body. The presence of any personally identifiable information can help the attacker identify the sender and the receiver of the message. 
So, it is vital to make sure that the data packets in the waku relay protocol do not carry sensitive metadata and PII. 
The structure of waku messages and the headers used during the transportation via the GossipSub protocol (i.e., Waku-Relay) are as below:
A waku message contains: 
- Payload which can be encrypted
- ContentTopic
- Version
- Timestamp
The waku message then resides inside the `data` field of a pubsub message with the following fields
- data
- topic
- seq#
- from
- sign
- key


## No Sign Policy
To preserve anonymity, the relay protocol follows a strict no sign policy which means the `seq#`, `from`, `sign`, and `key` fields are omitted as they indicate info related to the sender of the message.

- [ ] The use of IP addresses in the GossipSub protocol is not clear to me, I need to make sure that the sender's IP of the sender does not get shared/used during the routing process.

## Payload Encryption
The payload field contains the content of the message either in clear or encrypted. Having it encrypted has two benefits, one is data confidentiality and the other is that it prevents unintentional disclosure of personally identifiable information e.g., the payload may contain the sender's email address. 


## Topic anonymity
The use of `topic` is an application layer concern and not directly related to the waku protocol stack. However, a solution on how to treat and utilize this field securely is the key to anonymity and is worthy of investigation. 

Currently, the `topic` field is used to connect the two ends of communication i.e., the publishers and the subscribers find each other through pubsub topics. Also, AFAIK, the Status app relies on the pubsub topics to distinguish between different 1:1 or group chats. That is each 1:1 chat is associated with a distinct chat id used as the pubsub topic. Having unique pubsub topics enables the attacker to spot the sender and the receiver. How?   Let's say an attacker eavesdrops on the network traffic of two targeted nodes and realizes that they are actively relaying messages of the pubsub topic X, then it can infer they are communicating which each other. 

The general rule is that when a node is part of a topic mesh then he is the (potential) receiver of messages of that topic. Hence if a topic indicates a group of communicating nodes, then breaking the anonymity can be done by identifying the nodes within the same mesh. This info is not secret and is somewhat publicly available.

### Topic sharding
Topic sharding is to blend multiple groups of communicating participants into one i.e., mixing multiple meshes into one. As such, instead of having one shard for each topic let's say K1 ... KN, all of them will be in the same shard hence relayed within one single mesh. then the relay nodes in K1 are indistinguishable from K2 and... KN. This is also known as K-anonymity when a group of k users looks identical w.r.t. some attributes.
Another way to look at topic sharding is that nodes from otherwise distinct meshes aid in relaying topics of other meshes. 
 <!-- to confuse the attacker and make the topics less specific. -->

- [ ] Is k-anonymity sufficient? How does it compare to the Tor? It depends on the deployed sharding algorithm as well as the adversary background knowledge. A concrete answer requires a study on k-anonymity techniques and their security analysis and attacks.

## Potential solution: Growing the topic mesh with random volunteered relay nodes (server donation)
One way to preserve anonymity is to encourage more nodes to participate in relaying random pubsub topics i.e., topics that might not be of their interest. This way the true participants of the mesh will get mixed with the volunteer ones and will enable a higher level of anonymity. However, it comes with the cost of bandwidth for the volunteered relay nodes.

## Single global pubsub topic
The ultimate and maximum anonymity level that can be achieved by topic sharding is when all the topics are shared into one single topic i.e., all the nodes relay all the topics. As the result, being a relay node of that single topic conveys no useful information about the true interest of the relayer. However, this approach might be inefficient and costly for all the relayers.

### Potential Solution: The use of Content Topic for group management
In the case of using one single pubsub topic, we can distinguish different communication groups e.g., 1:1 and group chats through waku content topics.
This may sound like getting back to the same set of security issues as when the pubsub topic is used for the same purpose, however, there are several differences:
- Being a relay node does not mean being the receiver of all the content topics published on that pubsub topic. Indeed, we are decoupling the routing from the group management layer. 
- The receiver of the message remains anonymous as long as it does not publish a message with a similar content topic. This is not the case when pubsub topics are used to signify group ids.
#### Asymmetric content topics
Now, to provide anonymity we need to find a way to hide the link between a publisher and his content topic.
Let's take a different perspective, instead of hiding who is publishing to which content topic, let's focus on making the content topics look different from the sender to the receiver i.e., using asymmetric content topics. For example, Alice uses content topic `A` to send a message to Bob whereas Bob replies to Alice using content topic `B`. In this example, both Alice and Bob know that they should expect and listen to content topics `B` and `A`, respectively.  
- [ ] This is just a proposal, but a concrete solution on such asymmetrical topic generation needs more research. Just for intuition, you can think of the double ratchet algorithm and how it yields a unique message key per send and receive. The message keys can be used as the content topic in the waku messaging scenario.

# Waku security issues
Timing attack on publisher-topic unlinkability: The act of publishing to a topic is theoretically protected and is anonymous, That is by hijacking a link and getting to see message m is set from node A to B, cannot judge the author of the message (A can be a relayer or can be the original publisher). However, a more powerful adversary can monitor multiple network links and analyze the delay by which the message arrives at other nodes of the network. The one with minimum delay is potentially closer to the owner of the message or even is the message's owner. 
For example in the chain of nodes A->B->C->D, if A generates and publishes a message M, then B is the first one the receives it, and D is the last one. Such time difference can help to identify the owner of the message. 

# Waku advantages over the Tor
One potential advantage of using waku is that it is computationally lighter than Tor and does not require multiple encryption and decryption. This would also lower the message transmission delay.

Another advantage is the lighter key management where the sender does not have to establish shared keys with all the intermediate routers (as opposed to the Tor).

<!-- No **end-to-end timing attack**: Waku is not prone to e2e timing attack as there is no destination in waku if topics are used deliberately and wisely. In waku, the traffic pattern at all the relay nodes that are subscribed to the same topic is identical.  -->
<!-- However, we should be aware of the fact that the number of messages that a sender sends will be evident which I believe is the same in Tor.  -->

------------

Summary of my takes from https://github.com/zcash/zcash/issues/4902
## What ZCash needs from a secure transport layer or an Anonymous Communication Network
- Sending transactions between Zcash addresses to increase the performance of wallet apps. https://github.com/zcash/zcash/issues/4902#issuecomment-763715838
- Anonymous read from zcash chain (not quite sure about this one, it might be specific to zcash ACN project)
- A network layer that has the ability to store and forward messages, which would be really desirable for ACNs https://github.com/zcash/zcash/issues/4902#issuecomment-763715838
- A library for anonymous real-time and asynchronous messaging
- A low-fee and efficient solution that fits light nodes like mobile devices

## Considered and suggested approaches
- Signal over Tor
- Signal over Mixnet
- Tor
- Zcash ACN (Anonymous Communication Network), this one os on-chain solution and got critiques about its efficiency, cost, and delay 
- MixNet https://en.wikipedia.org/wiki/Mix_network
- Nym https://nymtech.net/nym-whitepaper.pdf. and https://nymtech.net/

## Security requirements 
It seems zcash project is seeking the following security objectives in their messaging network:
- Forward secrecy and limited message retention. If something is sensitive, people want it gone. https://github.com/zcash/zcash/issues/4902#issuecomment-763706787

## General 
Providing an ACN is to achieve a trade-off between bandwidth, latency, and anonymity.

## How Waku can help w.r.t. the Zcash requirements 
- Waku is an off-chain messaging solution
- It has the ability to store and forward messages (through the store protocol)

-----------------------------------


More on the use-cases of secure and anonymous transport layer:

In a project like zcash, the security of the transport layer is vital to deliver full node services to a light node in a privacy-preserving manner. And privacy and anonymity are defined around the unlinkability of a light node's Eth address to its IP.

- Anonymous information retrieval (read): This is normal that a light node is interested in data related to its Eth address or some limited number of addresses. As such, a full node responding to a light node can find a mapping between the light node's IP address and its Eth address. In the long round, full nodes can track light nodes' geographical movements based on their IP address change. 
- A similar issue appears in discovery services when nodes ID and IP address are stored on some central boot servers.  Nodes have to update the servers about their change of location by updating their IP address associated with their ID. As such, their history of locations will become available to the servers.
  
Tor has been deployed to obfuscate the mapping between the IP and Eth account, however, 
- Embedded devices are not compatible with Tor due to huge cryptographic overhead  
- There are other issues related to connectivity, not being able to find enough peer (IP mixers), increased latency, the bandwidth go down due to dropping peers 


**What can waku do?**
In the current architect of waku v2, the problem of Anonymous retrieval of information is related to the waku store protocol. I envision that Oblivious transfer and private information retrieval techniques can lead us to a solution, though, we should be careful about the cryptographic overhead. 
Another possibility is to set light nodes to listen to all the network traffic and cherry-pick what is intended for them, while not being involved in the relay process. This solution is not bandwidth-efficient. 

-----------------------------------

# Transport Privacy
- Sender anonymity: No global entity except the sender knows which entity owns the message
- Recipient Anonymity: No global entity except the receiver knows which entity received the message
- Participation Anonymity: No global entuty can discover which two entities are engaged in a conversation except the conversation participants.
- Unlnikability: No two protocol messages are atrributable to the same conversation unless by the conversation participants.
  
  ## Broadcast systems
  It provides 
  - recipient anonymity 
  - participation anonymity
  - unlinkability 
  - against all network attackers.
  Has an innate anonymous contact discovery as the requests for contact is ent to the network without the posterior knolwedge of the repient.
  ### Downsides
  - High bandwidth
  - No asynchronicity supports
  - Scalability issues
    - possible solutions, to cluster nodes into smaller broadcast groups at the cost of reduced anonymity set size
  - Attack on availability by Flooding
    - Existing solutions have issues:
      - requires monetary fees
      - PoW for sending messages which comes with computation requirements and message delays
  
  ## Onion Routing
  Example is the Tor protocol, provides 
  - sender anonymity 
  - participation anonymity
  - unlinkability 
  - against an attacker with limited scope.
- ### Downsides
- Global adversary can break anonymity by statistical analysis based on 
  - content size
  - Transmission direction
  - counts
  - timing
  
### Security measures:
  - adding random delays to transmission, the longer the delay the less statistical power
    - higher message delay
    - more storage requirement at the relays
    - Not useful for instant messaging
  - Saturating the bandwidth of all connections
    - Infeasible

Provides asynchronous communication by dedicated and online server (Tor hidden server) for each user.

-----------------------------------------

# Threat Models
Based on domain of knowledge, the following non-exclusive categories of adversary exist. Any collusion among the adversaries is perceivable. 
## Local adversary (passive (HbC), active (malicious))
An adversary with the control of local network
## Global adversary (passive (HbC), active (malicious))
An adversary with the control of a larger portion of the network e.g., ISPs.
## Service Providers
Any centralized service operator and aid the messaging system e.g., public key directories.

The end-point security is assumed, hence malware or hardware attacks are precluded.

-----------------------------------------

# Definitions
## Synchonicity
Asynchronous messaging protocol with store-and-forward model: Store nodes are used to buffer messages for the offline recipients. As such, the receiver does not have to be online at the same time as the sender. 
## Deniability/repudiability:  
  The high level idea in deniability in a messaging system is to resemble the day to day conversation.
  ### Message repudiation 
  A messaging system is repuriable/deniable if no one can provably attribute a message to its sender.
  ### Participation repudiation
   No one can prove one's participation in a conversion with some other party. 
No sign policy has been adopted by waku to achieve repudiability. 
<!-- TODO: We do not have to preclude signature usage entirely,  if the sginatures are not tied to partipants long-term keys, that should not harm anonymity. Though, inclusion of this field would require extra care at the application layer and the perceived anonymity relies on the upper level decisions. Deniable encryption can be a solution.-->
## Usability 
Human end users need to understand how to use the system securely and the effort required to do so must be acceptable for the perceived benefits. 
## Ease of Adoption
Requirements imposed by the underlying technology

-----------------------------------------
# Solution ideas
How to provide sender anonymity in waku as a broadcast system:
Querying nodes publish their request on a pubsub topic, and store nodes reply to that request with that given request id. 
Publisher nodes must be relay nodes, otherwise it is evident that they are the origin of the messages they publish but not relaying. Maybe it is good to dedicate a network for querying nodes i.e., light nodes combined with the store nodes. A query layer just handle queries for light nodes that is comprised of light nodes.

Every x minutes, each node drops its current connections and re-establishes new one. So that not eny pair of connections in the graph last longer than x minutes and preclude traffic analysis. It does not have to happen for the store nodes, those are system's backbone. 
There should be a directory service for all the available nodes. Each node id gets expired after x minutes automatically. New IDs get registered every x minutes or even longer, the new ids differ from the past ids. 

-----------------------------------------
# Resources

Sharing some relevant resources for the record:
- Unlinkable waku message format: https://github.com/vacp2p/rfc/issues/182
- Sphinx: A Compact and Provably Secure Mix Format
https://cypherpunks.ca/~iang/pubs/Sphinx_Oakland09.pdf
- SoK: Secure Messaging (An evaluation framework for the security, usability, and ease-of-adoption of secure messaging solutions)
 https://cacr.uwaterloo.ca/techreports/2015/cacr2015-02.pdf
