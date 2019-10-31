const crypto = require('crypto');
const fs = require('fs');
const zkSnark = require('snarkjs');
const circomlib = require('circomlib');
const web3Utils = require('web3-utils');
const ethers = require('ethers');
const SMT = require('semaphore-merkle-tree');

const {stringifyBigInts, unstringifyBigInts} = require("snarkjs/src/stringifybigint.js");
//const {stringifyBigInts, unstringifyBigInts} = require("./node_modules/snarkjs/src/stringifybigint.js");
const asciiToHex = web3Utils.asciiToHex;
const bigInt = zkSnark.bigInt;
const eddsa = circomlib.eddsa;
const mimcsponge = circomlib.mimcsponge;

// Utils

function pedersenHash(ints) {
    const p = circomlib.babyJub.unpackPoint(circomlib.pedersenHash.hash(Buffer.concat(
        ints.map(x => x.leInt2Buff(32))
    )));
    return bigInt(p[0]);
}

beBuff2int = function(buff) {
    let res = bigInt.zero;
    for (let i=0; i<buff.length; i++) {
        const n = bigInt(buff[buff.length - i - 1]);
        res = res.add(n.shl(i*8));
    }
    return res;
};

// XXX: stringifyBigInts etc probably more robust

// Dealing with JSON BigInt serialization/deserialization
function stringifyReplacer(key, value) {
    if (typeof value === 'bigint') {
        return value.toString() + 'n';
    } else {
        return value;
    }
}

function parseReviver(key, value) {
    if (typeof value === 'string' && /^\d+n$/.test(value)) {
        return BigInt(value.slice(0, -1));
    }
    return value;
}

function serialize(value) {
    return JSON.stringify(value, stringifyReplacer);
}

function deserialize(json_str) {
    return JSON.parse(json_str, parseReviver);
}

function generate_identity() {
    const private_key = crypto.randomBytes(32).toString('hex');
    const prvKey = Buffer.from(private_key, 'hex');
    const pubKey = eddsa.prv2pub(prvKey);

    // XXX: Right, so just some random bytes?
    const identity_nullifier = '0x' + crypto.randomBytes(31).toString('hex');
    const identity_trapdoor = '0x' + crypto.randomBytes(31).toString('hex');
    console.log(`generate identity from (private_key, public_key[0], public_key[1], identity_nullifier): (${private_key}, ${pubKey[0]}, ${pubKey[1]}, ${identity_nullifier}, ${identity_trapdoor})`);

		const identity_commitment = pedersenHash([bigInt(circomlib.babyJub.mulPointEscalar(pubKey, 8)[0]), bigInt(identity_nullifier), bigInt(identity_trapdoor)]);

    console.log(`identity_commitment : ${identity_commitment}`);
    const generated_identity = {
        private_key,
        identity_nullifier: identity_nullifier.toString(),
        identity_trapdoor: identity_trapdoor.toString(),
        identity_commitment: identity_commitment.toString(),
    };

    return generated_identity;
}

// Using Groth

// 1. Compile circuit with circom:
// circom snark/circuit.circom -o build/circuit.json
const circuitDef = deserialize(fs.readFileSync("build/circuit.json", "utf-8"));
const circuit = new zkSnark.Circuit(circuitDef);

// 2. Inspect circuit with e.g.:
// circuits.nConstraints

// 3. Perform setup - only done once
function performSetup(circuit) {
    const setup = zkSnark.groth.setup(circuit);
    /// XXX run this again - takes 1h so do at home
    fs.writeFileSync("myCircuit.vk_proof", JSON.stringify(stringifyBigInts(setup.vk_proof)), "utf8");
    fs.writeFileSync("myCircuit.vk_verifier", JSON.stringify(stringifyBigInts(setup.vk_verifier)), "utf8");

//    fs.writeFileSync("build/proving_key.json", serialize(setup.vk_proof), "utf8");
//    fs.writeFileSync("build/verification_key.json", serialize(setup.vk_verifier), "utf8");
    console.log("Toxic waste:", setup.toxic);  // Must be discarded.
}
// TODO: Conditionally run if file exists
//performSetup(circuit);
//console.log("Done, exiting");
//process.exit(1);
// TODO: run this to get new proving key with stringified etc

////////////////////////////////////////////////////////////

// XXX: Here at the moment, the inputs are wrong (obviously)

// XXX: Optionally persist this
let loaded_identity = generate_identity();
console.log("loaded_identity", loaded_identity);

// Calculate witness? I know roughly: client/semaphore.js, construct all inputs and to the checkWitness etc. Has logic for proofs and so on.

//const prvKey = Buffer.from('0001020304050607080900010203040506070809000102030405060708090001', 'hex');

let private_key = loaded_identity.private_key;
const prvKey = Buffer.from(private_key, 'hex');

// external nullifier, signal_hash
// what are the exactly? external nullifier must match the one in contract, ok. lets just set it to some arbitrary number for now.

let signal_str = "hello world";
let external_nullifier = bigInt(12312);

console.log("signal_str", signal_str);
// Some signal conversion voodo, seems complex
// XXX: It'd be good to minimize this to whats actually minimally needed
const signal_to_contract = asciiToHex(signal_str);
const signal_to_contract_bytes = new Buffer(signal_to_contract.slice(2), 'hex');

const signal_hash_raw = ethers.utils.solidityKeccak256(
    ['bytes'],
    [signal_to_contract_bytes],
);
// XXX: Buffer deprecated
const signal_hash_raw_bytes = new Buffer(signal_hash_raw.slice(2), 'hex');
const signal_hash = beBuff2int(signal_hash_raw_bytes.slice(0, 31));
console.log("signal_hash", signal_hash);

