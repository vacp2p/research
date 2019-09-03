import os
import strformat
import strutils

import cas_service_pb
import cas_service_twirp

var cas_req = newvac_cas_CASRequest()
try:
  cas_req.id = "foo"
  cas_req.data = "bar"
except:
  echo("Unable to create CASRequest")
  quit(QuitFailure)

# XXX
let client = newCASClient("http://localhost:8001")

# XXX: resp is wrong here
try:
  let resp = Post(client, cas_req)
  echo(&"I got a new post: {resp.id}, {resp.data}")
except Exception as e:
  echo(&"Exception: {e.msg}")
