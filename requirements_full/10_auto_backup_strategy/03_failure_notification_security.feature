Feature: 備份失敗処理和通知

Background:
  Given 系統正在執行自動備份
  And 備份通知功能已啟用

Scenario: 備份失敗時傳送通知
  When 系統在執行自動備份時失敗
  And 備份檔案寫入失敗或磁碟滿
  Then 系統應立即傳送警示通知給系統管理員
  And 通知應包含失敗原因和建議的解決方案
  And 該次備份失敗應記錄在備份歷史中

Scenario: 備份成功通知
  When 系統成功完成自動備份
  Then 系統可以傳送成功確認通知（可選）
  And 記錄備份的時間、大小、檢查碼等資訊

Scenario: 備份安全性
  When 備份過程完成
  Then 備份檔案應使用AES-256加密
  And 加密金鑰應安全儲存
  And 只有授權的系統管理員可存取備份檔案
