# GradeInsight 成績管理系統

GradeInsight 是提供教師與課程助教使用的成績管理工作台。後端使用 FastAPI，前端使用 Streamlit；成績資料儲存於 SQLite，提供 CSV／Excel 匯入、成績分析、個別學生管理、報表匯出及加密備份。系統啟動時會在空資料庫中建立 30 位模擬學生，方便立即展示與試用。

## 功能

- CSV、Excel（`.xls`、`.xlsx`、`.xlsm`）成績匯入，支援繁中或英文欄名、最多 500 筆、資料預覽、格式驗證、重複略過及錯誤摘要。
- 班級成績直方圖、平均數、中位數、眾數、標準差、變異數、最高／最低分、等級分布、及格率、優良率與離群值分析。
- 依及格線與風險範圍識別學生、排序及匯出需協助名單。
- 自訂加權平均、簡單平均、最高分優先評分方案，提供套用前預覽與撤銷。
- 個人成績、班級排名、班級平均、平時／期中／期末趨勢及修改稽核紀錄。
- 單一成績修改需填寫原因，修改後重新計算總成績，可撤銷最近一次修改。
- 自動調整規則的建立、預覽、人工確認、重複套用防護及撤銷。
- 班級或個人報告匯出為 CSV、Excel、PDF；支援自訂標題、隱私遮蔽及 PDF 識別 QR Code。
- 每日午夜建立 AES-256-GCM 加密備份，保留最近 30 天且最多 30 份；支援手動備份、備份紀錄及選配管理員 Webhook 警示。

## 專案結構

```text
backend/
  main.py                       FastAPI 路由、API 驗證、啟動與排程
  models/schemas.py             Pydantic 請求模型與欄位驗證
  services/
    storage.py                  SQLite 儲存與稽核紀錄
    student_service.py          學生資料、模擬資料、總成績與詳情
    import_service.py           CSV／Excel 解析與匯入檢核
    analysis_service.py         統計、分布、離群值與風險名單
    scoring_service.py          評分方案與自動調整規則
    report_service.py           CSV／Excel／PDF 報表
    backup_service.py           AES-256-GCM 備份與保留策略
frontend/
  streamlit_app.py              繁體中文互動介面，透過 requests 呼叫 API
requirements.txt                固定版本的 Python 套件
data/                            執行時建立資料庫與本機加密備份
```

## 環境需求

- Python 3.10
- GitHub Codespaces 或一般 Linux／macOS 環境
- 不需要 Docker

請從專案根目錄執行下列安裝步驟：

```bash
python3.10 --version
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 啟動方式

開啟兩個終端機，兩邊都先切換至專案根目錄並啟用同一個虛擬環境：

```bash
source .venv/bin/activate
```

### 1. 啟動後端 API

在第一個終端機執行：

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API 文件位於 `http://127.0.0.1:8000/docs`，健康檢查位於 `http://127.0.0.1:8000/api/health`。Codespaces 首次啟動時，請將 8000 連接埠設為 Private；前端透過容器內的 `127.0.0.1:8000` 呼叫 API。

### 2. 啟動前端介面

在第二個終端機執行：

```bash
streamlit run frontend/streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

Codespaces 會提供 8501 連接埠的瀏覽器網址；將此連接埠設為 Private 或 Public，依課程資料的存取需求決定。若後端使用非預設位址，可在前端側邊欄修改 API 位址，或設定 `GRADEINSIGHT_API_URL`。

### 選用安全設定

本機展示可直接啟動。若要保護 API，請在**後端與前端兩個終端機**設定相同的 Token，再分別啟動服務：

```bash
export GRADEINSIGHT_API_TOKEN="請替換成自行產生的長隨機字串"
```

AES 備份金鑰預設會建立在 `data/backups/.local-backup.key`，檔案權限限制為目前使用者。正式環境建議從 Secret Manager 注入 32 位元組金鑰的 64 位十六進位字串，並另外安全保存金鑰：

```bash
export GRADEINSIGHT_BACKUP_KEY="64位十六進位字串"
```

可選擇設定 `GRADEINSIGHT_ADMIN_WEBHOOK`，備份失敗時系統會向該 URL 傳送 JSON `{ "text": "..." }` 警示；未設定時會將警示寫入後端日誌。資料庫位置可用 `GRADEINSIGHT_DB` 覆寫，預設為 `data/gradeinsight.sqlite3`。

## 常見問題排除

- **找不到 Python 3.10**：確認 `python3.10 --version` 可執行，並使用該直譯器建立 `.venv`。容器若只有其他 Python 版本，請先安裝 Python 3.10，避免用錯版本建立虛擬環境。
- **前端顯示無法連線後端**：確認後端終端機仍在執行、網址為 `http://127.0.0.1:8000`，並確認 Codespaces 沒有終止該程序。
- **API 回傳 401 未授權**：若後端設定了 `GRADEINSIGHT_API_TOKEN`，前端也必須設定完全相同的值；本機未設定 Token 時不會啟用 API Token 驗證。
- **匯入被略過或出現欄位錯誤**：請使用範本標題 `學號、姓名、班級、平時、期中、期末、出席率、缺席次數`；學號、姓名及三項成績不可空白，成績需介於 0 至 100，且單次最多 500 位學生。
- **Excel 檔案無法讀取**：確認檔案未損毀且副檔名為 `.xls`、`.xlsx` 或 `.xlsm`。舊版 `.xls` 由 `xlrd` 讀取，新版格式由 `openpyxl` 讀取。
- **無法建立加密備份**：檢查 `data/backups` 是否可寫入。若設定 `GRADEINSIGHT_BACKUP_KEY`，須為有效的 64 位十六進位字串；更換金鑰後，舊備份仍需舊金鑰才能解密。
- **提醒沒有寄給學生**：目前批次提醒會建立系統內模擬紀錄，不會寄送郵件或簡訊；實際傳送需另行整合並設定郵件／簡訊服務。
- **排程重複執行**：請以單一 Uvicorn worker 啟動後端；多 worker 部署前應改用獨立排程器，避免每個 worker 都執行午夜備份。

## 安全與資料範圍

此專案提供教師工作台的基本 API Token 保護，但未包含使用者帳號、角色管理或完整登入流程。正式部署前，請設定 API Token、限制網路存取並使用 HTTPS。備份依需求僅提供建立、保留與紀錄功能，不提供資料還原；請另行制定還原程序與金鑰保管政策。

批次提醒目前為模擬紀錄。資料匯入與報表可處理學生個人資料，請依校方規範選擇隱私級別並限制檔案存取。