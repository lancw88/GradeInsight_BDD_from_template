# 🎓 GradeInsight - 教師成績管理系統

一個以 Python、Flask-SQLAlchemy 和 Click 建立的成績管理 CLI 專案，包含成績匯入、分析、報告匯出及資料庫管理功能。此專案目前不是可透過 `backend.main` 啟動的 Web 後端，也沒有提供 HTTP API。

## ✨ 功能特性

### 目前功能狀態
| 功能 | 目前可用方式 | 狀態 |
|------|-------------|------|
| CSV/Excel 成績匯入 | CLI：`import-grades from-csv`、`from-excel` | 可用 |
| 成績分布、統計摘要 | CLI：`analyze distribution`、`summary` | 可用 |
| 風險學生、學生詳情 | CLI：`students at-risk`、`details` | 可用 |
| 班級、個人及統計報告 | CLI：Excel/CSV 匯出 | 可用；不提供 PDF 匯出命令 |
| 評分方案、編輯成績、調整規則 | 部分服務層程式碼，沒有 CLI 管理命令 | 尚未完成使用者入口與測試 |
| 備份與還原 | CLI 可建立、列出、清理備份；沒有還原命令 | 有限制，詳見下方 |
| Web 後端 | `gradeinsight.app` 只有 Flask app factory，沒有 Web API 路由；不存在 `backend.main` | 未提供 |

## 🚀 快速開始

### 系統要求

- Python 3.9 或更新版本（`pandas 2.1.4` 不支援 Python 3.8）
- pip

### 已知限制

- 專案沒有 `backend.main`、Web server 啟動入口或 HTTP API；目前主要介面是 CLI。
- 評分方案、成績編輯、調整規則已有部分服務層程式碼，但沒有 CLI 管理命令，現有測試也未涵蓋這些流程。
- 備份只有建立、列出和清理 CLI 命令；沒有還原 CLI 命令，且加密金鑰只在單次程式執行期間有效。不要依賴它保存重要資料。
- `gradeinsight/config.py` 和備份服務目前將資料、日誌及備份路徑寫死為 `/workspaces/GradeInsight_BDD_from_template/...`。若專案放在其他路徑，需先調整設定。
- 設定使用的資料庫路徑是 `data/gradeinsight.db`。若資料目錄內另有 `gradeinsight.sqlite3`，目前設定不會自動使用該檔案。

#### 1️⃣ **方式一：自動化安裝（推薦）**

```bash
# 切換到項目目錄
cd /workspaces/GradeInsight_BDD_from_template

# 賦予執行權限
chmod +x setup.sh

# 執行安裝腳本
./setup.sh
```

此腳本將自動：
- ✅ 建立虛擬環境
- ✅ 安裝所有依賴
- ✅ 初始化數據庫
- ✅ 準備系統啟動

#### 2️⃣ **方式二：手動安裝**

```bash
# 1. 建立虛擬環境
python3 -m venv venv

# 2. 啟動虛擬環境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 初始化數據庫
python gradeinsight/cli.py database init
```

### 啟動應用程序

```bash
# 確保虛擬環境已啟動
source venv/bin/activate

# 查看 CLI 指令
python gradeinsight/cli.py --help

# 查看特定功能的指令
python gradeinsight/cli.py analyze --help
```

請在專案根目錄執行上述命令。`python gradeinsight/cli.py --help` 會列出 CLI 指令；執行功能時需帶上對應子命令。`python -c "import backend.main"` 會失敗，因為專案沒有 `backend/main.py`。若需求是 Web 伺服器，目前程式碼尚未提供可啟動的 API。

## 📋 使用指南

### 匯入成績 (US-001)

```bash
# 從 CSV 文件匯入
python gradeinsight/cli.py import-grades from-csv data/sample_grades.csv

# 從 Excel 文件匯入
python gradeinsight/cli.py import-grades from-excel data/grades.xlsx

# ✓ 系統會進行數據驗證並要求確認
# ✓ 匯入後自動記錄審計日誌
```

### 查看成績分布 (US-002)

