Feature: 成績分布圖表顯示

Background:
  Given 授課教師已登入系統
  And 系統中已有100名學生的成績數據

Scenario: 顯示成績分布直方圖
  When 授課教師進入"成績分析"頁面
  And 點擊"成績分布"選項
  Then 系統應顯示成績分布的直方圖
  And 直方圖的縱軸顯示人數
  And 直方圖的橫軸顯示成績段位
  And 直方圖應清晰可讀

Scenario: 按等級分類統計
  When 授課教師在成績分布頁面點擊"按等級分類"
  Then 系統應轉換為等級統計視圖
  And 顯示A、B、C、D、F各等級的人數和百分比
