Feature: 導出個人成績單

Background:
  Given 授課教師已登入系統
  And 正在查看學生詳細成績頁面

Scenario: 打印和導出個人成績單
  When 授課教師在學生詳情頁點擊"打印"按鈕
  Then 瀏覽器應打開打印對話框
  And 成績單應格式清晰，適合打印輸出
  When 授課教師點擊"導出為PDF"
  Then 系統應下載該學生的PDF成績單
  And 成績單應包含完整的成績信息

Scenario: 隱私保護
  When 系統顯示學生個人成績
  Then 頁面應標記為"機密信息"
  And 系統應記錄誰查看了該學生成績
  And 未授權的教師應無法訪問該信息
