#!/bin/bash
# 测试路径逻辑
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "SCRIPT_DIR: $SCRIPT_DIR"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
echo "PROJECT_ROOT: $PROJECT_ROOT"
DATA_COLLECTOR_DIR="$PROJECT_ROOT/data_collector"
echo "DATA_COLLECTOR_DIR: $DATA_COLLECTOR_DIR"
