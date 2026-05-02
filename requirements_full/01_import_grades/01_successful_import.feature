Feature: 成功匯入成績檔案

  Background:
    Given 授課教師已登入系統
    And 系統已準備就緒

  Scenario: 成功匯入CSV格式的成績檔案
    When 授課教師選擇"匯入成績"功能
    And 上傳一個包含100名學生成績的CSV檔案
    Then 系統應顯示匯入預覽
    And 預覽中包含學號、姓名、成績三列
    And 授課教師點選"確認匯入"按鈕
    And 系統應完成匯入並顯示"成功匯入100名學生"的提示
    And 產生匯入摘要報告

  Scenario: 成功匯入Excel格式的成績檔案
    When 授課教師選擇"匯入成績"功能
    And 上傳一個包含200名學生成績的Excel檔案
    Then 系統應顯示匯入預覽
    And 預覽中包含所有學生資訊
    When 授課教師點選"確認匯入"按鈕
    Then 系統應完成匯入並顯示成功提示
