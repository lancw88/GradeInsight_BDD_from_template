Feature: 導出成績報告

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

Scenario: 批量導出個人成績單
  When 授課教師進入"個人成績單"導出頁面
  And 選擇導出格式為"PDF"
  And 點擊"批量導出全部"
  Then 系統應為每名學生生成一份PDF成績單
  And 成績單應包含學生個人信息和詳細成績
  And 所有PDF應打包為ZIP文件供下載

Scenario: 自訂報告內容範本
  When 授課教師進入"報告範本"設置
  And 選擇要包含的欄位（學號、姓名、各科成績、評論等）
  And 保存為"自訂範本1"
  And 使用該範本導出報告
  Then 系統應根據自訂範本生成報告
  And 報告應僅包含選中的欄位
