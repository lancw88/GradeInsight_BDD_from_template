Feature: 匯入失敗錯誤處理

  Background:
    Given 授課教師已登入系統
    And 系統已準備就緒

  Scenario: 匯入失敗時提供詳細錯誤報告
    When 授課教師上傳含有無效資料的檔案
    Then 系統應顯示詳細錯誤報告
    And 標出具體錯誤行號和原因
    And 提供修復建議（如"第5行：成績須為數字"）
    And 錯誤報告可匯出為文本檔案

  Scenario: 超過檔案大小限制
    When 授課教師上傳超過500MB的檔案
    Then 系統應顯示"檔案過大"的錯誤資訊
    And 提示最大檔案大小限制
    And 建議分批匯入
