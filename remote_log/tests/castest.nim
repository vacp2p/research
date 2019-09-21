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

when isMainModule:
  echo("Running CAS tests")
  doAssert 1 == 1
  let id = postContent("hello")
  echo("ID:", id)
  # TODO: Run retrieve test on this ID
