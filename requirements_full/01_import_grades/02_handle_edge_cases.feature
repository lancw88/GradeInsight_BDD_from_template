Feature: 處理匯入文件中的異常情況

  Background:
    Given 授課教師已登入系統
    And 系統已準備就緒

  Scenario: 處理匯入文件中的重複記錄
    When 授課教師上傳包含5條重複學生記錄的CSV文件
    Then 系統應顯示"檢測到5條重複記錄"的警告
    And 提供"跳過重複"選項
    When 授課教師選擇"跳過重複"
    Then 系統應僅匯入不重複的記錄

  Scenario: 跳過無效的記錄
    When 授課教師上傳包含無效學號的文件
    Then 系統應識別無效記錄
    And 提供自動跳過無效記錄的選項
    When 授課教師選擇"跳過無效"
    Then 系統應忽略無效記錄並匯入有效數據
