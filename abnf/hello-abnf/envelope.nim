import
  sequtils, options, unittest, tables, nimcrypto/hash, stew/byteutils,
  eth/[keys, rlp], eth/p2p/rlpx_protocols/whisper/whisper_types as whisper

# example from https://github.com/paritytech/parity-ethereum/blob/93e1040d07e385d1219d00af71c46c720b0a1acf/whisper/src/message.rs#L439
let
  env0 = Envelope(
    expiry:100000, ttl: 30, topic: [byte 0, 0, 0, 0],
    data: repeat(byte 9, 256), nonce: 1010101)
  env1 = Envelope(
    expiry:100000, ttl: 30, topic: [byte 0, 0, 0, 0],
    data: repeat(byte 9, 256), nonce: 1010102)

echo "* env0"
echo env0

echo "* repr env0"
echo repr(env0)

echo "* rlp env0"
echo rlp.encodeList(env0.expiry, env0.ttl, env0.topic, env0.data, env0.nonce)

echo "* hex rlp env0"
echo toHex(rlp.encodeList(env0.expiry, env0.ttl, env0.topic, env0.data, env0.nonce))

