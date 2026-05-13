# full path: C:/Users/Hubar Tech/Downloads/Soccho/Soccho/compile_protos.sh
#!/usr/bin/env sh
set -eu

PROTO_FILE="shared/proto/soccho.proto"
PROTO_DIR="shared/proto"

OUT_DIRS="
gateway/app/grpc_client/generated
auth/grpc_infra/generated
social/grpc_infra/generated
transaction/grpc_infra/generated
notification/grpc_infra/generated
"

for OUT_DIR in $OUT_DIRS; do
  mkdir -p "$OUT_DIR"
  python -m grpc_tools.protoc \
    -I"$PROTO_DIR" \
    --python_out="$OUT_DIR" \
    --grpc_python_out="$OUT_DIR" \
    "$PROTO_FILE"
done

echo "Proto compilation completed for all services."