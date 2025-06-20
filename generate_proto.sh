#!/usr/bin/env bash
python -m grpc_tools.protoc \
  --proto_path=./proto \
  --python_out=./backend \
  --grpc_python_out=./backend \
  proto/llm_quality.proto
