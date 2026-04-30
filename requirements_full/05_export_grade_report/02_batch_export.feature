Feature: 批量導出個人成績單

Background:
  Given 授課教師已登入系統
  And 系統中有班級成績數據

Scenario: 批量導出個人成績單為PDF
  When 授課教師進入"個人成績單"導出頁面
  And 選擇導出格式為"PDF"
  And 點擊"批量導出全部"
  Then 系統應為每名學生生成一份PDF成績單
  And 成績單應包含學生個人信息和詳細成績
  And 所有PDF應打包為ZIP文件供下載

Scenario: 導出特定學生的成績單
  When 授課教師從學生列表中選擇特定學生
  And 點擊"導出此學生成績單"
  Then 系統應生成該學生的個人成績單
  And 成績單應包含詳細的評分組件信息
