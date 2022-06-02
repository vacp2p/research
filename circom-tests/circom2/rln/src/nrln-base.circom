pragma circom 2.0.0;

include "./incrementalMerkleTree.circom";
include "../node_modules/circomlib/circuits/poseidon.circom";

template HasherAB() {
  signal input a;
  signal input b;
  signal output out;

  component hasher = Poseidon(2);
  hasher.inputs[0] <== a;
  hasher.inputs[1] <== b;

  out <== hasher.out;
}

template CalculateIdentityCommitment() {
    signal input secret;
    signal output out;

    component hasher = Poseidon(1);
    hasher.inputs[0] <== secret;

    out <== hasher.out;
}


template CalculateA0(limit) {
  signal input identity_secret[limit];
  signal output out;

  component hasher = Poseidon(limit);
  var i;
  for(i=0;i<limit;i++) {
    hasher.inputs[i] <== identity_secret[i];
  }

  out <== hasher.out;
}

template CalculateOutput(limit) {
  signal input a0;
  signal input identity_secret[limit];
  signal input epoch;
  signal input x;
  signal input rln_identifier;

  signal output out;
  signal output nullifier;

  signal degrees[limit];
  signal values[limit];
  component coeffs[limit];
  component nullifierHash = Poseidon(limit + 1);

  degrees[0] <== x;
  coeffs[0] = HasherAB();
  coeffs[0].a <== identity_secret[0];
  coeffs[0].b <== epoch;

  values[0] <== coeffs[0].out * degrees[0] + a0;
  nullifierHash.inputs[0] <== coeffs[0].out;

  var i;
  for(i = 1; i < limit; i++) {

    degrees[i] <== x * degrees[i - 1];

    coeffs[i] = HasherAB();
    coeffs[i].a <== identity_secret[i];
    coeffs[i].b <== epoch;

    values[i] <== coeffs[i].out * degrees[i] + values[i - 1];
    nullifierHash.inputs[i] <== coeffs[i].out;
  }

  component rln_identifier_hash = Poseidon(1);
  rln_identifier_hash.inputs[0] <== rln_identifier;

  nullifierHash.inputs[limit] <== rln_identifier_hash.out;

  out <== values[limit-1];
  nullifier <== nullifierHash.out;
}


template NRLN(n_levels, limit) {
    //constants
    var LEAVES_PER_NODE = 2;
    var LEAVES_PER_PATH_LEVEL = LEAVES_PER_NODE - 1;

    //private signals
    signal input identity_secret[limit];
    signal input path_elements[n_levels][LEAVES_PER_PATH_LEVEL];
    signal input identity_path_index[n_levels];

    //public signals
    signal input x; // x is actually just the signal hash
    signal input epoch;
    signal input rln_identifier;

    //outputs
    signal output y;
    signal output root;
    signal output nullifier;

    var i;
    var j;

    component A0 = CalculateA0(limit);
    for(i = 0; i < limit; i++) {
      A0.identity_secret[i] <== identity_secret[i];
    }

    component identity_commitment = CalculateIdentityCommitment();
    identity_commitment.secret <== A0.out;
    component inclusionProof = MerkleTreeInclusionProof(n_levels);
    inclusionProof.leaf <== identity_commitment.out;

    for (i = 0; i < n_levels; i++) {
      for (j = 0; j < LEAVES_PER_PATH_LEVEL; j++) {
        inclusionProof.path_elements[i][j] <== path_elements[i][j];
      }
      inclusionProof.path_index[i] <== identity_path_index[i];
    }

    root <== inclusionProof.root;

    component PX = CalculateOutput(limit);
    for (i = 0; i < limit; i++) {
      PX.identity_secret[i] <== identity_secret[i];
    }

    PX.epoch <== epoch;
    PX.a0 <== A0.out;
    PX.x <== x;
    PX.rln_identifier <== rln_identifier;

    y <== PX.out;
    nullifier <== PX.nullifier;

}
