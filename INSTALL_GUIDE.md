# 🔄 版本更新和安裝指南

## 問題說明
如果 `pip install` 仍然嘗試安裝舊版本（如 `pandas==2.1.0`），這通常是由於 **pip 緩存** 的問題。

## 解決方案

### 方案 1️⃣ 快速清理和重新安裝（推薦）
如果虛擬環境已存在，只需清理緩存並重新安裝：

```bash
source venv/bin/activate
./quick_reinstall.sh
```

**這個腳本將：**
- 清除 pip 緩存
- 卸載所有舊套件
- 使用最新版本重新安裝（優先預編譯 wheel）
- 預計耗時：2-5 分鐘

### 方案 2️⃣ 完整重置（乾淨起始）
如果快速方案不奏效，執行完整重置：

```bash
./clean_install.sh
```

**這個腳本將：**
- 清除 pip 緩存
- 刪除舊虛擬環境
- 建立全新虛擬環境
- 安裝最新依賴
- 初始化數據庫
- 預計耗時：5-10 分鐘

## 📦 已更新的套件版本

| 套件 | 舊版本 | 新版本 | 優化 |
|------|--------|--------|------|
| Flask | 2.3.3 | 3.0.0 | 效能改進 |
| Flask-SQLAlchemy | 3.0.5 | 3.1.1 | 相容性修復 |
| SQLAlchemy | 2.0.21 | 2.0.23 | 穩定性修復 |
| **pandas** | **2.1.0** | **2.1.4** | ⭐ **編譯卡頓修復** |
| matplotlib | 3.8.0 | 3.8.2 | 效能優化 |
| PyPDF2 | 3.0.1 | 3.0.1 | 最新穩定版 |
| behave | 1.2.7 | 1.2.6 | 最新穩定版 |

## 🚀 安裝優化

### 先前問題
- `pandas==2.1.0` 每次都需要從源碼編譯（`.tar.gz`）
- 編譯時特別容易卡頓，耗時 10+ 分鐘

### 現在的改進
- ✅ 使用 `--prefer-binary` 優先選擇預編譯 wheel
- ✅ 使用 `--no-cache-dir` 減少磁碟占用
- ✅ `pandas==2.1.4` 有更多預編譯版本可用
- ✅ 預期安裝時間：**2-5 分鐘**

## 🔍 驗證安裝

安裝完成後，檢查版本：

```bash
python -c "import pandas; print(f'pandas: {pandas.__version__}')"
python -c "import flask; print(f'Flask: {flask.__version__}')"
python -c "import sqlalchemy; print(f'SQLAlchemy: {sqlalchemy.__version__}')"
```

應該看到：
```
pandas: 2.1.4
Flask: 3.0.0
SQLAlchemy: 2.0.23
```

## 📝 使用說明

### 第一次安裝或環境無效
```bash
./clean_install.sh
```

### 只更新套件版本
```bash
source venv/bin/activate
./quick_reinstall.sh
```

### 手動逐步操作
```bash
# 清除緩存
pip cache purge

# 重新安裝
pip install --prefer-binary --no-cache-dir --upgrade -r requirements.txt

# 初始化數據庫
python -c "from gradeinsight.app import create_app; app = create_app(); app.app_context().push(); from gradeinsight.models import db; db.create_all()"
```

## ⚠️ 常見問題

### Q: 仍然卡在編譯 pandas
A: 執行 `pip cache purge` 後再試一次，確保未使用緩存。

### Q: 某些套件安裝失敗
A: 檢查網路連線，或嘗試只安裝必要套件：
```bash
pip install Flask pandas SQLAlchemy --prefer-binary
```

### Q: 虛擬環境創建失敗
A: 確保有足夠的磁碟空間，手動重試：
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install --prefer-binary -r requirements.txt
```

---

**最後更新**：2026-05-02
**Python 版本**：3.10+
**主要依賴**：pandas 2.1.4（預編譯 wheel）
