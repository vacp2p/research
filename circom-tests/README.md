# Experimenting with Circom

## Some automation

- To run Phase 1 of Powers Of Tau Ceremony:
 
`./pot`

- To create a new project from template:

`./create project_name`

- To build a project (circuit compilation + witness generation + Phase 2 + proof generation + proof verification), `cd` into the project folde, update `input.json` with a correct input for the circuit and 

```
make
```

- To compute a witness for a given input, update `input.json` and

```
make witness
```

- To generate a proof and verify it (witness for  `input.json` is recomputed):

```
make proof
```

