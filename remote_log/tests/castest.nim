import cas_service_pb
import cas_service_twirp
import strutils
import byteutils
import strformat

# XXX: Hacky tests
# Can retrieve and post node

# CAS util
proc createContent*(s: string): vac_cas_Content =
  var content = newvac_cas_Content()
  try:
    content.data = hexToSeqByte(s.toHex())
  except:
    echo("Unable to create Content data")
    quit(QuitFailure)
  return content

proc createAddress*(s: string): vac_cas_Address =
  var address = newvac_cas_Address()
  try:
    setid(address, hexToSeqByte(s))
  except:
    echo("Unable to create Address data")
    quit(QuitFailure)
  return address

let casClient = newCASClient("http://localhost:8001")

proc postContent(s: string): string =
  var content = createContent(s)
  try:
    let resp = Add(casClient, content)
    let str = parseHexStr(toHex(resp.id))
    echo(&"I got a new post: {str}")
    return str
  except Exception as e:
    echo(&"Exception: {e.msg}")

proc getContent(s: string): string =
  echo("getContent s: <", s, ">")
  var address = createAddress(s)
  echo("getContent address: <", toHex(address.id), ">")
  try:
    let resp = Get(casClient, address)
    let str = parseHexStr(toHex(resp.data))
    echo(&"I got a new post: {str}")
    return str
  except Exception as e:
    echo(&"Exception: {e.msg}")

when isMainModule:
  echo("Running CAS tests")
  doAssert 1 == 1
  let id = postContent("hello")
  echo("ID:", id)
  let res = getContent(id)
  echo("getContent res:", res)
  # TODO: Run retrieve test on this ID
