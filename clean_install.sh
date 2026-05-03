#!/bin/bash

# GradeInsight 虛擬環境重置和清理腳本
# 用於清除 pip 緩存和廢棄的虛擬環境，然後重新安裝

set -e

VENV_DIR="venv"
PYTHON_CMD="python3"

echo "================================"
echo "GradeInsight 環境清理和重置"
echo "================================"
echo ""

# 清除 pip 緩存
echo "🗑️  清除 pip 緩存..."
pip cache purge 2>&1 | tail -1
echo "✓ pip 緩存已清除"
echo ""

# 移除舊的虛擬環境
if [ -d "$VENV_DIR" ]; then
    echo "🔄 移除舊的虛擬環境..."
    rm -rf "$VENV_DIR"
    echo "✓ 舊虛擬環境已移除"
else
    echo "✓ 未發現舊虛擬環境"
fi

echo ""
echo "📦 正在建立新虛擬環境..."
$PYTHON_CMD -m venv "$VENV_DIR"
echo "✓ 虛擬環境建立成功"
echo ""

echo "🔄 啟動虛擬環境..."
source "$VENV_DIR/bin/activate"
echo "✓ 虛擬環境已啟動"
echo ""

echo "📥 升級 pip、setuptools 和 wheel..."
pip install --upgrade pip setuptools wheel --quiet
echo "✓ 基礎工具已升級"
echo ""

echo "📥 安裝依賴套件..."
echo "  使用最新版本（優先預編譯 wheel，避免編譯卡頓）..."
pip install --prefer-binary --no-cache-dir -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ 所有依賴已安裝完成"
else
    echo ""
    echo "⚠ 安裝過程中出現警告"
    exit 1
fi

echo ""

# 初始化數據庫
echo "🗄️  初始化數據庫..."
python -c "from gradeinsight.app import create_app; app = create_app(); app.app_context().push(); from gradeinsight.models import db; db.create_all()"
echo "✓ 數據庫已初始化"
echo ""

echo "================================"
echo "✅ 環境重置完成！"
echo "================================"
echo ""
echo "接下來請執行以下命令啟動應用程序："
echo ""
echo "  source venv/bin/activate"
echo "  python gradeinsight/cli.py"
echo ""
