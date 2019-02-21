#!/usr/bin/env sh

# Should probably be a subprocess in python and print to some logger
# Or Docker compose or whatever.

geth --testnet --syncmode=light --rpc --maxpeers=25 --shh --shh.pow=0.002 --rpcport=8500 --datadir=/tmp/node-a --port=30000
