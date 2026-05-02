Feature: 匯出成績報告

Background:
  Given 授課教師已登入系統
  And 系統中有班級成績資料

Scenario: 匯出班級總成績表為Excel
  When 授課教師進入"報告匯出"功能
  And 選擇"班級總成績表"
  And 選擇匯出格式為"Excel"
  And 點選"匯出"按鈕
  Then 系統應產生Excel報告檔案
  And 報告應包含所有學生的成績資訊
  And 報告應包含統計指標（平均分、及格率、優良率）
  And 使用者應能下載該檔案

Scenario: 批次匯出個人成績單
  When 授課教師進入"個人成績單"匯出頁面
  And 選擇匯出格式為"PDF"
  And 點選"批次匯出全部"
  Then 系統應為每名學生產生一份PDF成績單
  And 成績單應包含學生個人資訊和詳細成績
  And 所有PDF應打包為ZIP檔案供下載

Scenario: 自訂報告內容範本
  When 授課教師進入"報告範本"設定
  And 選擇要包含的欄位（學號、姓名、各科成績、評語等）
  And 儲存為"自訂範本1"
  And 使用該範本匯出報告
  Then 系統應根據自訂範本產生報告
  And 報告應僅包含選中的欄位
