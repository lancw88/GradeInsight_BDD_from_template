Feature: 統計指標和報告匯出

Background:
  Given 授課教師已登入系統
  And 系統中已有100名學生的成績資料

Scenario: 顯示統計指標
  When 授課教師檢視成績分布頁面
  Then 系統應顯示關鍵統計指標：
  | 指標 | 說明 |
  | 平均分 | 班級平均成績 |
  | 中位數 | 中間成績值 |
  | 標準差 | 成績波動程度 |
  | 最高分 | 班級最高成績 |
  | 最低分 | 班級最低成績 |

Scenario: 匯出圖表為PNG和PDF
  When 授課教師點選"匯出"按鈕
  And 選擇匯出格式"PNG"
  Then 系統應下載高解析度PNG圖表檔案
  When 授課教師選擇匯出格式"PDF"
  Then 系統應匯出包含統計資訊的PDF報告
