const crypto = require('crypto');
const fs = require('fs');
const sha1 = require('sha1');
const zkSnark = require('snarkjs');
const circomlib = require('circomlib');
const web3Utils = require('web3-utils');
const ethers = require('ethers');
const SMT = require('semaphore-merkle-tree');
const secrets = require("secrets.js");

const {stringifyBigInts, unstringifyBigInts} = require("snarkjs/src/stringifybigint.js");
const asciiToHex = web3Utils.asciiToHex;
const bigInt = zkSnark.bigInt;
const eddsa = circomlib.eddsa;
const mimcsponge = circomlib.mimcsponge;

// Largely based on https://github.com/kobigurk/semaphore

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

function generateIdentity() {
    const private_key = crypto.randomBytes(32).toString('hex');
    const prvKey = Buffer.from(private_key, 'hex');
    const pubKey = eddsa.prv2pub(prvKey);

    // XXX: Right now just using random bytes, what should this be?
    const identity_nullifier = '0x' + crypto.randomBytes(31).toString('hex');
    const identity_trapdoor = '0x' + crypto.randomBytes(31).toString('hex');
    //log(`generate identity from (private_key, public_key[0], public_key[1], identity_nullifier): (${private_key}, ${pubKey[0]}, ${pubKey[1]}, ${identity_nullifier}, ${identity_trapdoor})`);

		const identity_commitment = pedersenHash([bigInt(circomlib.babyJub.mulPointEscalar(pubKey, 8)[0]), bigInt(identity_nullifier), bigInt(identity_trapdoor)]);

    //log(`identity_commitment: ${identity_commitment}`);
    const generated_identity = {
        private_key,
        identity_nullifier: identity_nullifier.toString(),
        identity_trapdoor: identity_trapdoor.toString(),
        identity_commitment: identity_commitment.toString()
    };
    //console.log("Identity commitment (Save this to load identity)", identity_commitment.toString());
    const filename = "build/identity_commitment_" + identity_commitment.toString();
    // XXX: Maybe not needed here, weird BigInt parsing
    fs.writeFileSync(filename, JSON.stringify(stringifyBigInts(generated_identity)), "utf8");
    return generated_identity;
}

function getPublicKey(identity) {
    const private_key = identity.private_key;
    const prvKey = Buffer.from(private_key, 'hex');
    const pubKey = eddsa.prv2pub(prvKey);
    return pubKey;
}

function loadIdentity(identity_commitment) {
    log("loadIdentity");
    const filename = "build/identity_commitment_" + identity_commitment;
    const identity = JSON.parse(fs.readFileSync(filename, "utf8"));
    return identity;
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

    //console.log("Toxic waste:", setup.toxic);  // Must be discarded.
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
    const witness_hash = sha1(JSON.stringify(stringifyBigInts(witness)));
    const filename = "build/witness_proof_" + witness_hash;
    //console.log("witness hash", filename);
    fs.writeFileSync(filename, JSON.stringify(stringifyBigInts(proof)), "utf8");
    //console.log("proof done and persisted", proof);
    return proof;
}

function loadPreComputedProof(witness) {
    const witness_hash = sha1(JSON.stringify(stringifyBigInts(witness)));
    const filename = "build/witness_proof_" + witness_hash;
    //console.log("witness hash", filename);
    log("loadPreComputedProof");
    const proof = unstringifyBigInts(JSON.parse(fs.readFileSync(filename, "utf8")));
    return proof;
}

function loadOrGenerateProofWithKey(witness) {
    let res;
    try {
        //log("Looking for already existing proof...");
        res = loadPreComputedProof(witness);
    } catch(err) {
        //log("Can't find proof for witness, generating new proof");
        res = generateProofWithKey(witness);
    }
    return res;
}

function verifyProofWithKey(proof, publicSignals) {
    const vk_verifier = JSON.parse(fs.readFileSync("build/myCircuit.vk_verifier", "utf8"));
    log("verifyProof");
    if (zkSnark.groth.isValid(unstringifyBigInts(vk_verifier), unstringifyBigInts(proof), unstringifyBigInts(publicSignals))) {
        log("The proof is valid");
        return true;
    } else {
        log("The proof is not valid");
        return false;
    }
}

function checkSignature(msg, signature, pubKey) {
    log("checkSignature");
    assert(eddsa.verifyMiMCSponge(msg, signature, pubKey));
}

// XXX: What does this actually do?
function checkWitness(circuit, witness) {
    log("checkWitness");
    assert(circuit.checkWitness(witness));
}

