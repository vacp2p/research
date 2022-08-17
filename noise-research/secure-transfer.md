# Secure Transfers with Noise


## Overview (sketch)

Two devices exchange sensitive information in two independent phases:

- [Device Pairing](#Device-Pairing): two devices exchange their long term device ID static keys;
- [Secure Transfer](#Secure-Transfer): information is securely exchanged in encrypted form using key material obtained during a successful Pairing phase.

## Device Pairing

In the pairing phase, a device `B` requests to be paired to a device `A`.

The requests is made by exposing a QR code that has to be scanned by device `A`. 
If device `A` doesn't have a camera but device `B` does, [it is possible](#Rationale) to execute a slightly different pairing with same security guarantees but where `A` exposes a QR code instead.

### Employed Cryptographic Primitives

- `H`: the underlying hash function, i.e. SHA-256;
- `HKDF`: a key derivation function (based on SHA-256);
- `Curve25519`: the underlying elliptic curve for DH operations.

### The Noise Handshake
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
    - An ephemeral public key `eB`
    - A `contentTopic` where the information exchange could take place
    - A commitment `H(sB||r)` for its static key `sB` where `r` is a random fixed-lenght value.

2. The device `A`:
    - scans the QR code;
    - obtains `eB`, `contentTopic`, `Hash(sB|r)`;
    - initializes the Noise handshake by passing `contentTopic` and `Hash(sB||r)` to the handshake prologue;
    - executes the pre-handshake message, i.e. processes the key `eB`;
    - executes the first handshake message over `contentTopic`, i.e. 
        - processes and sends an ephemeral key `eA`; 
        - performs `DH(eA,eB)` (which computes a symmetric encryption key);
        - attach as payload to the handshake message a commitment `H(sA|s)` for `A`'s static key `sA`, where `s` is a random fixed-lenght value;
    - an 8-digits authorization code `auth_code` obtained as `HKDF(h) mod 10^8` is displayed on the device, where `h`is the handshake value obtained once the first handshake message is processed.

3. The device `B`:
    - listens for new messages on `contentTopic`. If any, continues.
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
    - listens for new messages on `contentTopic`. If any, continues.
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

    - listens for new messages on `contentTopic`. If any, continues.
    - obtains from decrypting the received message a public key `sA`. If `sA` is not a valid public key, the protocol is aborted.
    - performs `DH(sA,eB)` (which updates a symmetric encryption key);
    - performs `DH(sA,sB)` (which updates a symmetric encryption key);
    - decrypts the payload to obtain the randomness `s`. 
    - Computes `H(sA||s)` and checks if this value corresponds to the commitment obtained in step 6. If not, the protocol is aborted.
    - Calls Split() and obtains two cipher states to encrypt inbound and outbound messages.

## Security Analysis (sketch)

### Assumptions
- The attacker is active, i.e. can interact with both devices `A` and `B` by sending messages over `contentTopic`.

- The attacker has access to the QR code, that is knows the ephemeral key `eB`, the commitment `H(sB||r)` and the `contentTopic` exposed by the device `B`.

- Devices `A` and `B` are considered trusted (otherwise the attacker will simply exfiltrate the relevant information from the attacked device).

- As common for Noise, we assume that ephemeral keys cannot be compromised, while static keys might be later compromised. However, we enforce in the pairing some security mechanisms (i.e. static key commitments) that will prevent some attacks which are possible when ephemeral keys are weak or get compromised.
 
### Rationale
- The QR is by default exposed by device `B` and not by `A` because:
    - device `B` locally stores no relevant cryptographic material, so an active local attacker that scans the QR code first would only be able to transfer *his own* session information and get nothing from `A`. However,
    - since the user confirms at the end of message `1` that the authorization code is the same on both devices, the role of handhsake initiator and responder can be safely swapped in message `0` and `1`. **This allows pairing in case device `A` does not have a camera to scan a QR (e.g. a desktop client) while device `B` has.** The resulting handshake would be:
```
WakuPairing2:
0.   -> eA              {H(sA||s), contentTopic}
     ...
1.   <- eB, eAeB        {H(sB||r)}   [auth_code]
2.   <- sB, eAsB        {r}
3.   -> sA, sAeB, sAsB  {s}

{}: payload,    []: user interaction
```

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
  
 


# Secure Transfer (sketch)

## Use cases (TBD)

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


# Open problems and future work
The above protocol pairs a single device `A` with `B`, however we have scenarios (e.g. the [NM](https://rfc.vac.dev/spec/37/#the-nm-session-management-mechanism) session managment mechanism) where we need to pair device `B` with multiple devices `A1, A2, ..., An`, which are already paired two-by-two. A naive approach requires `B` to be paired with each of such devices, but exposing/scanning `n` QRs is clearly impractical for a large number of devices. 

As a future work we need to desing a n-to-1 pairing protocol, where only one out of `n` devices scans the QR exposed by the pairing requester device and the latter can efficiently (in term of exchanged messages) be securely paired to all of them. A possible approach consists in sharing among all already paired devices a list of key bundles that device `B` can get from the device with which is executing the pairing, that can allow it to be paired in 0.5 RTT.