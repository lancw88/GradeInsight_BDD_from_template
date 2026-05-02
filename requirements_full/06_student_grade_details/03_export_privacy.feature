Feature: 匯出個人成績單

Background:
  Given 授課教師已登入系統
  And 正在檢視學生詳細成績頁面

Scenario: 列印和匯出個人成績單
  When 授課教師在學生詳情頁點選"列印"按鈕
  Then 瀏覽器應打開列印對話框
  And 成績單應格式清晰，適合列印輸出
  When 授課教師點選"匯出為PDF"
  Then 系統應下載該學生的PDF成績單
  And 成績單應包含完整的成績資訊

Scenario: 隱私保護
  When 系統顯示學生個人成績
  Then 頁面應標記為"機密資訊"
  And 系統應記錄誰檢視了該學生成績
  And 未授權的教師應無法存取該資訊
