Feature: 匯出班級成績報告

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

Scenario: 匯出為CSV格式
  When 授課教師選擇匯出格式"CSV"
  And 點選"匯出"按鈕
  Then 系統應產生可被其他系統匯入的CSV檔案
  And 檔案應保留所有成績資訊的完整性