// what does this mean exactly?
// We are signing the external nullifer and signal hash
// https://github.com/iden3/circomlib/pull/13
// https://eprint.iacr.org/2016/492.pdf
// https://en.wikipedia.org/wiki/Sponge_function
// Why multihash?
const msg = mimcsponge.multiHash([external_nullifier, signal_hash]);
console.log("msg", msg);
// we are signing with MIM
// Whats interaction between EDDSA and MiMC?
const signature = eddsa.signMiMCSponge(prvKey, msg);
console.log("signature", signature);

const pubKey = eddsa.prv2pub(prvKey);

// XXX: What are these exactly?
let identity_nullifier = loaded_identity.identity_nullifier;
let identity_trapdoor = loaded_identity.identity_trapdoor;
let identity_commitment = loaded_identity.identity_commitment;

// identity_path we await from server, glurgh.
// XXX: Not an easy place to leave, but that's where I am at
// server.js: path_for_element/:el
// semaphore.tree.element_index(leaf)
// identity tree index, MerkleTree

// Construct tree
const storage = new SMT.storage.MemStorage();
const hasher = new SMT.hashers.MimcSpongeHasher();
const prefix = 'semaphore';
const default_value = '0';
const depth = 20; // quite deep?

//async function foo() {

const tree = new SMT.tree.MerkleTree(
    `${prefix}_id_tree`,
    storage,
    hasher,
    depth,
    default_value,
);

// ok, we got the tree, now what?
// Add to the tree! we ge that identity commitment
// get tree index, etc etc
// first have to add to tree
// let loaded_identity = generate_identity();

// semapohore url
// server://path_for_element/:identity_commitment OR if exists
// server://path/identity.index
// 1. How is tree constructed?

const leaf = identity_commitment; // element

// tostring?
console.log("leaf", leaf);

// adding identity commitment to tree

let leaf_index;
let path;

// XXX: Ugly as hell here
async function updateTree() {
    await tree.update(1, leaf);
    leaf_index = await tree.element_index(leaf);
    // find path to a index containing identity commitment;
    path = await tree.path(leaf_index);
    console.log("***leaf_index", leaf_index);
};

// returns promise, we can use .then and go
updateTree()
    .then(() => {
        console.log("***leaf_index outside", leaf_index);
        console.log("tree", tree);
        bar();
    })
    .catch((err) => {
        console.log("error", err);
    });

// XXX
let inputs;
let identity_path;

let witness;
let vk_proof;
let proof;
let publicSignals;

function bar() {
    console.log("path", leaf_index);
    identity_path = path;
    console.log("identity_path", identity_path);
    // XXX
    const identity_path_elements = identity_path.path_elements;
    console.log("identity_path_elements", identity_path_elements);
    const identity_path_index = identity_path.path_index;

    assert(eddsa.verifyMiMCSponge(msg, signature, pubKey));
    // => true

    // What are the different types of signature fields?

    // loaded_identity.identity_nullifier?

    inputs = {
        'identity_pk[0]': pubKey[0],
        'identity_pk[1]': pubKey[1],
        'auth_sig_r[0]': signature.R8[0],
        'auth_sig_r[1]': signature.R8[1],
        auth_sig_s: signature.S,
        // XXX
        signal_hash,
        external_nullifier,
        identity_nullifier,
        identity_trapdoor,
        identity_path_elements,
        identity_path_index,
        fake_zero: bigInt(0),
    };

    // So we can define inputs skeleton before

    witness = circuit.calculateWitness(inputs);
    assert(circuit.checkWitness(witness));


    // ok? I assume key is correct
    //vk_proof = deserialize(fs.readFileSync("build/myCircuit.vk_proof", "utf8"));
    vk_proof = JSON.parse(fs.readFileSync("build/myCircuit.vk_proof", "utf8"));
    // XXX: original vs goth?
    // xxx vk_proof is a hing, whats up witness
    // unsringifybigints of vk proof loooks...weird tho. like a string.
    console.log("gen proof");
    // now it looks OK but smt wrong
    // compile time
    // loading
    let {proof, publicSignals} = zkSnark.groth.genProof(unstringifyBigInts(vk_proof), unstringifyBigInts(witness));
//    error TypeError: Cannot read property '5' of undefined
    // gyuess would be it doesn't work.


    // a.affine is not a function
    // https://github.com/iden3/snarkjs/issues/9 err I thought I did this already
    // zkSnark.groth.genProof(vk_proof, witness); fails
    //let {proof, publicSignals} = zkSnark.groth.genProof(vk_proof, witness);

    // // 5. Verify proof
    // XXX dunno if good
    console.log("before vk verifier");
    const vk_verifier = JSON.parse(fs.readFileSync("build/myCircuit.vk_verifier", "utf8"));
    console.log("after vk verifier");

//    if (zkSnark.groth.isValid(vk_verifier, proof, publicSignals)) {
    // wow works
    if (zkSnark.groth.isValid(unstringifyBigInts(vk_verifier), unstringifyBigInts(proof), unstringifyBigInts(publicSignals))) {
        console.log("The proof is valid");
    } else {
        console.log("The proof is not valid");
    }


}

////////////////////////////////////////////////////////////

////  4. Generate proof
// nice, progress

//const w = circuit.calculateWitness(inputs);

//};

//foo();
