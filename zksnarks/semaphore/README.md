# Semaphore experiments

Based on https://github.com/kobigurk/semaphore but only focusing on the core circom circuits, not contracts or on chain orchestration.

See https://github.com/iden3/snarkjs for a quick start.

Experimenting with feasability of Semaphore in general and https://ethresear.ch/t/semaphore-rln-rate-limiting-nullifier-for-spam-prevention-in-anonymous-p2p-setting/5009 in particular.

See https://github.com/vacp2p/research/issues/2

Main file in `src/hello.js`

To play:
- `npm install`
- generate circuits in build dir (see tutorial above)
- `time node --experimental-repl-await -i -e "$(< src/hello.js)"`
