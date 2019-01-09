all: protoc_python

clean:
	rm -rf sync_pb2.py*

protoc_python: sync.proto
	protoc -I=. --python_out=. ./sync.proto

run:
	python -i sync.py
