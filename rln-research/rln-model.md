- [Abstract](#abstract)
- [RLN System Model](#rln-system-model)
  - [1. SetUp](#1-setup)
  - [2. Registration](#2-registration)
  - [3. Signalling per epoch](#3-signalling-per-epoch)
- [The design requirements](#the-design-requirements)
- [Building blocks](#building-blocks)
- [Security Guarantees](#security-guarantees)
- [Security concerns](#security-concerns)
## Abstract

The following is the summary of how RLN works. This writeup combines the Semaphore paper and the RLN doc (some parts were missing in [RLN doc](https://hackmd.io/tMTLMYmTR5eynw2lwK9n1w?both) that are borrowed from [Semaphore](https://github.com/appliedzkp/semaphore/blob/master/spec/Semaphore%20Spec.pdf)).
The system consists of a set of peers and a smart contract. The local operations of each party for each phase as well as the exact data flows are described. 

## RLN System Model
### 1. SetUp

A membership contract on the blockchain with the following state variables
-  a Merkle Tree (`MT`) of the registered users 
- a list of submitted nullifiers as `nullifier_map`
- a list of submitted signals as `signal_map`

Peer (user)
-  to generate a secret key `a_0` as its identity

### 2. Registration

Peer

- to submit the commitment of `a_0`  i.e., `h(a_0)` together with a deposit to the membership contract and to obtain the insertion path `auth_path` 

Membership Contract

-  to insert `h(a_0)` to `MT`

### 3. Signalling per epoch
Peer
- Inputs: (`signal`, `a_0`, `auth_path`, `epoch`)
- To create a polynomial of degree 1 with the following coefficients

  - `A_epoch(x)= a_0 + a_1 x`
  - `a_1= h (a_0, epoch)`

- Given the peer's `signal`, the followings are submitted to the contract
  - `signal`
  - `external_nullifier= epoch`
  - `internal_nullifier = h(a_1) `
  - `share_x =  h(signal)`
  - `share_y = A_epoch(share_x)`
  - `proof ` (`proof` is generated using ZKSNARKs for some given circuit)

Contract 
- Verify the `proof` using the `MT.root`
- Check the presence of the `internal_nullifier` in the `nullifier_map`, if a duplicate is found for `internal_nullifier `, perform slashing, otherwise, add the `signal` to the `signal_map`, and `internal_nullifier` to the `nullifier_map`.
- 
------
## The design requirements

1. To verify proofs, the membership tree `MT.root` must be known by the verifier
2. To spot a double singling, the `nullifier_map` must also be known
3. A smart contract on the blockchain is required to enforce a global consistent view of the registration tree `MT` and `nullifier_map`
4. To preserve anonymity, peers need to keep their `auth_proof` always updated with the latest tree root (this requirement is still under discussion with the RLN group)

-------
## Building blocks

1. Peer: KeyGen()--> a_0
2. Peer: PolyGen(a_0,epoch) --> the description of the line A(x) (Not really a building block but needed)
3. Peer: ZKProofGen(secret: (a_0, auth_path), public: (epoch, signal, A(x)) ) --> proof
4. Verifier: ZKProofVerify(MT.root, signal, external_nullifier,  internal_nullifier, share_x, share_y, proof )-->True / False
5. Verifier: contains(nullifier_map, internal_nullifier) --> True (together with the information about the duplicate i.e., share_x, share_y) / False
6. Verifier Slash(share1_x, share1_y , share2_x , share2_y) --> a_0

--------
## Security Guarantees

1. Per each peer with a secret registered in the registration tree, there will be no more than one signal at each epoch unless the secret gets revealed and the peers gets slashed 
   
--------
## Security concerns

1. Each peer can register multiple times and use her cumulative quotas for signalling. The deposit required per account may disincentivize multiple registration but does not eliminate it entirely. As the result, the system will be still subject to spam and spammers with enough wealth.
2. Inline with item 1, there is no registration policy in place, everyone can join
3. Forward secrecy does not hold; that is as soon as a user attempts double signalling, her prior signals attached to the same secret can be identified and linked.