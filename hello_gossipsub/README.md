# Hello GossipSub

Playing around with GossipSub in Nim to check feasibility of moving over Waku to libp2p.

Let's start small:
- Node that broadcast message
- Node that receives it


## Running

`nim c -r src/hello_gossipsub.nim`

Alt, Waku (imported):

```
make start_network quicksim
# ./build/start_network --topology:FullMesh --amount:6 --test-node-peers:2
./build/start_network
./build/quicksim
```

## What I want to do

Use Waku stuff from Nimbus here,
Get quicksim working
Then try to do similar with libp2p gossipsub
