# Secure Transfers with Noise


In this document we describe a compound protocol to enable two devices to mutually authenticate and securely exchange (arbitrary) information. 
It consists of two main subprotocols or *phases*:

- [Device Pairing](#Device-Pairing): the devices exchange and authenticate their long term device ID static keys;
- [Secure Transfer](#Secure-Transfer): the devices securely exchange in encrypted form information using key material obtained during a successful pairing phase.

## Device Pairing

In the pairing phase, a device `B` requests to be paired to a device `A`. Once the two devices are paired, the devices will be mutually authenticated and will share a Noise session within which they can securely exchange information.

The requests is made by exposing a QR code that, by default, has to be scanned by device `A`. 
If device `A` doesn't have a camera while device `B` does, [it is possible](#Rationale) to execute a slightly different pairing (with same security guarantees), where `A` is exposing a QR code instead.

### Employed Cryptographic Primitives

- `H`: the underlying hash function, i.e. SHA-256;
- `HKDF`: a key derivation function (based on SHA-256);
- `Curve25519`: the underlying elliptic curve for Diffie-Hellman (DH) operations.

### The `WakuPairing` Noise Handshake
The devices execute a custom handshake derived from `X1X1`, where they mutually exchange and authenticate their device static keys, i.e.

```
WakuPairing:
0.   <- eB              {H(sB||r), contentTopic}
     ...
1.   -> eA, eAeB        {H(sA||s)}   [auth_code]
2.   <- sB, eAsB        {r}
3.   -> sA, sAeB, sAsB  {s}

{}: payload,    []: user interaction
```


Beside the ephemeral key, all the information embedded in the QR code should be passed to the prologue of the Noise handshake (e.g. `H(sB||r)`, `contentTopic`, etc.).


### Protocol Flow
1. The device `B` exposes through a QR code a Base64 serialization of:
    - An ephemeral public key `eB`;
    - A `contentTopic` where the information exchange will take place. `contentTopic` follows [23/WAKU2-TOPICS](https://rfc.vac.dev/spec/23/#content-topics) specifications and is then of the form `/{application-name}/{application-version}/wakunoise/1/sessions-{shard-id}/{random-message-id}/proto` for a randomly generated `random-message-id`. `contentTopic` can be then serialized in compressed form as `{application-name}:{application-version}:{shard-id}:{random-message-id}`.
    - A commitment `H(sB||r)` for its static key `sB` where `r` is a random fixed-lenght value.

2. The device `A`:
    - scans the QR code;
    - obtains `eB`, `contentTopic`, `Hash(sB|r)`;
    - initializes the Noise handshake by passing `contentTopic` and `Hash(sB||r)` to the handshake prologue;
    - executes the pre-handshake message, i.e. processes the key `eB`;
    - executes the first handshake message over `contentTopic`, i.e. 
        - processes and sends a Waku message containing an ephemeral key `eA`; 
        - performs `DH(eA,eB)` (which computes a symmetric encryption key);
        - attach as payload to the handshake message a commitment `H(sA|s)` for `A`'s static key `sA`, where `s` is a random fixed-lenght value;
    - an 8-digits authorization code `auth_code` obtained as `HKDF(h) mod 10^8` is displayed on the device, where `h`is the handshake value obtained once the first handshake message is processed.

3. The device `B`:
    - subscribes to any message sent to `/{application-name}/{application-version}/wakunoise/1/sessions-{shard-id}/*` and locally filters only messages sent to `contentTopic`. If any, continues.
    - initializes the Noise handshake by passing `contentTopic` and `Hash(sB||r)` to the handshake prologue;
    - executes the pre-handshake message, i.e. processes its static key `eB`;
    - executes the first handshake message, i.e.
        - obtains from the received message a public key `eA`. If `eA` is not a valid public key, the protocol is aborted.
        - performs `DH(eA,eB)` (which computes a symmetric encryption key);
        - decrypts the commitment `H(sA||s)` for `A`'s static key `sA`.
    - an 8-digits authorization code `auth_code` obtained as `HKDF(h) mod 10^8` is displayed on the device, where `h`is the handshake value obtained once the first handshake message is processed.

4. Device `A` and `B` wait the user to confirm with an interaction (button press) that the authorization code displayed on both devices are the same. If not, the protocol is aborted.
    
5. The device `B`:
    - executes the second handshake message, i.e.
        - processes and sends his (encrypted) device static key `sB` over `contentTopic`;
        - performs `DH(eA,sB)` (which updates the symmetric encryption key);
        - attaches as payload the (encrypted) commitment randomness `r` used to compute `H(sB||r)`.

6. The device `A`:
    - subscribes to any message sent to `/{application-name}/{application-version}/wakunoise/1/sessions-{shard-id}/*` and locally filters only messages sent to `contentTopic`. If any, continues.
    - obtains from decrypting the received message a public key `sB`. If `sB` is not a valid public key, the protocol is aborted.
    - performs `DH(eA,sB)` (which updates a symmetric encryption key);
    - decrypts the payload to obtain the randomness `r`. 
    - Computes `H(sB||r)` and checks if this value corresponds to the commitment obtained in step 2. If not, the protocol is aborted.
    - executes the third handshake message, i.e.
        - processes and sends his (encrypted) device static key `sA` over `contentTopic`;
        - performs `DH(sA,eB)` (which updates the symmetric encryption key);
        - performs `DH(sA,sB)` (which updates the symmetric encryption key);
        - attaches as payload the (encrypted) commitment randomness `s` used to compute `H(sA||s)`.
    - Calls Split() and obtains two cipher states to encrypt inbound and outbound messages.
    

7. The device `B`:

    - locally filters new messages addressed to `contentTopic`. If any, continues.
    - obtains from decrypting the received message a public key `sA`. If `sA` is not a valid public key, the protocol is aborted.
    - performs `DH(sA,eB)` (which updates a symmetric encryption key);
    - performs `DH(sA,sB)` (which updates a symmetric encryption key);
    - decrypts the payload to obtain the randomness `s`. 
    - Computes `H(sA||s)` and checks if this value corresponds to the commitment obtained in step 6. If not, the protocol is aborted.
    - Calls Split() and obtains two cipher states to encrypt inbound and outbound messages.

### The `WakuPairing` for Devices without a Camera
In the above pairing handshake, the QR is by default exposed by device `B` and not by `A` because device `B` locally stores no relevant cryptographic material, so an active local attacker that scans the QR code first would only be able to transfer *his own* session information and get nothing from `A`. 

However, since the user confirms at the end of message `1` that the authorization code is the same on both devices, the role of handhsake initiator and responder can be safely swapped in message `0` and `1`. 

This allows pairing in case device `A` does not have a camera to scan a QR (e.g. a desktop client) while device `B` has.

The resulting handshake would then be:
```
WakuPairing2:
0.   -> eA              {H(sA||s), contentTopic}
     ...
1.   <- eB, eAeB        {H(sB||r)}   [auth_code]
2.   <- sB, eAsB        {r}
3.   -> sA, sAeB, sAsB  {s}

{}: payload,    []: user interaction
```

## Security Analysis (sketch)

### Assumptions
- The attacker is active, i.e. can interact with both devices `A` and `B` by sending messages over `contentTopic`.

- The attacker has access to the QR code, that is knows the ephemeral key `eB`, the commitment `H(sB||r)` and the `contentTopic` exposed by the device `B`.

- Devices `A` and `B` are considered trusted (otherwise the attacker will simply exfiltrate the relevant information from the attacked device).

- As common for Noise, we assume that ephemeral keys cannot be compromised, while static keys might be later compromised. However, we enforce in the pairing some security mechanisms (i.e. static key commitments) that will prevent some attacks which are possible when ephemeral keys are weak or get compromised.
 
### Rationale

- The device `B` exposes a commitment to its static key `sB` because:
    - if the private key of `eB` is weak or gets compromised, an attacker can impersonate `B` by sending in message `2` to device `A` his own static key and successfully complete the pairing. Note that being able to compromise `eB` is not contemplated by our security assumptions.
    - `B` cannot adaptively chose a static key based on the state of the Noise handshake at the end of message `1`, i.e. after the authentication code is confirmed. Note that device `B` is trusted in our security assumptions.
    - Confirming the authentication code after processing message `1` will ensure that no MitM can send a static key different than `sB`.


- The device `A` sends a commitment to its static key `sA` because:
    - `A` cannot adaptively chose a static key based on the state of the Noise handshake at the end of message `1`, i.e. after the authentication code is confirmed. Note that device `A` is trusted in our security assumptions.
    - Confirming the authentication code after processing message `1` will ensure that no MitM can send a static key different than `sA`.

- The authorization code is shown and has to be confirmed at the end of message `1` because:
    - an attacker that frontruns device `A` by sending faster his own ephemeral key, will be detected before  he's able to know device `B` static key `sB`;
    - it ensures that no MitM attacks will happen during *the whole* pairing handshake, since commitments to the (later exchanged) device static keys will be implicitly acknowledged by the authorization code confirmation;
    - it enables to safely swap the role of handshake initiator and responder (see above);

- Device `B` sends his static key first because:
    - by being the pairing requester, it cannot probe device `A` identity without revealing its own (static key) first. Note that device `B` static key and its commitment can be binded to other cryptographic material (e.g. seed phrase).

- Device `B` opens a commitment to its static key at message `2.` because:
    - if device `A` replies concluding the handshake according to the protocol, device `B` acknowledges that device `A` correctly received his static key `sB`, since `r` was encrypted under an encryption key derived from the static key `sB` and the genuine (due to the previous `auth_code` verification) ephemeral keys `eA` and `eB`.

- Device `A` opens a commitment to its static key at message `3.` because:
    - if device `B` doesn't abort the pairing, device `A` acknowledges that device `B` correctly received his static key `sA`, since `s` was encrypted under an encryption key derived from the static keys `sA` and `sB` and the genuine (due to the previous `auth_code` verification) ephemeral keys `eA` and `eB`.

- Device `A` and `B` subscribe to `/{application-name}/{application-version}/wakunoise/1/sessions-{shard-id}/*` and not to `contentTopic` because:
    - in this they don't leak to store nodes their interest for encrypted messages sent to `contentTopic`.


# Secure Transfer (sketch)

Once the handshake is concluded, sensitive information can be exchanged using the encryption keys agreed during the pairing phase. If more higher security guarantees are required, some [additional tweaks](#Additional-Possible-Tweaks) are possible.

In the following subsections we report the details of applications which are currently under development, mainly in order to implement [35/WAKU2-SESSION]().

However, the pairing and transfer phases descriptions are designed to be application-agnostic, and should be flexible enough to mutually authenticate and allow secure communication of two devices over a distributed network of Waku2 nodes.

## N11M session management mechanism
In this scenario, one of Alice's devices is already communicating with one of Bob's devices within an active Noise session, e.g. after a successful execution of a Noise handshake.

Alice and Bob would then share some cryptographic key material, used to encrypt their communications. According to [37/WAKU2-NOISE-SESSIONS](https://rfc.vac.dev/spec/37/) this information consists of:
- A `session-id` (32 bytes)
- Two cipher state `CSOutbound`, `CSInbound`, where each of them contains
- an encryption key `k` (2x32bytes)
- a nonce `n` (2x8bytes)
- (optionally) an internal state hash `h` (2x32bytes)
        
for a total of **170 bytes** of information.

In a [`N11M`](https://rfc.vac.dev/spec/37/#the-n11m-session-management-mechanism) session mechanism scenario, all (synced) Alice's devices that are communicating with Bob, share the same Noise session cryptographic material.
Hence, if Alice wishes to add a new device, she must securely transfer a copy of such data from one of her device `A` to a new device `B` in her possession.

In order to do so:
- she pairs device `A` with `B` in order to have a Noise session between them; 
- she securely transfers within such session the 170 bytes serializing the active session with Bob;
- she manually instantiates in `B` a Noise session with Bob from the received session serialization.


# Additional Possible Tweaks

## Randomized Rekey

The Noise framework supports [`Rekey()`](http://www.noiseprotocol.org/noise.html#rekey), in order to update encryption keys *"so that a compromise of cipherstate keys will not decrypt older* \[exchanged\] *messages"*. However, if a certain cipherstate key is compromised, it will become possible for the attacker not only to decrypt messages encrypted under that key, but also all those messages encrypted under any following new key obtained through a `Rekey()`.

This can be mitigated by:
- keeping the full Handhshake State even after the handshake is complete (by specification a call to `Split()` should delete the Handshake State)
- continuing updating the Handshake State by processing every after-handshake exchanged message (i.e. the `payload`) according to the Noise [processing rules](http://www.noiseprotocol.org/noise.html#processing-rules) (i.e. by calling `EncryptAndHash(payload)` and `DecryptAndHash(payload)`);
- adding to each (or every few) message exchanged in the transfer phase a random ephemeral key `e` and perform Diffie-Hellman operations with the other party's ephemeral/static keys in order to update the underlying CipherState and recover new random inbound/outbound encryption keys by calling `Split()`.

In short, the transfer phase would look like (but not necessarily the same as):

```
TransferPhase:
   -> eA, eAeB, eAsB  {payload}
   <- eB, eAeB, sAeB  {payload}
   ...
   
{}: payload
```

## Content Topic Derivation

To reduce metadata leakage and increase devices's anonymity over the p2p network, [35/WAKU2-NOISE](https://rfc.vac.dev/spec/37/#session-states) suggests to use some common secrets `ctsInbound, ctsOutbound` (e.g. `ctsInbound, ctsOutbound = HKDF(h)` where `h` is the handshake hash value of the Handshake State at some point of the pairing phase) in order to frequently and deterministically change `contentTopic` of messages exchanged during the pairing and transfer phase - ideally, at each message or round trip communication. 

Given the proposed content topic format
```
/{application-name}/{application-version}/wakunoise/1/sessions-{shard-id}/{random-message-id}/proto
```
the `ctsInbound` and `ctsOutbound` secrets can be used to iteratively generate the `{random-message-id}` field of content topics for inbound and outbound messages, respectively. 

The derivation of `{random-message-id}` should be deterministic only for communicating devices and independent from message content, otherwise lost messages will prevent computing the next content topic. A possible approach consists of computing the `n`-th `{random-message-id}` as `H( ctsInbound || n)`, where `n` is serialized as `uint64`.

In this way, sender and recipient device can keep updated a buffer of `random-message-id` to sieve from their subscription to `/{application-name}/{application-version}/wakunoise/1/sessions-{shard-id}/*` (i.e., the next 50 not yet seen), and become then able to further identify if one or more messages were eventually lost/not-yet-delivered during the communication.

We note that this approach brings the advantage that devices can efficiently identify messages addressed to them when filtering messages from their subscription to

We note that since the `ChaChaPoly` cipher used to encrypt messages supports additional data, an encrypted payload can be further authenticated by passing the `contentTopic` as additional data to the encryption/decryption routine, so that an attacker would be unable to send an authenticated Waku message over a content topic agreed during the pairing phase.


# Future work: n-to-1 pairing
The above protocol pairs a single device `A` with `B`, creating the conditions for a secure transfer. However, we would like to efficiently address scenarios (e.g. the [NM](https://rfc.vac.dev/spec/37/#the-nm-session-management-mechanism) session managment mechanism) where a device `B` is paired with multiple devices `A1, A2, ..., An`, which were, in turn, already paired two-by-two. A naive approach requires `B` to be paired with each of such devices, but exposing/scanning `n` QRs is clearly impractical for a large number of devices. 

As a future work we wish to desing a n-to-1 pairing protocol, where only one out of `n` devices scans the QR exposed by the pairing requester device and the latter can efficiently (in term of exchanged messages) be securely paired to all of them. 

A possible approach requires that all already paired devices share a list of *pairing key bundles*, that device `B` can securely receive from the device it has been paired with and use to complete multiple pairings, in a similarly fashion as X3DH.