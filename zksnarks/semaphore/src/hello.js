const crypto = require('crypto');
var fs = require('fs');
const zkSnark = require('snarkjs');
const circomlib = require('circomlib');

const web3Utils = require('web3-utils');

const ethers = require('ethers');

const asciiToHex = web3Utils.asciiToHex;

const bigInt = zkSnark.bigInt;

const eddsa = circomlib.eddsa;
const mimcsponge = circomlib.mimcsponge;

// Utils

beBuff2int = function(buff) {
    let res = bigInt.zero;
    for (let i=0; i<buff.length; i++) {
        const n = bigInt(buff[buff.length - i - 1]);
        res = res.add(n.shl(i*8));
    }
    return res;
};

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
    fs.writeFileSync("build/proving_key.json", serialize(setup.vk_proof), "utf8");
    fs.writeFileSync("build/verification_key.json", serialize(setup.vk_verifier), "utf8");
    console.log("Toxic waste:", setup.toxic);  // Must be discarded.
}
// TODO: Conditionally run if file exists
// performSetup(circuit);

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

// identity_path we await from server, glurgh.
// XXX: Not an easy place to leave, but that's where I am at
// server.js: path_for_element/:el
// semaphore.tree.element_index(leaf)
// identity tree index, MerkleTree
// HERE AM
const identity_path_elements = identity_path.path_elements;
const identity_path_index = identity_path.path_index;

assert(eddsa.verifyMiMCSponge(msg, signature, pubKey));
// => true

// What are the different types of signature fields?

// loaded_identity.identity_nullifier?

const inputs = {
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

// const w = circuit.calculateWitness(inputs);
// assert(circuit.checkWitness(w));

////////////////////////////////////////////////////////////

////  4. Generate proof
// const input = {
//     "a": "3",
//     "b": "11"
// }
// const witness = circuit.calculateWitness(input);
// const vk_proof = deserialize(fs.readFileSync("build/proving_key.json", "utf8"));

// const {proof, publicSignals} = zkSnark.groth.genProof(vk_proof, witness);

// // 5. Verify proof
// const vk_verifier = deserialize(fs.readFileSync("build/verification_key.json", "utf8"));

// if (zkSnark.groth.isValid(vk_verifier, proof, publicSignals)) {
//     console.log("The proof is valid");
// } else {
//     console.log("The proof is not valid");
// }
