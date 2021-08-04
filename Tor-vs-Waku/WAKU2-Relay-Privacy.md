Below, we analyze the security of the transport protocol of waku v2 i.e., WAKU2-Relay. In this analysis, we preclude the metadata included in the WakuMessage, as the unit of data transported using WAKU2-Relay. The waku message is treated as a black box. A privacy-respected application can provide the utmost level of security by encrypting the waku message before transportation.  
The analysis of the metadata included in the WakuMessage will fall into the "conversational security" and deserves a separate issue. 

#  Required Privacy Features in a Private Trasnport Protocol
- Sender anonymity: No global entity except the sender knows which entity owns the message
- Recipient Anonymity: No global entity except the receiver knows which entity received the message
- Participation Anonymity: No global entity can discover which two entities are engaged in a conversation except the conversation participants.
- Unlinkability: No two protocol messages are attributable to the same conversation unless by the conversation participants.

# Threat Models
Based on the domain of knowledge, the following non-exclusive categories of adversary exist. Any collusion among the adversaries is perceivable. 
- Local adversary (passive (HbC), active (malicious)): An adversary with the control of local network
- Global adversary (passive (HbC), active (malicious)): An adversary with the control of a larger portion of the network e.g., ISPs.
- Service Providers: Any centralized service operator and aid the messaging system e.g., public key directories.

In this treat model, the end-point security is assumed, hence malware or hardware attacks are precluded.
Also, the adversary has **NO** **Auxiliary** **Information** (background about users). The inclusion of such information would open up all sorts of inference attacks and a countermeasure demands research techniques like differential privacy which is going to be left out of scope for now.

# WAKU2 Relay analysis

**Recipient Anonymity**: No global entity except the receiver knows which entity received the message 
- Level of privacy: K-anonymity
- Adversarial model: it holds against a global adversary 
- Details: The number of topics transported within the same mesh determines recipient anonymity, e.g., if the mesh is used to transport k topics then the recipient anonymity of all the nodes within that mesh is k-Anonymity. That is, every message in that mesh belongs to a participant with 1/k probability.
  - The anonymity level can be increased by generalizing the topics hence supporting more topics within a single mesh
  - Increasing anonymity of recipient comes with the bandwidth penalty for all the participants i.e., nodes have to spend their bandwidth to relay messages not within their interests

The same analysis as above applies to **Participation Anonymity**.

**Sender anonymity:** No global entity except the sender knows which entity owns the message
- Adversarial model: local and global 
- No sender anonymity against even local adversary
- Attack scenario: The adversary can eavesdrop on the incoming and outgoing traffic of a target node and realizes that some messages appear in the outgoing traffic but not in the incoming traffic. Those messages are the ones originated by that node. 


**Unlinkability:** No non-global entities except the conversation participants can discover that two protocol messages belong to the same conversation.
- Level of privacy: K-anonymity
- Adversarial model: Global 
- The number of topics transported within the same mesh determines unlinkability level, e.g., if the mesh is used to transport k topics then for every two messages m1 and m2 transported within that mesh, the probability that these two belong to the same conversation is 1/k 
  - The anonymity level can be increased by generalizing the topics hence supporting more topics within a single mesh
  - Increasing anonymity of recipient comes with the bandwidth penalty for all the participants i.e., nodes have to spent their bandwidth to relay messages, not within their interests 


# Tor
 Tor protocol provides the following privacy properties, however against an attacker with limited scope.
  - sender anonymity 
  - participation anonymity
  - unlinkability 
 
 A global adversary can break anonymity by statistical analysis based on 
  - content size
  - Transmission direction
  - counts
  - timing

For example:
- End-to-end timing attack: Tor does not protect against end-to-end timing attacks; If the attacker can watch the traffic coming out of your computer, and also the traffic arriving at your chosen destination, he can use statistical analysis to discover that they are part of the same circuit.

- Traffic analysis: imagine you have got the time signature of the messages sent by a single client. The incoming traffic to the destination server will be a mess of lots of messages. But imagine that you can find the key points that match up with what the client sent in. Then it can be used to deanonymize that client.
