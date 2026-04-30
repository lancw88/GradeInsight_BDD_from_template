#!/bin/bash

# GradeInsight 虛擬環境設置腳本
# 此腳本將自動設置虛擬環境並安裝所有必要的依賴

set -e  # 任何命令失敗時退出

VENV_DIR="venv"
PYTHON_CMD="python3"

echo "================================"
echo "GradeInsight 虛擬環境設置工具"
echo "================================"
echo ""

# 檢查 Python 版本
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "✓ 檢測到 Python 版本: $PYTHON_VERSION"
echo ""

# 檢查是否已存在虛擬環境
if [ -d "$VENV_DIR" ]; then
    echo "⚠ 虛擬環境已存在，將使用現有環境"
else
    echo "📦 正在建立虛擬環境..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo "✓ 虛擬環境建立成功"
fi

echo ""
echo "🔄 啟動虛擬環境..."
source "$VENV_DIR/bin/activate"

echo "✓ 虛擬環境已啟動"
echo ""

echo "📥 安裝依賴套件..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
pip install -r requirements.txt

echo ""
echo "✓ 所有依賴已安裝完成"
echo ""

# 初始化數據庫
echo "🗄️  初始化數據庫..."
python -c "from gradeinsight.app import create_app; app = create_app(); app.app_context().push(); from gradeinsight.models import db; db.create_all()"

echo "✓ 數據庫已初始化"
echo ""
echo "================================"
echo "✅ 設置完成！"
echo "================================"
echo ""
echo "接下來請執行以下命令啟動應用程序："
echo ""
echo "  source venv/bin/activate"
echo "  python gradeinsight/cli.py"
echo ""
