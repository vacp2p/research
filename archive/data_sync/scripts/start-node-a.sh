#!/usr/bin/env sh

# Should probably be a subprocess in python and print to some logger
# Or Docker compose or whatever.

echo "[Starting node-a...]"

echo "[Copying static-nodes...]"
#cp static-nodes.json /tmp/node-a/
mkdir -p ~/.ethereum/node-a/
cp static-nodes.json ~/.ethereum/node-a/
#geth --testnet --syncmode=light --rpc --maxpeers=25 --shh --shh.pow=0.002 --rpcport=8500 --datadir=~/ethereum/node-a --port=30000

#geth --testnet --syncmode=light --rpc --maxpeers=25 --shh --shh.pow=0.002 --rpcport=8501 --datadir=~/.ethereum/node-b --port=30001 --verbosity=4

echo "[geth starting at port 30000, see node-a.log for logs.]"
geth --rpc --maxpeers=25 --shh --shh.pow=0.002 --rpcport=8500 --datadir=~/.ethereum/node-a --port=30000 --vmodule eth/*=2,p2p=4,shh=5,whisper=5 #&> node-a.log
