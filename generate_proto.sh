#!/usr/bin/env bash
python -m grpc_tools.protoc \
  --proto_path=./grpc_service/proto \
  --python_out=./backend \
  --grpc_python_out=./backend \
  grpc_service/proto/llm_quality.proto