```bash
# 查看成績直方圖和統計指標
python gradeinsight/cli.py analyze distribution --width 10

# 查看統計分析摘要
python gradeinsight/cli.py analyze summary
```

### 識別風險學生 (US-003)

```bash
# 獲取需要幫助的學生列表
python gradeinsight/cli.py students at-risk --pass-line 60 --risk-range 10

# 查看特定學生詳情
python gradeinsight/cli.py students details S001

# 輸出包含：
# - 各科成績及權重
# - 最終分數（加權平均）
# - 班級排名
# - 與班級平均分的對比
```

### 導出報告 (US-005)

```bash
# 導出班級成績表
python gradeinsight/cli.py export class-report --format xlsx
python gradeinsight/cli.py export class-report --format csv

# 導出個人成績單
python gradeinsight/cli.py export individual S001

# 導出統計分析報告
python gradeinsight/cli.py export statistics

# 📁 文件自動保存到：data/exports/
```

### 備份管理 (US-010)

```bash
# 創建備份
python gradeinsight/cli.py backup create

# 列出所有備份
python gradeinsight/cli.py backup list

# 清理過期備份 (>30天)
python gradeinsight/cli.py backup cleanup

# 備份需手動執行；CLI 不會啟動每日排程，也沒有還原子命令
```

**備份限制：** 備份服務目前使用執行時產生、只存在記憶體的 Fernet 金鑰，程式重新啟動後無法用新金鑰解密舊備份。現階段請勿將此功能當成可靠的長期災難復原方案。每日排程類別雖存在，但 CLI 不會啟動它。

### 數據庫管理

```bash
# 初始化數據庫
python gradeinsight/cli.py database init

# 查看數據庫狀態
python gradeinsight/cli.py database status

# ⚠️ 重置數據庫 (會刪除所有數據)
python gradeinsight/cli.py database reset
```

## 📊 項目結構

```
GradeInsight_BDD_from_template/
├── gradeinsight/                      # 主應用程序包
│   ├── __init__.py                    # 包初始化
│   ├── app.py                         # Flask 應用工廠（目前沒有 API 路由）
│   ├── cli.py                         # CLI 主程序
│   ├── config.py                      # 配置管理
│   ├── models/
│   │   └── __init__.py               # SQLAlchemy 數據模型
│   │       └── Student, Grade, GradeComponent, ScoringScheme, AuditLog, BackupLog
│   ├── services/
│   │   ├── __init__.py               # 成績匯入服務 (US-001)
│   │   ├── analysis.py               # 成績分析服務 (US-002, 003, 006, 007)
│   │   └── scoring.py                # 評分方案和編輯 (US-004, 008, 009)
│   ├── export/
│   │   └── __init__.py               # 導出服務 (US-005)
│   │       └── Excel/CSV 匯出
│   └── backup/
│       └── __init__.py               # 備份服務 (US-010)
│           └── 備份與清理（加密金鑰目前不持久化）
├── data/
│   ├── gradeinsight.db               # SQLite 數據庫
│   ├── uploads/                      # 上傳的文件
│   ├── exports/                      # 導出的報告
│   ├── backups/                      # 備份文件
│   ├── logs/                         # 應用日誌
│   └── sample_grades.csv             # 示例數據
├── tests/
│   └── test_gradeinsight.py          # 單元測試
├── requirements.txt                  # Python 依賴
├── setup.sh                          # 安裝腳本
└── README.md                         # 本文檔
```

## 🗄️ 數據模型

### 核心表

| 表名 | 用途 | 主要字段 |
|------|------|--------|
| `students` | 學生信息 | id, student_id, name, class_name, email |
| `grade_components` | 成績組件 | id, name, weight, max_score, component_type |
| `grades` | 成績記錄 | id, student_id, component_id, score, remarks |
| `scoring_schemes` | 評分方案 | id, name, calculation_method, rules |
| `adjustment_rules` | 自動調整規則 | id, name, condition, rule_type, adjustment_value |
| `audit_logs` | 審計日誌 | id, operation_type, old_value, new_value, reason |
| `backup_logs` | 備份日誌 | id, backup_file, status, created_at |