// Inputs used for witness
function makeInputs(signature, signal_hash, external_nullifier, identity, identity_path) {
    const identity_nullifier = identity.identity_nullifier;
    const identity_trapdoor = identity.identity_trapdoor;
    const pubKey = getPublicKey(identity);
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
    const signal_to_contract_bytes = Buffer.from(signal_to_contract.slice(2), 'hex');
    const signal_hash_raw = ethers.utils.solidityKeccak256(
        ['bytes'],
        [signal_to_contract_bytes],
    );
    // XXX: Buffer deprecated, replace
    const signal_hash_raw_bytes = Buffer.from(signal_hash_raw.slice(2), 'hex');
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
    // Once per identity
    // let identity = generateIdentity();
    let identity = loadIdentity("17939861921584559533262186509737425990469800861754459917147159747570381958900");
    let tree = MakeMerkleTree();
    let circuit = loadCircuit();

    // Perform setup - only done once
    // performSetup(circuit);

    // TODO: Case where identity isn't in tree, this should mean they aren't allowed to signal and thus proof is invalid (?)
    // XXX: Not quite clear to me how this would work, since you have to verify with merkle tree
    updateTreeAndGetPath(tree, 1, identity.identity_commitment)
        .then((identity_path) => {
            //console.log("identity_path", identity_path);

            // Input, what we want to signal
            let signal_hash = signal("hello world");
            //console.log("signal hash", signal_hash);
            // In order to prevent double signals
            // _How_ does it do this though?
            // And how do we prove we are identity allowed to signal? What happens if identity isn't in tree?
            let external_nullifier = bigInt(12312);
            let msg = message(external_nullifier, signal_hash);
            //console.log("msg", msg);
            let signature = sign(identity, msg);
            //console.log("signature", signature);
            checkSignature(msg, signature, getPublicKey(identity));
            let inputs = makeInputs(signature, signal_hash, external_nullifier, identity, identity_path);
            let witness = circuit.calculateWitness(inputs);
            checkWitness(circuit, witness);
            let {proof, publicSignals} = loadOrGenerateProofWithKey(witness);
            verifyProofWithKey(proof, publicSignals);
        })
        .catch((err) => {
            console.log("error", err);
        });
}

