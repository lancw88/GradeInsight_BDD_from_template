Feature: 批次匯出個人成績單

Background:
  Given 授課教師已登入系統
  And 系統中有班級成績資料

Scenario: 批次匯出個人成績單為PDF
  When 授課教師進入"個人成績單"匯出頁面
  And 選擇匯出格式為"PDF"
  And 點選"批次匯出全部"
  Then 系統應為每名學生產生一份PDF成績單
  And 成績單應包含學生個人資訊和詳細成績
  And 所有PDF應打包為ZIP檔案供下載

Scenario: 匯出特定學生的成績單
  When 授課教師從學生清單中選擇特定學生
  And 點選"匯出此學生成績單"
  Then 系統應產生該學生的個人成績單
  And 成績單應包含詳細的評分元件資訊
