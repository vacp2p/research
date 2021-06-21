# Probelm Definition

This document is going to provide a comparison between  Tor and Waku. The ["Waht is Tor"](#what-is-tor) section presents a quick overview of the Tor, and can be skipped for those that are already familiar.  


# What is Tor

As stated in the [Tor specifications](https://gitweb.torproject.org/torspec.git/tree/tor-spec.txt#n142), Tor is a distributed overlay network designed to anonymize low-latency TCP-based applications such as web browsing, secure shell, and instant messaging. Clients choose a path through the network and build a `circuit`, in which each node (or `onion router `or `OR`) in the path knows its predecessor and successor, but no other nodes in the circuit.  Traffic flowing down the circuit is sent in **fixed-size** `cells`, which are unwrapped by a symmetric key at each node (like the layers of an onion) and relayed downstream. Tor only works for TCP streams and can be used by any application with SOCKS support.

It comes in 3 main steps:
- The Tor client fetches a list of Tor nodes (Onion routers) from a directory server. Onion routers are voluntarily operated servers around the world that are listed publicly in a directory and there is no concern finding out their identity.
- The Tor client picks a random path to the destination server. The path includes three hops. The client negotiates a separate set of encryption keys for each hop along the circuit to ensure that each hop can't trace these connections as they pass through. The message is then encrypted  through **3 layers of encryption**. 
  - For example consider A sending message `M` to B through R1-R3 i.e., A → R3 -> R2 -> R1 -> B, the message `M` is encrypted with 3 keys, in 3 layers as `E(k3, E(k2, E(k1, M)))` where each key is only known to one of the intermediate nodes.
  - Routing nodes only need to know their preceding and exceeding connection, but not the sender of the message. 
  - Once a circuit has been established, many kinds of data can be exchanged and several different sorts of software applications can be deployed over the Tor network.
  - For efficiency, the Tor software uses the same circuit for connections that happen within the same ten minutes or so. Later requests are given a new circuit, to keep people from linking your earlier actions to the new ones.
  - No header is added to the message, otherwise it would be lot easier that how far the message is from its destination. 

- Tor's users employ this network by connecting through a series of **virtual tunnels** rather than making a direct connection, thus allowing both organizations and individuals to share information over public networks without compromising their privacy.
- Tor is the implementation of Onion routing which enables us to communicate anonymously over the internet
- The more people use the Tor network the stronger it gets. As it is easier to hide in a crowd of people that look exactly the same


Tor Messages are called cells, and are each 512 bytes long 

Routers are talking to many users and as an intermediary for the conversation, like the first node, second nodes, the thrid node, the exit node, and it does not really know which one it is. 

So it is a not an easy job to correlate the traffics and figure out what someone did job to


## Security consideration
Tor is all about **Transport Security** and there is no anonymity gaurantee about the data that is sent by the user over Tor e.g., an attacker may sniff the last connection in thr Tor circuit to the destination server, and sees someone's username and password in clear. It is up to the user to use TLS or HTTPS for the connection. What is transported is exactly a https request and reply that goes through Tor instead of the ISP router.


## security features
Below is the the list of  the security features that Tor provides, however, the essence of all these features are two things:
1.  Tor hides (or make it difficult to know) the two end of communication i.e., who is talking to whom
2. It preserves meta data protection that include - Users Real identity
   - Precise location 
   - OS
   - The browser used to surf the web
This means, to make a fair comparison with waku, we need to know whether we can achieve these two major features or not and how.

- Protects against Traffic analysis by concealing headers of Internet data packets:
How does traffic analysis work? Internet data packets have two parts: a data payload and a header used for routing. The data payload is whatever is being sent, whether that's an email message, a web page, or an audio file. Even if you encrypt the data payload of your communications, traffic analysis still reveals a great deal about what you're doing and, possibly, what you're saying. That's because it focuses on the header, which discloses source, destination, size, timing, and so on.

Protecting against traffic analysis results means no one knows who you are talking to. This means:
- **BROWSE FREELY** Tor is a censorship circumvention tool, allowing its users to reach otherwise blocked destinations or content. One reason for that is the pool of volunteer-run servers known as Tor relays.
- **DEFEND AGAINST SURVEILLANCE** Tor Browser prevents someone watching your connection from **knowing what websites you visit.** All anyone monitoring your browsing habits can see is that you're using Tor.
-  **MULTI-LAYERED ENCRYPTION**: The traffic is relayed and encrypted three times as it passes over the Tor network. The network is comprised of thousands of volunteer-run servers known as Tor relays. Though, this is not exactly for the confidentiallity but more for the anonymity. The final data that is passed to the final destination may still be unencrypted and compromised privacy. 
- **BLOCK TRACKERS** Tor Browser isolates each website you visit so third-party trackers and **ads can't follow you**. Any **cookies automatically clear** when you're done browsing. Cannot compare this part with waku as I am not sure about the low level details of performing advertising in waku.
- **RESIST FINGERPRINTING** Tor Browser aims to make all users look the same, making it **difficult** for you to be fingerprinted based on **your** **browser** and **device information**.



## Security Vulnerabilities
The tor network does load sharing: to protect against DoS attack. To load a single router and anyone talking to that router will have a problem.The circuits are restablished about every 10 minutes
It is adaptive and can take a different tour


What if some of the third parties are controlling these nodes:
Maybe government agencies want to know what is going on
They control these nodes with the hope that they eventually control A and B
That is why they are called the guard nodes, because you trust them and you don't pick them randomly


- Weakness of Tor that is unsolvable: If the adversary is the front node and the exit node on the circuit, then it can figure out what is going on. - Weakness 2,end to end timing attack: Tor does not provide protection against end-to-end timing attacks: If your attacker can watch the traffic coming out of your computer, and also the traffic arriving at your chosen destination, he can use statistical analysis to discover that they are part of the same circuit.

- Weakness 2, traffic analysis: imagine you have got the time signature of the messages sent by a single client. The incomming ttraffic to the destination server will be a mess of lots of messages. But imagine that you can find the key points that match up with what I sent in. Then it can be used to deanonymize people
If messages are of the certain size with a certain tempo, and figure out that the same messages came out another side of the network

## Performance Concerns

Tor routers may be distant and you may get delay till your message get to the destination.

# Anonymity levels
Anonymity can be analyzed from various levels. Below is a broad classification of such: 
- Communication anonymity against a third person, in this anonymity level, the communication must stay anonymous in the eyes of a third person. Neverthelss, the sender and receiver may know each other and have no concern in this regard.
- Sender anonymity (against the network and the receiver):  For example when you want to hide the fact you are visiting a website
- Receiver anonymity, where there is a publisher  with public identity lets say broadcasting political news, and the subscribers want to hide their interest in that topic yet be able to have access to the news

# Waku
In waku, the relay protocol constitutes the transport layer. The objective would be to protect anonymity in this layer isolated from other available protocols. That is, we rule out the anonymity concerns related to the filter or store protocols. As in those protocols, some level of trust between the service provider and consumer is expected. Further on the anonymity and trust requirement of the store and the filter protocol can be found in their respective specs. 

In the following, I am considering nodes with relay protocol mounted and involve both as relayer and as publisher. Later, we can extend the security analysis for other types of the nodes like light nodes and also consider inclusion of other protocols.

## Metadata protection
One source of information for the attacker in breaking anonymity is the metadata that is included inside the transported data. Such information can be included to aid the transportation or can be some application level information that are in clear. The presence of any personally identifiable information can help the attacker identify the sender and the receiver of the message. 

Lets first have a look at the structure of waku messages and the headers used while transporting them using GossipSub protocol (i.e., Waku-Relay. 
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
In order to preserve anonymity, the relay-protocol follow strict no sign policy which means the `seq#`, `from`, `sign` and `key` fields are omitted as they indicate info related to the sender of the message.

### Open questions
The use of IP addresses in the GossipSub protocol is not clear to me, I need to make sure that the sender's IP of the sender does not get shared/used during the routing process.

There are two other fields of `ContentTopic` and `topic` used in GossipSub routing which can cause anonymity issues. Why so?
In order to address anonymity, we should understand how the two ends of communication find each other? 
The current approach is that two end of communications (more precisely the publishers and subscribers) find each other through pubsub topics i.e, the `topic` field. AFAIK, in the Status app also relies on the pubsub topics to distinguish between different 1:1 or group chats. That is each 1:! chat is associated with a distinct chat id used as the pubsub topic. 

This means in order to preserve anonymity we need to hide the relation between the topics and their publishers and subscribers i.e., to preserve publisher-topic anonymity and subscriber-topic anonymity.
However, consider the case that we use distinct pubsub topics for each 1:1 or private group chats. For those specific pubsub topics, there will be a limited number of relay nodes subscribed to that pubsub topic hence identifying them would be easy. Moreover, that would be easy to find out whether there is an active conversation between two parties. Lets say if an attacker eavesdrops the network traffic of two victim nodes and realises that they are actively relaying messages of pubsub topic X, then it can infer they are communicating which each other. 

In the light of this observation, we need to have a large number of relay nodes involved in the pubsub topic over which nodes communicate. This means we need to have a  single topic that would result in many relay nodes. It is somewhat similar to what Tor requires, it says that the more Tor realyers would result in better anonymity. As such, I suggest to use waku content topic to manage direct or group messaging. 

## No payload protection

You need to use **protocol-specific support software** if you don't want the sites you visit to see your identifying information. This exists in Tor browser, For example, you can use Tor Browser while browsing the web to withhold some information about your computer's configuration.

- If your attacker can watch the traffic coming out of your computer, and also the traffic arriving at your chosen destination, he can use statistical analysis to discover that they are part of the same circuit.


In waku there are two ways to spot the two ends of communication:
- Via Publishing: If Alice and Bob both publish to the same topic
- Via joining the topic mesh: If Alice and Bob are both part of the same topic mesh
  

The act of publishing to a topic is theoretically protected and is anonymous, That is by hijacking a link and getting to see message m is set from node A to B, cannot jusge the author of the message. Nevertheless, a more powerful adversary can analyze the delay  by which the message arrives at other nodes of the netwrok. The one with minimum delay is potentially the owner of the message. 
For example in the chanin of nodes A->B->C->D, if A publishes and owns a messages, then B is the first one the receives it and D is the last one. Such time difference can help identifying the owner of the message. Likewise, the other part of the communocation can be spot. Hence, the anonymity gets violated.

Neverthelss, this is an application layer concern and not directly related to the waku protocol stack. A topic generation method that provides forward secrecy and randmozes the topic for each message transmission can solve the issue in a 1:1 chat. 

## Topic randmization
## Topic sharding 
One way is to confuse the attacker about the actual particpants of a pubsub topic.

# Waku advantages
One potential advantage of using waku is that it is computationally lighter than Tor and does not require multiple encryption and decryption. Thi would also lower the message transmission delay.

Another advantage is the lighter key management where  the sender does not have to establish shared keys with all the intermediate routers (as apposed to the Tor).


No **end-to-end timing attack**: There is no destination in waku if topics are used deliberately and wisely. In waku, the traffic pattern at all the relay nodes that are subscribed to the same topic is identical. However, we should be aware of the fact that the number of messages that a sender sends will be evident which I believe is the same in Tor. 