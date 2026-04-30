Feature: 導出班級成績報告

Background:
  Given 授課教師已登入系統
  And 系統中有班級成績數據

Scenario: 導出班級總成績表為Excel
  When 授課教師進入"報告導出"功能
  And 選擇"班級總成績表"
  And 選擇導出格式為"Excel"
  And 點擊"導出"按鈕
  Then 系統應生成Excel報告文件
  And 報告應包含所有學生的成績信息
  And 報告應包含統計指標（平均分、及格率、優秀率）
  And 用戶應能下載該文件

Scenario: 導出為CSV格式
  When 授課教師選擇導出格式"CSV"
  And 點擊"導出"按鈕
  Then 系統應生成可被其他系統導入的CSV文件
  And 文件應保留所有成績信息的完整性