## 📥 兼容的文件格式

### 匯入格式

**CSV 範例：**
```csv
student_id,name,class_name,email,期中考,期末考,作業
S001,王小明,一年級甲班,wang@example.com,85,92,88
S002,李小華,一年級甲班,li@example.com,78,82,85
```

**Excel 格式**：
- 支持 .xlsx 和 .xls
- 同樣的列結構

### 目前提供的導出格式

- 班級報告：Excel (`.xlsx`) 或 CSV (`.csv`)
- 個人成績單：Excel (`.xlsx`)
- 統計摘要：Excel (`.xlsx`)
- 目前沒有 PDF 匯出 CLI 命令

## 🧪 運行測試

```bash
# 運行目前的 unittest 測試（目前測試涵蓋資料模型建立）
python -m unittest discover tests/
```

目前測試檔案只有少量模型建立測試；README 中列出的完整功能尚未由測試套件全面驗證。

## 📝 示例工作流程

### 典型使用場景

1. **學期開始**：
   ```bash
   python gradeinsight/cli.py database init
   python gradeinsight/cli.py import-grades from-csv semester1_grades.csv
   ```

2. **定期分析**：
   ```bash
   python gradeinsight/cli.py analyze summary
   python gradeinsight/cli.py students at-risk --pass-line 60
   ```

3. **導出報告**：
   ```bash
   python gradeinsight/cli.py export class-report --format xlsx
   python gradeinsight/cli.py export statistics
   ```

4. **備份數據**：
   ```bash
   python gradeinsight/cli.py backup create
   python gradeinsight/cli.py backup list
   ```

## 🐛 故障排查

### 問題 1: 匯入失敗 - "數據驗證失敗"

**解決方案**：
- ✓ 確保 CSV 包含必需的列：`student_id`, `name`
- ✓ 檢查成績值是否在 0-100 之間
- ✓ 確保沒有空行或不完整的記錄

### 問題 2: 數據庫錯誤 - "DatabaseError"

**解決方案**：
```bash
# 1. 查看數據庫狀態
python gradeinsight/cli.py database status

# 2. 重新初始化数据庫
python gradeinsight/cli.py database reset
python gradeinsight/cli.py database init
```

### 問題 3: 導出文件不存在

**解決方案**：
```bash
# 確保導出目錄存在
mkdir -p data/exports

# 檢查文件權限
chmod 755 data/exports
```

## 📚 技術棧

| 組件 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.9+ | 核心語言 |
| **Flask** | 2.3.3 | 應用框架工廠 |
| **Flask-SQLAlchemy** | 3.0.5 | ORM 整合 |
| **SQLAlchemy** | 2.0.21 | ORM 和數據庫 |
| **Pandas** | 2.1.4 | 數據處理 |
| **OpenpyXL** | 3.1.2 | Excel 操作 |
| **Click** | 8.1.7 | CLI 框架 |
| **Cryptography** | 41.0.3 | 備份加密（目前金鑰未持久化） |

## 📖 API 參考

### 主要服務類

```python
# 成績匯入
from gradeinsight.services import GradeImportService
GradeImportService.import_grades(df)

# 成績分析
from gradeinsight.services.analysis import GradeAnalysisService
GradeAnalysisService.get_grade_distribution()
GradeAnalysisService.identify_at_risk_students()

# 評分方案
from gradeinsight.services.scoring import ScoringSchemeService
ScoringSchemeService.create_scheme(...)
ScoringSchemeService.apply_scheme(...)

# 備份（目前金鑰不會跨程式執行保存；請勿用於重要資料的唯一備份）
from gradeinsight.backup import BackupService
BackupService.create_backup()
BackupService.restore_backup(filename)
```

以上是 Python 服務層介面，不代表所有功能都有 CLI 命令或完整測試；例如 `restore_backup` 目前只能透過程式呼叫，CLI 沒有還原子命令。

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！

## 📄 許可證

MIT License

---

文件依目前專案程式碼與 CLI 指令更新：2026-10-04
