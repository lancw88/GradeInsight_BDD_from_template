# GradeInsight 系統構建指南（完整版 - 含詳細功能規格）

## 概述
你現在是一位資深的 Python 全端架構師。請根據本指南和 `requirements_full/` 目錄下的 10 個 User Story 及詳細 Feature 檔案，構建一個完整、穩健且專業的成績管理系統。

---

## 1. 專案架構規範

### 1.1 系統整體架構
```
gradeinsight/
├── backend/                    # FastAPI 後端服務
│   ├── main.py                # API 路由定義
│   ├── models/                # Pydantic 資料模型
│   ├── services/              # 核心業務邏輯（10個服務）
│   ├── database/              # SQLAlchemy 設定和 ORM 模型
│   ├── config.py              # 環境和設定
│   └── utils.py               # 工具函式
│
├── frontend/                   # Streamlit 前端應用程式
│   ├── streamlit_app.py       # 主要應用程式
│   ├── pages/                 # 10個功能頁面
│   ├── components/            # UI 元件庫
│   └── utils/                 # 前端工具
│
├── tests/                      # 自動化測試（pytest）
│   ├── unit/                  # 單元測試
│   └── integration/           # 整合測試
│
└── data/                       # 資料儲存目錄
```

### 1.2 技術棧核心
| 層級 | 技術選擇 | 版本 |
|------|---------|------|
| Web框架 | FastAPI | ^0.104 |
| 資料驗證 | Pydantic | ^2.0 |
| ORM | SQLAlchemy | ^2.0 |
| 前端 | Streamlit | ^1.28 |
| 資料處理 | Pandas | ^2.1 |
| 圖表 | Matplotlib/Plotly | ^3.8/^5.17 |
| 測試 | pytest | ^7.4 |
| 加密 | cryptography | ^41.0 |
| 定時任務 | APScheduler | ^3.10 |

---

## 2. 功能模組清單 - Release 1 MVP（核心功能）

本階段實現 4 個核心功能：

1. **US-001 匯入學生成績** - 支援 CSV/Excel 檔案上傳、資料驗證、匯入預覽
2. **US-002 檢視成績分布** - 直方圖展示、統計指標、段位自訂、圖表匯出
3. **US-003 識別需要幫助的學生** - 自動篩選不及格和風險學生、排序、批次通知
4. **US-005 匯出成績報告** - 多格式匯出(PDF/Excel/CSV)、班級報告、個人成績單

### 詳細功能規格

詳細的 Feature 驗收場景已儲存在 `requirements_full/` 目錄下：在實現每個功能時，參考對應目錄下的 `.md` 檔案（User Story 描述）和 `.feature` 檔案（Gherkin 驗收場景）。

---

## 3. 核心服務層設計 - Release 1

### Services 模組劃分（Phase 1 所需）
| 服務 | 主要職責 |
|------|--------|
| import_service.py | 檔案上傳、驗證、預覽、匯入 |
| grade_service.py | 成績查詢、編輯、計算 |
| statistics_service.py | 統計分析、指標計算 |
| export_service.py | PDF/Excel/CSV 匯出，多格式支援 |
| notification_service.py | 郵件通知、提醒傳送 |
| data_generator.py | 模擬資料產生（30名學生） |

---

## 4. API 路由概覽 - Release 1

```python
# 成績管理
POST   /api/grades/import           # 檔案匯入
GET    /api/grades/student/{id}     # 查詢學生成績
PUT    /api/grades/student/{id}     # 編輯成績

# 統計分析
GET    /api/statistics/summary      # 摘要統計
GET    /api/statistics/detailed     # 詳細分析

# 匯出報告
POST   /api/export/class-report     # 班級報告
POST   /api/export/student-report/{id}  # 個人成績單
POST   /api/export/batch            # 批次匯出

# 資料初始設定
POST   /api/data/generate-sample    # 產生模擬資料
```

---

## 5. 前端頁面映射 - Release 1

| 頁面 | User Story | 功能 |
|------|-----------|------|
| 01_匯入成績 | US-001 | 檔案上傳、預覽、匯入 |
| 02_成績分布 | US-002 | 直方圖、統計指標、匯出 |
| 03_風險學生識別 | US-003 | 篩選、排序、傳送通知 |
| 04_報告匯出 | US-005 | 多格式匯出、批次匯出 |

---

## 6. 開發優先順序

### Phase 1: MVP（Release 1）
1. 設定專案結構和資料庫
2. 實現 `import_service` 和 `grade_service`
3. 實現 API 路由和前端頁面（US-001、US-002、US-003、US-005）
4. **編寫完整的單元測試和整合測試（覆蓋率 >= 80%）**

---

## 7. 環境設定

### 8.1 Python 版本和依賴安裝
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 8.2 啟動命令

**後端：**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**前端：**
```bash
cd frontend
streamlit run streamlit_app.py --server.port=8501
```

**執行測試：**
```bash
pytest --cov=backend --cov-report=html
```

---

## 8. 品質保證要求

### 測試覆蓋率目標
- 整體程式碼覆蓋率：≥ 80%
- Services 層：≥ 90%
- Models 層：≥ 85%

### 測試類型
- ✅ 單元測試：每個 service 方法
- ✅ 整合測試：API 端點和工作流程
- ✅ 場景測試：Feature檔案中的 Gherkin 場景
- ✅ 邊界測試：異常情況和驗證

### 提交前檢查清單
- [ ] 所有 pytest 測試通過
- [ ] 程式碼覆蓋率 ≥ 80%
- [ ] 所有 10 個 US 的 Feature 場景都有對應測試
- [ ] API 文件產生（FastAPI 的 Swagger UI）
- [ ] 程式碼無明顯邏輯錯誤

---

## 9. 關鍵交付件

```
需要產生的檔案和資料夾：
✅ backend/ - 完整後端程式碼
✅ frontend/ - 完整前端程式碼
✅ tests/ - 完整的 pytest 測試套件
✅ data/database.db - 初始設定的 SQLite 資料庫
✅ requirements.txt - 完整依賴清單
✅ .env.example - 環境變數範本
✅ README.md - 快速開始指南
```
