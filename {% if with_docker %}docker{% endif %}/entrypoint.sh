#!/bin/sh
set -e

# 스택별 런타임 분기(예: GPU 미검출 시 CPU 강제)가 필요하면 여기에 추가하세요.

exec "$@"
