#!/bin/bash

# 快速清理 pip 緩存並重新安裝依賴
# 當 pip 仍然使用舊版本時使用

echo "🧹 快速清理 pip 緩存..."
pip cache purge

echo "🔄 移除舊套件..."
pip uninstall -y -r requirements.txt 2>/dev/null || true

echo "📥 重新安裝所有依賴..."
pip install --prefer-binary --no-cache-dir --upgrade -r requirements.txt

echo "✓ 依賴已重新安裝"