// badRun: Identity not part of tree
// I don't understand how the following holds:
// The commitment of the identity structure (identity_pk, identity_nullifier, identity_trapdoor) exists in the identity tree with the root root, using the path (identity_path_elements, identity_path_index). This ensures that the user was added to the system at some point in the past.
// Cause we don't actually _use_ the tree to check membership
// This tree should live in a smart contract or so
// TODO: Emulate smart contract here?
// XXX: Some issue with identity_path, might just be format though?
function badRun() {
    let identity = loadIdentity("17939861921584559533262186509737425990469800861754459917147159747570381958900");
    let tree = MakeMerkleTree();
    let circuit = loadCircuit();
    // Perform setup - only done once
    // performSetup(circuit);

    // fake path
    let identity_path = {root: '0', path_elements: ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0'], path_index: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], element: "0"};
    // Input, what we want to signal
    let signal_hash = signal("hello world");
    // In order to prevent double signals
    // _How_ does it do this though?
    // And how do we prove we are identity allowed to signal? What happens if identity isn't in tree?
    let external_nullifier = bigInt(12312);
    let msg = message(external_nullifier, signal_hash);
    let signature = sign(identity, msg);
    checkSignature(msg, signature, getPublicKey(identity));
    let inputs = makeInputs(signature, signal_hash, external_nullifier, identity, identity_path);
    // Here it breaks, something wrong with witness -> inputs -> identity_path
    // throw new Error("Invalid signal identifier: "+ name);
    let witness = circuit.calculateWitness(inputs);
    checkWitness(circuit, witness);
    let {proof, publicSignals} = loadOrGenerateProofWithKey(witness);
    verifyProofWithKey(proof, publicSignals);
}

//run();
//badRun(); // XXX doesn't work right now

// nullifiers_hash is uniquely derived from external_nullifier, identity_nullifier and identity_path_index. This ensures a user cannot broadcast a signal with the same external_nullifier more than once.
//
// if you have a different signal but same external_hash

// I want to detect if someone signals twice with same external nullifier, what consequence does this have?
// Next step is validation of external nullifier I suppose
// Even if same signal OR if change signal, both counts as double signaling

// I don't follow how 'owner' sets external nullifier, and identity commitment.
// ("Make a signal a day is OK"). Oh wait! Whats in proof, you got those public signals, 4 of them.

// Do these correspond directly?
// signal_hash
// external_nullifier
// root
// nullifiers_hash
// "publicSignals":["5121897353393075953233736662126164055971964573317818869495592865833472332086","6540712601030472624123295577656975405754743854357625108717032000526996056503","125606243838566630058575099447702412745558900339761109861010052356172984351","12312"]

// 1256... is the signal_hash, i.e. just a a hash of signal
// 12312 is external nullifier
// 512... is the root of the merkle tree
// and I suppose 654... is the nullifiers_hash

// Ok cool, so can we do with this public info in proof?
// - we can see if someone has used the same external nullifier twice (double spend)
// - we can also check if external_nullifier is a reasonable date
// I don't get why we need nullifiers hash... oh wait, cause you can have (signal, external nullifier) same for different participants
// so what you want to check is with nullifier hash, since thats hashed with identity too

// e.g. only allow
// - single nullifier hash, if multiple we should 'reject proof' (though it is valid? just wrong kind? eh)
// - external nullifiers in a specific time range (+-20s in unix time)
// e.g. don't allow random stuff in external nullifier

// then the extension for rate limiting and slashing goes something like:
// deposit in contract some slashable stuff
// then reveal from https://ethresear.ch/t/semaphore-rln-rate-limiting-nullifier-for-spam-prevention-in-anonymous-p2p-setting/5009
//
//
// "We generate a nullifier_private_key based upon hash(external_nullifier, leaf_private_key)
// We encrypt the leaf_private_key with the nullfier_private_key and reveal the result as a public input.
//     We user shamir secret sharing to encode the nullifier_private_key so that 51% of the shares are required to reconstruct the secret.
//     We then use signal to randomly select 50% of the shares and reveal them.

// Now each time you create a signal with the same external_nullifier but different signal it

// calculates the same nullifier_private_key key and encrypts your leaf_private_key with it.
//     It calculates the same shamir secret and shares.
//     But it reveals a different 50% of the shares."

// Need to think about this more

// If this is a voting signal, how do we ensure voting only once? Fixed external nullifier

// In voting, we restrict external nullifier to a constant
// This way a given identity can only signal once
function votingExample(vote_token, vote_signal) {
    let identity = loadIdentity("17939861921584559533262186509737425990469800861754459917147159747570381958900");
    let tree = MakeMerkleTree();
    let circuit = loadCircuit();

    console.log("votingExample", vote_token, vote_signal);

    // Add identity to tree
    let res = updateTreeAndGetPath(tree, 1, identity.identity_commitment)
        .then((identity_path) => {
            //console.log("identity_path", identity_path);

            // Input, what we want to signal
            let signal_hash = signal(vote_signal);
            //console.log("signal hash", signal_hash);

            // Let's say external nullifier has to be this, if it isn't it should fail validation
            let external_nullifier = vote_token;
            let msg = message(external_nullifier, signal_hash);
            //console.log("msg", msg);
            let signature = sign(identity, msg);
            //console.log("signature", signature);
            checkSignature(msg, signature, getPublicKey(identity));
            let inputs = makeInputs(signature, signal_hash, external_nullifier, identity, identity_path);
            let witness = circuit.calculateWitness(inputs);
            checkWitness(circuit, witness);
            let {proof, publicSignals} = loadOrGenerateProofWithKey(witness);
            return untrustedVerify(proof, publicSignals);
        })
        .catch((err) => {
            console.log("error !", err);
            return false;
        });
    return res;
}

function untrustedVerify(proof, publicSignals) {
    let merkle_root = publicSignals[0];
    let nullifier_hash = publicSignals[1];
    let signal_hash = publicSignals[2];
    let external_nullifier = publicSignals[3];

    // This is the only valid external nullifier for this vote
    // XXX: Is what we want to check nullifier hash?
    // "With same external nullifier more than once"
    let vote_token = BigInt(12312);

    try {
        assert(external_nullifier == vote_token, "Wrong token!");
        assert(verifyProofWithKey(proof, publicSignals));
        console.log("All checks out!");
        return true;
    } catch(err) {
        console.log("Assertions failed:", err.message);
        return false;
    };
}

async function voteTesting() {
    try {
        assert(await votingExample(BigInt(12312), "I vote for A") == true);
        assert(await votingExample(BigInt(12319), "I vote for A") == false);
        // TODO: voteState - keep track of nullifier hashes seen between runs
        // This ensures you can't signal twice with same external identifier
        //assert(await votingExample(BigInt(12312), "I vote for B") == false);

        // TODO: Bad identity, this requires constructing 'untrusted' tree and verifying
        // TODO: To check for bad identity, we can simple reconstruct tree with:
        // identity commitment and path
        // Then merkle root has to match, and ZKP proves you are part of that
        // tree with that root
        // ...what does this mean if we add/leave network? need to update /
        // allow slack
    } catch(err) {
        console.log("Oops, no good", err);
    }
};

//voteTesting();

// // test merkle tree, untrusted pov
// let identity = loadIdentity("17939861921584559533262186509737425990469800861754459917147159747570381958900");
// let commitment = identity.identity_commitment;
// let tree = MakeMerkleTree();
// let path = updateTreeAndGetPath(tree, 1, identity.identity_commitment);
// root = merkle_root
// is_valid(proof)
// enough to show that identity is part of merkle tree at some specific position


// Rate limiting! Now we want some form of secret shamir sharing here.

// > Firstly we have a smart contract that allows anyone to deposit some
// > currency and join our group. At any point a users can be removed from the
// > group if someone calls a function passing their private key as an input.
// > Anyone who does this will receive 33% of the slashed stake the remainder is
// > burned.

// TODO: Clean up above and badRun

// 1. Based on nullifier hash (hash of external nullifier / leaf private key), we
// generate a private key
// 2. Encrypt leaf private key based on this nullifier private key
// 3. Use Shamir Secret Sharing to encode nullifier private key

// ...etc, lets break

// Code up shamir secret sharing?
// What changes to ZKP does this require

// If previously nullifier hash was hash(external_nullifier, leaf_private_key), wheres private key?

// nullifiers_hash is uniquely derived from external_nullifier, identity_nullifier and identity_path_index. This ensures a user cannot broadcast a signal with the same external_nullifier more than once.
// sow hat you mean? its hash of identity nullifier
// commitment is just identity nullifier and trapdoor

// Same external nullifier and different signal:
// Generate same secret shares etc, but reveal different portion
// 2/3 likely it'll pick another one. Then we can slash.
// Lets mock
// Doing in snarks is a bit too involved for now

// TODO: Add to snark (GHI) fun experiment too, standalone ish

// Assumption: same complexity ish

function shamirSeed(pk, en) {
    // XXX: probably more safe way to hash pk and en
    const seed = sha1(pk + en);
    const key = secrets.str2hex(seed);
    console.log("Shamir key", key);
    return key;
}

// Calculates a secret key that requires 2/3 shares to compute
// Uses pk and en as seed and returns a random share.
// If pk and en are the same, there's a 2/3 chance of reveal.
// XXX: Share generation not deterministic, need to re-use
// function shamirShare(key) {
//    const shares = secrets.share(key, 3, 2);
//     //const randIndex = Math.floor(Math.random()*Math.floor(3));
//     //return {secretKey: key, randomShare: shares[randIndex]};
//     return shares;
// }

// XXX This would be dealt with in Snarks
// XXX: Ugly global
let trustedKeysStore = new Set();
let shamirSharesStore = new Map();

// XXX: Ugly global, should be in local state
// XXX: This seems like an issue actually, how are we supposed to do this efficently?
// Having a hash for same external nullifier, different signals and same id would make detection easier
let sharesStore = [];

function foundShamirKey() {
    log("foundShamirKey");

    //console.log("sharesStore", sharesStore);
    // TODO: This should be all combinations of selection
    if (sharesStore.length < 2) {
        return false;
    }
    let candidates = [];
    for (let i = 0; i < sharesStore.length - 1; i++) {
        for (let j = i+1; j<sharesStore.length - 1; j++) {
            candidates.push([sharesStore[i], sharesStore[j]]);
        }
    }
    //console.log("CANDIDATES:", candidates);

    //console.log("trustedKeysStore", trustedKeysStore);
    for (let k = 0; k < candidates.length; k++) {
        let key_candidate = secrets.combine(candidates[k]);
        //console.log("key candidate", key_candidate);
        if (trustedKeysStore.has(key_candidate)) {
            console.log("Found the private key, can slash!");
            return true;
        }
    }

    return false;

    //let sel = [sharesStore[0], sharesStore[1]];
    //let key_candidate = secrets.combine(sel);
//     console.log("key candidate", key_candidate);
//     console.log("trustedKeysStore", trustedKeysStore);
//     if (trustedKeysStore.has(key_candidate)) {
//         console.log("Found the private key, can slash!");
//         return true;
//     } else {
//         return false;
//     }
}

function untrustedVerifySpam(proof, publicSignals, randomShare) {
    let merkle_root = publicSignals[0];
    let nullifier_hash = publicSignals[1];
    let signal_hash = publicSignals[2];
    let external_nullifier = publicSignals[3];

    // "With same external nullifier more than once"
    // TODO: Restrict allow_en to be timestamp +- 20s, say
    let allowed_en = external_nullifier;

    // Add to seen shares;
    sharesStore = sharesStore.concat(randomShare);
    let slashable = foundShamirKey();

    try {
        //assert(external_nullifier == allowed_en, "Wrong token!");
        assert(verifyProofWithKey(proof, publicSignals));
        assert(slashable == false, "Slashable!");
        console.log("All checks out!");
        return true;
    } catch(err) {
        console.log("Assertions failed:", err.message);
        return false;
    };
}


function spamExample(external_nullifier, signal_str) {
    let identity = loadIdentity("17939861921584559533262186509737425990469800861754459917147159747570381958900");
    let tree = MakeMerkleTree();
    let circuit = loadCircuit();

    // Lets try Shamir secret etc here
    // For every same external nullifier, generate shamir secret share
    // Can we use as seed?

    // QQQ
    // XXX: This logic should be in snarks
    let key = shamirSeed(identity.private_key, external_nullifier);
    let shares;
    if (shamirSharesStore.get(key)) {
        console.log("Already used key, picking random share to reveal");
    } else {
        console.log("New key, getting secretKey and shares");
        shares = secrets.share(key, 3, 2);
        //console.log("Shares", shares);
        // XXX: This doesn't deal with multiple keys, assumes one store
        shamirSharesStore.set(key, shares);
        //console.log("foo", shamirSharesStore);
    }
    // Picks a random share, assumes same key
    const randIndex = Math.floor(Math.random()*Math.floor(3));
    //console.log("shamirSharesStore", shamirSharesStore);
    let allShares = shamirSharesStore.get(key);
    //console.log("allShares", allShares);
    let randomShare = allShares[randIndex];

    console.log("spamExample", external_nullifier, signal_str);
    //console.log("secretKey", key);
    //console.log("shamirShares", shares);

    // XXX: Adding secret key and shares store, this would be in snark
    trustedKeysStore.add(key);

    /// QQQ: I bet this logic is wrong

    // Add identity to tree
    let res = updateTreeAndGetPath(tree, 1, identity.identity_commitment)
        .then((identity_path) => {
            //console.log("identity_path", identity_path);

            // Input, what we want to signal
            let signal_hash = signal(signal_str);
            //console.log("signal hash", signal_hash);

            // Let's say external nullifier has to be this, if it isn't it should fail validation
            let msg = message(external_nullifier, signal_hash);
            //console.log("msg", msg);
            let signature = sign(identity, msg);
            //console.log("signature", signature);
            checkSignature(msg, signature, getPublicKey(identity));
            let inputs = makeInputs(signature, signal_hash, external_nullifier, identity, identity_path);
            let witness = circuit.calculateWitness(inputs);
            checkWitness(circuit, witness);
            let {proof, publicSignals} = loadOrGenerateProofWithKey(witness);
            return untrustedVerifySpam(proof, publicSignals, randomShare);
        })
        .catch((err) => {
            console.log("error !", err);
            return false;
        });
    return res;
}

async function spamTesting() {
    try {
        // XXX: Just using voting signals to avoid recomputing proofs
        // XXX: Bad logic, should go through all and get probabilsitic falseCount
        assert(await spamExample(BigInt(12312), "I vote for A") == true);
        assert(await spamExample(BigInt(12312), "I vote for A") == (true || false));
        assert(await spamExample(BigInt(12312), "I vote for A") == (true || false));
        assert(await spamExample(BigInt(12312), "I vote for A") == (true || false));
        assert(await spamExample(BigInt(12312), "I vote for A") == (true || false));
        assert(await spamExample(BigInt(12312), "I vote for A") == (true || false));
        assert(await spamExample(BigInt(12312), "I vote for A") == (true || false));
        //assert(await spamExample(BigInt(12312), "I vote for B") == true);
    } catch(err) {
        console.log("Oops, no good", err);
    }
};


// TODO: Clean up this code comments

spamTesting();
