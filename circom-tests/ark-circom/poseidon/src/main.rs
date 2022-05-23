use ark_circom::{CircomBuilder, CircomConfig};
use ark_std::rand::thread_rng;
use color_eyre::Result;

use ark_bn254::Bn254;
use ark_groth16::{
    create_random_proof, generate_random_parameters, prepare_verifying_key, verify_proof,
};

use std::fs;
use num_bigint::BigInt;
use num_bigint::BigUint;

// JSON
use serde::Deserialize;

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct WitnessInput {
    inputs: Vec<String>,
}

fn test() -> Result<()> {

    // Load JSON input
    let file = fs::File::open("./inputs/input.json").expect("file should open read only");
    let witness_input: WitnessInput  = serde_json::from_reader(file).expect("file should be proper JSON");

    println!("JSON Witness input: {:?}", witness_input);

    // Load the WASM and R1CS for witness and proof generation
    let cfg = CircomConfig::<Bn254>::new(
        "./circuit/poseidon.wasm",
        "./circuit/poseidon.r1cs",
    )?;

    // Insert our public inputs as (key,value) pairs
    let mut builder = CircomBuilder::new(cfg);

    println!("Witness inputs: ");
    for v in witness_input.inputs.iter() {
            builder.push_input(
                "inputs",
                BigInt::parse_bytes(v.as_bytes(), 10).unwrap(),
            );
            println!("{:?}", BigInt::parse_bytes(v.as_bytes(), 10).unwrap());
        }

    // Create an empty instance for setting it up
    let circom = builder.setup();

    // Run a trusted setup
    let mut rng = thread_rng();
    let params = generate_random_parameters::<Bn254, _, _>(circom, &mut rng)?;

    // Get the populated instance of the circuit with the witness
    let circom = builder.build()?;

    let inputs = circom.get_public_inputs().unwrap();

    println!("Public circuit inputs/outputs: ");
    for i in 0..inputs.len() {
        let x: BigUint = inputs[i].into();
        println!("{:#?}", x);
    }

    // Generate the proof
    let proof = create_random_proof(circom, &params, &mut rng)?;

    // Check that the proof is valid
    let pvk = prepare_verifying_key(&params.vk);
    let verified = verify_proof(&pvk, &proof, &inputs)?;
    assert!(verified);

    Ok(())
}

fn main() {
    println!("testing ark-circom poseidon hash");

    match test() {
        Ok(_) => println!("Success"),
        Err(_) => println!("Error"),
    }
}