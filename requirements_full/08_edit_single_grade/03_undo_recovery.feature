Feature: 撤銷和恢復成績

Background:
  Given 授課教師已登入系統
  And 已有成績修改記錄

Scenario: 撤銷成績修改
  When 授課教師修改了一名學生的成績
  And 發現修改有誤
  And 點擊"撤銷"按鈕
  Then 系統應恢復到修改前的成績
  And 原本的修改記錄應標記為"已撤銷"

Scenario: 批量撤銷修改
  When 授課教師發現某個批次的修改有誤
  And 進入"修改歷史"
  And 選擇該批次的多條修改記錄
  And 點擊"批量撤銷"
  Then 系統應撤銷選中的所有修改
  And 所有受影響學生的成績應恢復
