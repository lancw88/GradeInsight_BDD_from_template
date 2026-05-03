# 🔧 Behave Step 衝突修復指南

## 問題概述

Behave 框架無法區分以下情況：
- 通用 step：`@when('授課教師選擇"{item}"')`
- 特定 step：`@when('選擇"按風險程度排序（高到低）"')`

因為特定 step 的字符串可以被通用步驟的參數 `"{item}"` 匹配。

## 衝突列表

### 1. 風險排序步驟（Line 749-755）

**問題**：
```python
# 行 282 - 通用（會被使用）
@when('授課教師選擇"{item}"')
def step_choose_option(context, item):
    context.last_selected = item

# 行 749 - 特定（被通用步驟遮蓋）
@when('選擇"按風險程度排序（高到低）"')
def step_choose_risk_sort(context):
    if hasattr(context, 'risk_students'):
        context.risk_students = sorted(...)

# 行 755 - 特定（被通用步驟遮蓋）
@when('選擇"按成績排序"')
def step_choose_score_sort(context):
    if hasattr(context, 'risk_students'):
        context.risk_students = sorted(...)
```

**原因**：
- `"按風險程度排序（高到低）"` 符合 `"{item}"` 模式
- Behave 優先匹配第一個定義（行 282）
- 導致特定邏輯無法執行

### 2. 方案排序步驟（Line 1089）

**問題**：
```python
# 行 1089 - 特定（被通用步驟遮蓋）
@when('選擇"按風險程度排序（高到低）"')
def step_redundant_sort(context):
    pass
```

**原因**：這是重複定義！已經在行 749 定義過。

## ✅ 解決方案

### 方案 A：刪除特定 step（推薦）
移除行 749-755 和 1089 的特定定義，單純使用行 282 的通用步驟。

**優點**：
- 減少代碼重複
- 更容易維護
- Behave 執行時不會有衝突

**缺點**：
- 需要在 feature 檔案中修改步驟文字，移除特定排序邏輯
- 排序邏輯需要在應用層面實現

### 方案 B：重新命名特定 step（替代方案）
改變特定 step 的名稱，避免與通用模式重疊。

**改法**：
```python
# 改為
@when('授課教師選擇排序方式"按風險程度排序（高到低）"')
def step_choose_risk_sort(context):
    ...

@when('授課教師選擇排序方式"按成績排序"')
def step_choose_score_sort(context):
    ...
```

**優點**：
- 保留特定邏輯
- 更清楚的步驟意圖

**缺點**：
- 需要修改 feature 檔案
- 步驟文字變得冗長

## 🎯 建議實施

**推薦使用方案 A**（刪除特定 step）：

1. **刪除以下行**：
   - Line 749-757（`step_choose_risk_sort` 函數）
   - Line 755-761（`step_choose_score_sort` 函數）
   - Line 1089-1091（重複的 `step_redundant_sort` 函數）

2. **在 feature 檔案中使用通用步驟**：
   ```gherkin
   # 改為
   When 授課教師選擇"按風險程度排序（高到低）"
   # 代替
   When 選擇"按風險程度排序（高到低）"
   ```

3. **驗證**：
   ```bash
   behave requirements_full/ --dry-run
   ```

## 📋 其他潛在衝突檢查

需要檢查的其他模式：

```
1. @when('授課教師選擇"{feature}"功能') - Line 277
   └─ 是否與其他選擇衝突？

2. @when('授課教師點選"{button}"按鈕') - Line 287
   └─ 是否與其他點選衝突？

3. @when('輸入...')
   @when('選擇...')
   └─ 是否有更細粒度的衝突？
```

## 執行步驟

1. 備份原始檔案
2. 應用修復
3. 執行 `behave --dry-run` 驗證
4. 執行 `behave` 運行完整測試
