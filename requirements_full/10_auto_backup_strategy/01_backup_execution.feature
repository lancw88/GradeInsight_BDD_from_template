Feature: 自動備份執行

Background:
  Given 系統正在運作
  And 系統已設定備份策略

Scenario: 系統按時執行自動備份
  When 系統時間到達每日午夜00:00:00
  Then 系統應自動觸發備份任務
  And 開始備份所有成績資料
  And 備份過程中系統照常運作，不影響教師使用
  And 備份檔案名格式為："grades_backup_YYYY-MM-DD.bak.enc"
  And 備份完成後應記錄備份時間、大小、狀態

Scenario: 手動觸發備份
  When 系統管理員進入"備份管理"頁面
  And 點選"立即備份"按鈕
  Then 系統應立即執行一次完整備份
  And 備份完成後顯示成功提示
