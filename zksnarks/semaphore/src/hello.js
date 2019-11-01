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

function log(s) {
    console.log(new Date(), s);
}

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

// TODO: Optionally persist this identity
function generate_identity() {
    const private_key = crypto.randomBytes(32).toString('hex');
    const prvKey = Buffer.from(private_key, 'hex');
    const pubKey = eddsa.prv2pub(prvKey);

    // XXX: Right now just using random bytes, what should this be?
    const identity_nullifier = '0x' + crypto.randomBytes(31).toString('hex');
    const identity_trapdoor = '0x' + crypto.randomBytes(31).toString('hex');
    log(`generate identity from (private_key, public_key[0], public_key[1], identity_nullifier): (${private_key}, ${pubKey[0]}, ${pubKey[1]}, ${identity_nullifier}, ${identity_trapdoor})`);

		const identity_commitment = pedersenHash([bigInt(circomlib.babyJub.mulPointEscalar(pubKey, 8)[0]), bigInt(identity_nullifier), bigInt(identity_trapdoor)]);

    console.log(`identity_commitment: ${identity_commitment}`);
    const generated_identity = {
        private_key,
        identity_nullifier: identity_nullifier.toString(),
        identity_trapdoor: identity_trapdoor.toString(),
        identity_commitment: identity_commitment.toString(),
        public_key: pubKey
    };

    return generated_identity;
}

function MakeMerkleTree() {
    // Construct tree
    const storage = new SMT.storage.MemStorage();
    const hasher = new SMT.hashers.MimcSpongeHasher();
    const prefix = 'semaphore';
    const default_value = '0';
    const depth = 20; // quite deep?
    //const depth = 2; // only 60k->35k constraints

    const tree = new SMT.tree.MerkleTree(
        `${prefix}_id_tree`,
        storage,
        hasher,
        depth,
        default_value,
    );
    return tree;
}

function performSetup(circuit) {
    const setup = zkSnark.groth.setup(circuit);
    fs.writeFileSync("myCircuit.vk_proof", JSON.stringify(stringifyBigInts(setup.vk_proof)), "utf8");
    fs.writeFileSync("myCircuit.vk_verifier", JSON.stringify(stringifyBigInts(setup.vk_verifier)), "utf8");

    console.log("Toxic waste:", setup.toxic);  // Must be discarded.
}

// Find path to a index containing identity commitment.
// XXX: What happens if tree changes?
async function updateTreeAndGetPath(tree, i, commitment) {
    await tree.update(i, commitment);
    let leaf_index = await tree.element_index(commitment);
    let identity_path = await tree.path(leaf_index);
    return identity_path;
};

// XXX: original vs goth? whats difference?
// XXX: This takes 15m to run
function generateProofWithKey(witness) {
    const vk_proof = JSON.parse(fs.readFileSync("build/myCircuit.vk_proof", "utf8"));
    log("generateProof");
    let proof = zkSnark.groth.genProof(unstringifyBigInts(vk_proof), unstringifyBigInts(witness));
    fs.writeFileSync("build/proof1", JSON.stringify(stringifyBigInts(proof)), "utf8");
    console.log("proof done and persisted", proof);
    return proof;
}

function verifyProofWithKey(proof, publicSignals) {
    const vk_verifier = JSON.parse(fs.readFileSync("build/myCircuit.vk_verifier", "utf8"));
    log("verifyProof");
    if (zkSnark.groth.isValid(unstringifyBigInts(vk_verifier), unstringifyBigInts(proof), unstringifyBigInts(publicSignals))) {
        console.log("The proof is valid");
    } else {
        console.log("The proof is not valid");
    }
}

function checkSignature(msg, signature, pubKey) {
    console.log("checkSignature");
    assert(eddsa.verifyMiMCSponge(msg, signature, pubKey));
}

// XXX: What does this actually do?
function checkWitness(circuit, witness) {
    console.log("checkWitness");
    assert(circuit.checkWitness(witness));
}

// Inputs used for witness
function makeInputs(signature, signal_hash, external_nullifier, identity, identity_path) {
    const identity_nullifier = identity.identity_nullifier;
    const identity_trapdoor = identity.identity_trapdoor;
    const pubKey = identity.public_key;
    const identity_path_elements = identity_path.path_elements;
    const identity_path_index = identity_path.path_index;

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
    return inputs;
}

// XXX: A lot of conversation, it'd be good to minimize this
function signal(str) {
    let signal_str = str;
    const signal_to_contract = asciiToHex(signal_str);
    const signal_to_contract_bytes = new Buffer(signal_to_contract.slice(2), 'hex');
    const signal_hash_raw = ethers.utils.solidityKeccak256(
        ['bytes'],
        [signal_to_contract_bytes],
    );
    // XXX: Buffer deprecated, replace
    const signal_hash_raw_bytes = new Buffer(signal_hash_raw.slice(2), 'hex');
    const signal_hash = beBuff2int(signal_hash_raw_bytes.slice(0, 31));
    return signal_hash;
}

function message(external_nullifier, signal_hash) {
    const msg = mimcsponge.multiHash([external_nullifier, signal_hash]);
    return msg;
}

function sign(identity, msg) {
    let private_key = identity.private_key;
    const prvKey = Buffer.from(private_key, 'hex');
    const signature = eddsa.signMiMCSponge(prvKey, msg);
    return signature;
}

function loadCircuit() {
    const circuitDef = unstringifyBigInts(JSON.parse(fs.readFileSync("build/circuit.json", "utf-8")));
    const circuit = new zkSnark.Circuit(circuitDef);
    return circuit;
}

//////////////////////////////////////////////////////////////////////////////

// NOTE: Using Groth

// 1. Compile circuit with circom:
// circom snark/semaphore.circom -o build/circuit.json (~7m)

// 2. Perform setup - only done once
// TODO: Conditionally run if file exists
// performSetup(circuit);

function run() {
    let identity = generate_identity();
    let tree = MakeMerkleTree();
    let circuit = loadCircuit();
    // Perform setup - only done once
    // performSetup(circuit);

    updateTreeAndGetPath(tree, 1, identity.identity_commitment)
        .then((identity_path) => {
            // Input, what we want to signal
            let signal_hash = signal("hello world");
            // In order to prevent double signals
            let external_nullifier = bigInt(12312);
            let msg = message(external_nullifier, signal_hash);
            let signature = sign(identity, msg);
            checkSignature(msg, signature, identity.public_key);
            let inputs = makeInputs(signature, signal_hash, external_nullifier, identity, identity_path);
            let witness = circuit.calculateWitness(inputs);
            checkWitness(circuit, witness);
            let {proof, publicSignals} = generateProofWithKey(witness);
            verifyProofWithKey(proof, publicSignals);
        })
        .catch((err) => {
            console.log("error", err);
        });
}
