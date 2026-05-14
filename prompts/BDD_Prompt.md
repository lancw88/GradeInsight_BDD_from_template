# 任務目標：
請根據目錄下的所有 .feature 檔案，實作一個完整的 Python 系統，並同步生成對應的自動化系統驗證測試。

## 執行指令與規範：

- 邏輯依據： 嚴格遵循 requirements_full/*.feature 中定義的 Gherkin 情境 (Given-When-Then)。

- 系統開發： 使用 Python 撰寫核心邏輯與介面，確保功能完整實現。

## 測試開發：

- 使用 Python 的 BDD 測試框架（如 behave 或 pytest-bdd）撰寫測試腳本（Step Definitions）。

- 測試必須能夠逐一驗證 .feature 檔案中的所有 Scenarios。

## 交付物清單：

- 完整的系統程式碼。

- 完整的測試程式碼（含 steps 目錄與環境設定）。

- requirements.txt（需包含系統執行與測試所需之套件，如 behave）。

- README.md：必須詳細說明：

  - 如何建立並啟動 Python 虛擬環境 (venv)。

  - 如何啟動系統。

  - 如何執行自動化測試指令（例如：使用 behave 指令）並解讀測試結果。

語氣要求： 請以專業工程師的口吻進行實作，專注於邏輯正確性、代碼穩健性與可測試性，無需多餘的修飾。