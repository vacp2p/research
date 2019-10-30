var fs = require('fs');
const zkSnark = require('snarkjs');

// Utils

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
    fs.writeFileSync("build/myCircuit.vk_proof", serialize(setup.vk_proof), "utf8");
    fs.writeFileSync("build/myCircuit.vk_verifier", serialize(setup.vk_verifier), "utf8");
    console.log("Toxic waste:", setup.toxic);  // Must be discarded.
}
// TODO: Conditionally run if file exists
// performSetup(circuit);

// 4. Generate proof
const input = {
    "a": "3",
    "b": "11"
}
const witness = circuit.calculateWitness(input);
const vk_proof = deserialize(fs.readFileSync("build/myCircuit.vk_proof", "utf8"));

const {proof, publicSignals} = zkSnark.groth.genProof(vk_proof, witness);

// 5. Verify proof
const vk_verifier = deserialize(fs.readFileSync("build/myCircuit.vk_verifier", "utf8"));

if (zkSnark.groth.isValid(vk_verifier, proof, publicSignals)) {
    console.log("The proof is valid");
} else {
    console.log("The proof is not valid");
}
