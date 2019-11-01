const crypto = require('crypto');
const fs = require('fs');
const zkSnark = require('snarkjs');
const circomlib = require('circomlib');
const web3Utils = require('web3-utils');
const ethers = require('ethers');
const SMT = require('semaphore-merkle-tree');

const {stringifyBigInts, unstringifyBigInts} = require("snarkjs/src/stringifybigint.js");
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

function generate_identity() {
    const private_key = crypto.randomBytes(32).toString('hex');
    const prvKey = Buffer.from(private_key, 'hex');
    const pubKey = eddsa.prv2pub(prvKey);

    // XXX: Right now just using random bytes, what should this be?
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
const circuitDef = unstringifyBigInts(JSON.parse(fs.readFileSync("build/circuit.json", "utf-8")));
const circuit = new zkSnark.Circuit(circuitDef);

// Inspect circuit with e.g.:
// circuits.nConstraints

// 2. Perform setup - only done once
function performSetup(circuit) {
    const setup = zkSnark.groth.setup(circuit);
    fs.writeFileSync("myCircuit.vk_proof", JSON.stringify(stringifyBigInts(setup.vk_proof)), "utf8");
    fs.writeFileSync("myCircuit.vk_verifier", JSON.stringify(stringifyBigInts(setup.vk_verifier)), "utf8");

    console.log("Toxic waste:", setup.toxic);  // Must be discarded.
}
// TODO: Conditionally run if file exists
//performSetup(circuit);

// TODO: Optionally persist this identity
let loaded_identity = generate_identity();
console.log("loaded_identity", loaded_identity);

let private_key = loaded_identity.private_key;
const prvKey = Buffer.from(private_key, 'hex');

// XXX: external nullifier what should this be set to?
let signal_str = "hello world";
let external_nullifier = bigInt(12312);
// XXX: It'd be good to minimize this to whats actually minimally needed
const signal_to_contract = asciiToHex(signal_str);
const signal_to_contract_bytes = new Buffer(signal_to_contract.slice(2), 'hex');
const signal_hash_raw = ethers.utils.solidityKeccak256(
    ['bytes'],
    [signal_to_contract_bytes],
);
// XXX: Buffer deprecated, replace
const signal_hash_raw_bytes = new Buffer(signal_hash_raw.slice(2), 'hex');
const signal_hash = beBuff2int(signal_hash_raw_bytes.slice(0, 31));
console.log("signal_hash", signal_hash);

// XXX: what does this mean exactly?
// We are signing the external nullifer and signal hash
// https://github.com/iden3/circomlib/pull/13
// https://eprint.iacr.org/2016/492.pdf
// https://en.wikipedia.org/wiki/Sponge_function
// Why multihash? Whats interaction between EDDSA, MiMC and Pedersen?
const msg = mimcsponge.multiHash([external_nullifier, signal_hash]);
console.log("msg", msg);
const signature = eddsa.signMiMCSponge(prvKey, msg);
console.log("signature", signature);
const pubKey = eddsa.prv2pub(prvKey);

// XXX: What are these exactly?
let identity_nullifier = loaded_identity.identity_nullifier;
let identity_trapdoor = loaded_identity.identity_trapdoor;
let identity_commitment = loaded_identity.identity_commitment;

// Construct tree
const storage = new SMT.storage.MemStorage();
const hasher = new SMT.hashers.MimcSpongeHasher();
const prefix = 'semaphore';
const default_value = '0';
const depth = 20; // quite deep?

const tree = new SMT.tree.MerkleTree(
    `${prefix}_id_tree`,
    storage,
    hasher,
    depth,
    default_value,
);

const leaf = identity_commitment;
console.log("leaf", leaf);
// Global scope for REPL debugging
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

// XXX: Very ugly
updateTree()
    .then(() => {
        console.log("leaf_index", leaf_index);
        console.log("tree", tree);
        bar();
    })
    .catch((err) => {
        console.log("error", err);
    });

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
    const identity_path_elements = identity_path.path_elements;
    console.log("identity_path_elements", identity_path_elements);
    const identity_path_index = identity_path.path_index;

    assert(eddsa.verifyMiMCSponge(msg, signature, pubKey));

    inputs = {
        'identity_pk[0]': pubKey[0],
        'identity_pk[1]': pubKey[1],
        'auth_sig_r[0]': signature.R8[0],
        'auth_sig_r[1]': signature.R8[1],
        auth_sig_s: signature.S,
        signal_hash,
        external_nullifier,
        identity_nullifier,
        identity_trapdoor,
        identity_path_elements,
        identity_path_index,
        fake_zero: bigInt(0),
    };

    witness = circuit.calculateWitness(inputs);
    assert(circuit.checkWitness(witness));

    // 3. Verify proof
    vk_proof = JSON.parse(fs.readFileSync("build/myCircuit.vk_proof", "utf8"));
    // XXX: original vs goth? whats difference?
    console.log("gen proof");
    // XXX: This takes a long time, benchmark?
    let {proof, publicSignals} = zkSnark.groth.genProof(unstringifyBigInts(vk_proof), unstringifyBigInts(witness));

    // 4. Verify proof
    console.log("before vk verifier");
    const vk_verifier = JSON.parse(fs.readFileSync("build/myCircuit.vk_verifier", "utf8"));
    console.log("after vk verifier");
    if (zkSnark.groth.isValid(unstringifyBigInts(vk_verifier), unstringifyBigInts(proof), unstringifyBigInts(publicSignals))) {
        console.log("The proof is valid");
    } else {
        console.log("The proof is not valid");
    }
}
