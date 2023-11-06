# Reinforced Concrete Modification for execution environments with 256 bit word sizes

> Note: All the implementations discussed below are for the scalar fields of the bn254 (alt-bn128) curve

The [paper](https://eprint.iacr.org/2021/1038) describes a new sponge hash function
that is designed to replace Poseidon (in specific contexts).

It claims to be over 15x faster than Poseidon, 
through the use of [lookup tables](https://eprint.iacr.org/2020/315.pdf).

For RLN, and associated zk-gadgets which make use of Poseidon, 
this will be a good alternative to favor performance.

The paper also describes how the RC hash function is more secure than Poseidon.

We must first analyze the viability of the RC hash in 3 contexts -
1. Plain Implementation
2. Different proof systems (groth16, plonky2, etc)
3. Virtual machines with a word size of 256 bit (EVM, etc)

If we are to get better performance in atleast 2 of these contexts,
we may be able to replace Poseidon.

## 1. Plain Implementation

The [reference implementation](https://extgit.iaik.tugraz.at/krypto/zkfriendlyhashzoo/-/blob/master/plain_impls/src/reinforced_concrete/reinforced_concrete.rs) is significantly faster than Poseidon -

| Hash Function | Plain performance (ns) |
|---------|--------------------------------------------|
| RC | 3_419 |
| Poseidon | 19_944 |

Result: The RC plain implementation is favored

## 2. Different proof systems

| Hash Function | R1CS equations | Plookup gates | 
| ------------- | -------------- | ------------- |
| RC | - | 378 | 
| Poseidon | 243 | 633 |

Note that RC has not been implemented in groth16, due to the requirement of lookup tables.

> Note: we will come back to this statement after analyzing the evm context

## 3. The EVM

The amount of gas used is excluding the base fee (21_000).
Both implementations are for t=2 inputs.

| Hash Function | Gas used |
| ------------- | -------- |
| [RC](https://github.com/rymnc/reinforced-concrete-huff) | 25_480 |
| [Poseidon](https://github.com/privacy-scaling-explorations/maci/blob/master/contracts/ts/buildPoseidon.ts) | 34_543 |

The RC implementation makes use of [bit shifting](https://github.com/rymnc/reinforced-concrete-huff/blob/9194824ececb86b83e6900fbe6fca08e2feb3062/src/ReinforcedConcrete.huff#L225-L228) arising 
from compressing the lookup table from 683 u16's to 42 u256's (to save on bytecode size).

We also reduce the number of operations required in the `decompose` and `compose` steps of the `bars` construct, 
since we do not need to cast integers to u16's.

- [Optimized decompose](https://github.com/rymnc/reinforced-concrete-huff/blob/9194824ececb86b83e6900fbe6fca08e2feb3062/src/ReinforcedConcrete.huff#L199-L206)
- [Optimized compose](https://github.com/rymnc/reinforced-concrete-huff/blob/9194824ececb86b83e6900fbe6fca08e2feb3062/src/ReinforcedConcrete.huff#L208-L223)

Result: The RC hash implementation is favored

## On the use of lookups

While the paper suggests the use of lookup tables, 
we were able to implement the hash function for the evm without the use of any (no support for constant time lookups).

This approach could be used to produce an RC implementation using groth16, 
but more experimentation should be done.

It may require more constraints than Poseidon, 
but yet to be seen.

