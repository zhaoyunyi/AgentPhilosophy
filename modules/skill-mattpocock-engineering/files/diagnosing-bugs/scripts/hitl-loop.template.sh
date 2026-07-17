#!/usr/bin/env bash
set -euo pipefail

artifact_dir="${TMPDIR:-/tmp}/diagnosing-bugs-hitl"
mkdir -p "$artifact_dir"

echo "1. 执行触发问题所需的人工步骤。"
echo "2. 完成后按回车，让脚本采集项目指定的日志或截图。"
read -r

# 按项目替换为只读采集命令，例如：
# cp /path/to/application.log "$artifact_dir/application.log"

echo "证据目录：$artifact_dir"
