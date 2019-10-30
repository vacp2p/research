# Semaphore experiments

Based on https://github.com/kobigurk/semaphore but only focusing on the core circom circuits, not contracts or on chain orchestration.

See https://github.com/iden3/snarkjs for a quick start.

According to https://github.com/kobigurk/semaphore#zksnark-statement:

```
The statement assures that given public inputs:

    signal_hash
    external_nullifier
    root
    nullifiers_hash

and private inputs:

    identity_pk
    identity_nullifier
    identity_trapdoor
    identity_path_elements
    identity_path_index
    auth_sig_r
    auth_sig_s

the following conditions hold:

    The commitment of the identity structure (identity_pk, identity_nullifier, identity_trapdoor) exists in the identity tree with the root root, using the path (identity_path_elements, identity_path_index). This ensures that the user was added to the system at some point in the past.
    nullifiers_hash is uniquely derived from external_nullifier, identity_nullifier and identity_path_index. This ensures a user cannot broadcast a signal with the same external_nullifier more than once.
    The message (external_nullifier, signal_hash) is signed by the secret key corresponding to identity_pk, having the signature (auth_sig_r, auth_sig_s). This ensures that a state of the contract having a specific external_nullifier, ensuring no double-signaling.
```

So we need to setup these identity_* and auth_* inputs.
