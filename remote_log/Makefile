all: casserver nsserver node

casserver: src/casserver.nim src/cas_service_pb.nim src/cas_service_twirp.nim
	nim c -o:bin/cas src/casserver.nim

nsserver: src/nsserver.nim src/ns_service_pb.nim src/ns_service_twirp.nim
	nim c -o:bin/ns src/nsserver.nim

node: src/node.nim src/remote_log_pb.nim src/remote_log_twirp.nim
	nim c -o:bin/node src/node.nim

castest: tests/castest.nim
	nim c --r tests/castest.nim

test: castest

%_pb.nim %_twirp.nim: %.proto
	nimtwirp_build -I:. --out:. $^
