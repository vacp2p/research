# XXX: Shouldn't it be pb3?
import sync_pb2
msg = sync_pb2.Record()
msg.header.version = 1
# assert based on type and length
msg.header.type = 1
msg.header.length = 10
msg.payload.message.group_id = "foo"
msg.payload.message.timestamp = 10
msg.payload.message.body = "hello"

# need to be bytes
acks = sync_pb2.Record()
acks.header.version = 1
# XXX: not showing up if version is 0
acks.header.type = 0
acks.header.length = 10
acks.payload.ack.id.extend(["a", "b"])
