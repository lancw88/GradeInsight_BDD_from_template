Feature: 撤銷和復用評分方案

Background:
  Given 授課教師已登入系統
  And 已有評分方案應用到成績

Scenario: 撤銷評分方案
  When 授課教師應用了一個評分方案後發現有誤
  And 進入"方案應用歷史"
  And 點擊"撤銷"按鈕
  Then 系統應恢復到應用前的原始成績
  And 顯示"成績已恢復"的提示

Scenario: 保存和復用方案
  When 授課教師點擊"另存為模板"
  And 輸入模板名稱"春季班級方案"
  Then 系統應保存該評分方案
  And 在課程間可復用該模板
  And 模板應出現在下次使用時的方案列表中
