#!/usr/bin/env sh

echo "[Checking Alice's log for topic Bob through various nodes...]"

alice="$(curl -s 'http://localhost:9600/bzz-feed:/?user=0xBCa21d9c6031b1965a9e0233D9B905d2f10CA259&name=bob')"
bob="$(curl -s 'http://localhost:9601/bzz-feed:/?user=0xBCa21d9c6031b1965a9e0233D9B905d2f10CA259&name=bob')"
charlie="$(curl -s 'http://localhost:9602/bzz-feed:/?user=0xBCa21d9c6031b1965a9e0233D9B905d2f10CA259&name=bob')"
gateway="$(curl -s 'https://swarm-gateways.net/bzz-feed:/?user=0xBCa21d9c6031b1965a9e0233D9B905d2f10CA259&name=bob')"

echo "9600 (Alice): $alice"
echo "9601 (Bob): $bob"
echo "9602 (Charlie): $charlie"
echo "swarm-gateways.net: $gateway"

echo "[Done]"
