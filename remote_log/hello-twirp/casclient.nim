import os
import strformat
import strutils

import cas_service_pb
import cas_service_twirp

import strutils
import byteutils

var content = newvac_cas_Content()
try:
  content.data = hexToSeqByte("foo".toHex())
except:
  echo("Unable to create Content data")
  quit(QuitFailure)

# XXX
let client = newCASClient("http://localhost:8001")

# XXX: resp is wrong here
try:
  let resp = Add(client, content)
  let str = parseHexStr(toHex(resp.id))
  echo(&"I got a new post: {str}")
except Exception as e:
  echo(&"Exception: {e.msg}")


# When you post in ipfs it's just some bytes.
# Then you get ID.

# IPFS as CAS:
# echo "hello worlds" | ipfs add # => QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx
# ipfs cat QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx

# Swarm as CAS:
# Very similar if used as raw chunks (otherwise content type)
# Possibly different ID scheme
