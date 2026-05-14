# GradeInsight 系統構建指南

你現在是一位資深的 Python 全端架構師。請閱讀位於 `@requirements/` 目錄下的 10 個 User Story 檔案，並根據這些需求構建一個完整、穩健且專業的系統。

## 1. 專案架構規範 (Architecture)

請嚴格遵守「職責分離」原則，將系統拆分為以下模組化的目錄結構：

### Backend 層級
- **backend/**: 使用 FastAPI 框架
  - **main.py**: 定義 API 路由與進入點
  - **services/**: 封裝所有核心邏輯（如：成績統計、不及格篩選、數據處理）
  - **models/**: 定義數據結構（Pydantic Models）

### Frontend 層級
- **frontend/**: 使用 Streamlit 框架
  - **streamlit_app.py**: 構建互動式網頁介面
  - 透過 `requests` 庫與後端 API 通訊

## 2. 技術約束與環境 (Tech Constraints)

- **語言**：全程使用 Python 3.10
- **環境**：執行於 GitHub Codespaces，不需要 Docker
- **執行方式**：請使用 Python 虛擬環境（venv）啟動系統
- **介面語言**：所有 UI 文字、圖表標題、提示訊息請統一使用 **繁體中文**
- **穩健性要求**：必須包含基本的錯誤處理（Error Handling），例如當檔案格式錯誤或數據缺失時，系統應顯示友善的警告訊息而非崩潰

## 3. 模擬數據與展示 (Data Simulation)

為了方便立即展示功能，請在後端內建一個「生成模擬數據」的功能，隨機產生 30 位學生的成績資料（包含姓名、學號、平時、期中、期末分數）。

## 4. 任務步驟 (Tasks)

請不要一次產出所有代碼。請按照以下順序執行：

1. **第一步**：簡要總結你對這 10 個需求的理解，並列出你預計建立的檔案清單
2. **第二步**：首先產出 `backend/` 的完整代碼（包含 models, services 與 main.py）
3. **第三步**：產出 `frontend/streamlit_app.py` 的代碼
4. **第四步**：提供一個 `requirements.txt` 檔案，包含所有必要的套件
5. **第五步**：新增 `README.md`，內容需包含專案簡介、目錄結構、環境需求、安裝步驟、啟動方式（後端與前端）、以及常見問題排除（Troubleshooting）

## 5. 啟動指引

最後，請告訴我如何在終端機中使用指令分別啟動後端 API 與前端介面，並確保這些指令與說明也完整寫入 `README.md`。
