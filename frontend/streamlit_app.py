import os
from typing import Any

import plotly.express as px
import requests
import streamlit as st


st.set_page_config(page_title="GradeInsight 成績管理", page_icon="GI", layout="wide")
st.markdown(
    """
    <style>
    :root {
        --ink: #20312d;
        --muted: #687873;
        --paper: #f4f6f2;
        --green: #176b59;
        --mint: #d9eee6;
        --coral: #d66b54;
        --gold: #d8a642;
        --text-color: #20312d;
        --secondary-text-color: #53635e;
        --heading-color: #20312d;
        color-scheme: light;
    }
    html, body, .stApp, [data-testid="stAppViewContainer"] {
        color: var(--ink) !important;
        background-color: var(--paper);
        color-scheme: light;
    }
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        --text-color: #20312d;
        --secondary-text-color: #53635e;
        --heading-color: #20312d;
    }
    .stApp :is(h1, h2, h3, h4, h5, h6, p, li, label, legend, summary),
    [data-testid="stAppViewContainer"] [data-testid="stWidgetLabel"],
    [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"],
    [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] :is(h1, h2, h3, h4, h5, h6, p, li, label, legend, summary),
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"],
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #20312d !important;
    }
    .stApp [data-testid="stCaptionContainer"],
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #53635e !important;
    }
    [data-testid="stSidebar"] {
        background: #e7eee9;
        border-right: 1px solid #d3ddd6;
        --text-color: #20312d;
        --secondary-text-color: #53635e;
        --heading-color: #20312d;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] [data-testid="stRadio"] label,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #20312d !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > label {
        padding: 6px 10px;
        border-radius: 5px;
        color: #20312d !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > label:hover {
        background: #d2e4da;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) {
        background: #176b59;
        color: #ffffff !important;
        font-weight: 600;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) * {
        color: #ffffff !important;
    }
    .stApp input,
    .stApp textarea,
    .stApp [data-baseweb="select"] > div,
    .stApp [data-baseweb="input"] > div,
    .stApp [data-baseweb="textarea"] > div,
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea {
        color: #20312d !important;
    }
    [data-testid="stMetric"] {
        background: #ffffff; border: 1px solid #dbe3dd; border-top: 3px solid var(--green);
        padding: 14px 16px; border-radius: 6px;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p { color: #53635e !important; }
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] div { color: #20312d !important; }
    div.stButton > button[kind="primary"] {
        background: var(--green);
        border-color: var(--green);
        color: #ffffff !important;
    }
    div.stButton > button:not([kind="primary"]) {
        color: #20312d !important;
    }
    div.stButton > button { border-radius: 5px; }
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        --text-color: #20312d;
        --background-color: #ffffff;
        --secondary-background-color: #eff4f1;
    }
    [data-testid="stAlert"] p,
    [data-testid="stAlert"] li,
    [data-testid="stNotification"] p {
        color: #20312d !important;
    }
    h1, h2, h3 { color: var(--ink); }
    .gi-kicker { color: var(--green); font-size: 0.78rem; font-weight: 700; letter-spacing: .06em; }
    .gi-note { color: var(--muted); font-size: .9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_request(method: str, path: str, **kwargs: Any) -> Any:
    base_url = st.session_state.get("api_url", "http://127.0.0.1:8000").rstrip("/")
    headers = {}
    api_token = os.getenv("GRADEINSIGHT_API_TOKEN", "")
    if api_token:
        headers["X-API-Key"] = api_token
    try:
        response = requests.request(
            method,
            f"{base_url}{path}",
            headers=headers,
            timeout=15,
            **kwargs,
        )
    except requests.RequestException as error:
        raise RuntimeError(f"無法連線至後端 API：{error}") from error
    if not response.ok:
        try:
            detail = response.json().get("detail", "請求失敗")
        except ValueError:
            detail = response.text or "請求失敗"
        if isinstance(detail, list):
            detail = "；".join(item.get("message", str(item)) for item in detail)
        raise RuntimeError(f"{detail}（HTTP {response.status_code}）")
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        return response.json()
    return response.content


def show_error(action) -> Any:
    try:
        return action()
    except (RuntimeError, ValueError, KeyError) as error:
        st.error(str(error))
        return None


def show_topline(section: str) -> None:
    st.markdown("<div class='gi-kicker'>GRADEINSIGHT　/　成績資料工作台</div>", unsafe_allow_html=True)
    st.title(section)


def student_frame(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "學號": row["student_id"],
            "姓名": row["name"],
            "班級": row["class_name"],
            "平時": row["scores"]["coursework"],
            "期中": row["scores"]["midterm"],
            "期末": row["scores"]["final"],
            "總成績": row["final_score"],
            "等級": row["grade"],
        }
        for row in rows
    ]


with st.sidebar:
    st.markdown("## GradeInsight")
    st.caption("班級成績管理與分析")
    page = st.radio(
        "功能導覽",
        ["總覽", "匯入成績", "成績分析", "需協助學生", "學生資料", "評分方案", "自動調整規則", "報表匯出", "備份管理"],
        label_visibility="collapsed",
    )
    st.divider()
    st.text_input("後端 API 位址", value=os.getenv("GRADEINSIGHT_API_URL", "http://127.0.0.1:8000"), key="api_url")
    st.caption("資料儲存於後端 SQLite 資料庫")


if page == "總覽":
    show_topline("班級總覽")
    overview_params = {"component": "overall", "pass_mark": 60, "bin_width": 10}
    result = show_error(lambda: api_request("GET", "/api/analysis", params=overview_params))
    records = show_error(lambda: api_request("GET", "/api/students"))
    if result and records is not None:
        stats = result["statistics"]
        metrics = st.columns(5)
        metrics[0].metric("修課人數", f"{result['count']} 人")
        metrics[1].metric("平均分", f"{stats['mean']:.1f}")
        metrics[2].metric("中位數", f"{stats['median']:.1f}")
        metrics[3].metric("及格率", f"{stats['pass_rate']:.1f}%")
        metrics[4].metric("標準差", f"{stats['standard_deviation']:.1f}")
        left, right = st.columns([1.55, 1])
        with left:
            st.subheader("總成績分布")
            histogram = result["histogram"]
            figure = px.bar(
                histogram,
                x="label",
                y="count",
                labels={"label": "成績區間", "count": "學生人數"},
                color="count",
                color_continuous_scale=["#d9eee6", "#176b59"],
            )
            figure.update_layout(showlegend=False, coloraxis_showscale=False, margin=dict(l=8, r=8, t=12, b=8))
            st.plotly_chart(figure, use_container_width=True)
        with right:
            st.subheader("成績等級")
            grade_rows = [{"等級": grade, **values} for grade, values in result["grade_counts"].items()]
            grade_chart = px.bar(grade_rows, x="等級", y="count", text="count", color="等級", color_discrete_map={"A": "#176b59", "B": "#61a58e", "C": "#d8a642", "D": "#de946b", "F": "#d66b54"})
            grade_chart.update_layout(showlegend=False, xaxis_title=None, yaxis_title="學生人數", margin=dict(l=8, r=8, t=12, b=8))
            st.plotly_chart(grade_chart, use_container_width=True)
        st.subheader("近期需要留意")
        risk_rows = show_error(lambda: api_request("GET", "/api/at-risk", params={"pass_mark": 60, "risk_range": 10}))
        if risk_rows:
            st.dataframe(risk_rows[:8], hide_index=True, use_container_width=True)
        else:
            st.success("目前沒有落在設定風險範圍內的學生。")
        with st.expander("產生模擬資料"):
            st.caption("新增 30 位隨機示範學生；不會刪除現有資料。")
            if st.button("新增 30 位模擬學生"):
                generated = show_error(lambda: api_request("POST", "/api/demo/generate", params={"count": 30}))
                if generated:
                    st.success(f"已新增 {generated['inserted']} 位，班級共 {generated['total']} 位。")
                    st.rerun()

elif page == "匯入成績":
    show_topline("匯入成績")
    st.caption("支援 CSV、Excel（.xls、.xlsx），單次最多 500 位學生；先預覽檢核結果，再確認匯入。")
    template = show_error(lambda: api_request("GET", "/api/import/template"))
    if template:
        st.download_button("下載 CSV 範本", template, file_name="grade-template.csv", mime="text/csv")
    upload = st.file_uploader("選擇成績檔案", type=["csv", "xls", "xlsx", "xlsm"])
    if upload and st.button("檢查並預覽", type="primary"):
        preview = show_error(
            lambda: api_request(
                "POST",
                "/api/import/preview",
                files={"file": (upload.name, upload.getvalue(), upload.type or "application/octet-stream")},
            )
        )
        if preview:
            st.session_state["import_preview"] = preview
    preview = st.session_state.get("import_preview")
    if preview:
        cols = st.columns(4)
        cols[0].metric("資料列", preview["total_rows"])
        cols[1].metric("可匯入", preview["valid_count"])
        cols[2].metric("重複略過", preview["duplicate_count"])
        cols[3].metric("格式錯誤", preview["invalid_count"])
        st.subheader("有效資料預覽（最多顯示 10 筆）")
        st.dataframe(student_frame([{**row, "final_score": 0, "grade": "預覽"} for row in preview["preview"]]), hide_index=True, use_container_width=True)
        if preview["errors"]:
            with st.expander(f"檢視 {len(preview['errors'])} 筆略過項目"):
                st.dataframe(preview["errors"], hide_index=True, use_container_width=True)
        if preview["valid_count"]:
            st.warning("確認後將新增有效資料；匯入後無法由此畫面批次撤銷。")
            if st.button("確認匯入有效資料", type="primary"):
                outcome = show_error(lambda: api_request("POST", "/api/import/commit", json={"records": preview["records"]}))
                if outcome:
                    st.success(f"已匯入 {outcome['imported']} 位，重複學號略過 {outcome['duplicates_skipped']} 筆。")
                    st.session_state.pop("import_preview", None)

elif page == "成績分析":
    show_topline("成績統計分析")
    controls = st.columns(4)
    component_map = {"總成績": "overall", "平時": "coursework", "期中": "midterm", "期末": "final"}
    selected_component = controls[0].selectbox("分析項目", list(component_map))
    pass_mark = controls[1].number_input("及格線", min_value=0.0, max_value=100.0, value=60.0, step=1.0)
    bin_width = controls[2].selectbox("分數區間寬度", [5, 10, 20], index=1)
    baseline = controls[3].number_input("比較基準平均", min_value=0.0, max_value=100.0, value=70.0, step=1.0)
    result = show_error(lambda: api_request("GET", "/api/analysis", params={"component": component_map[selected_component], "pass_mark": pass_mark, "bin_width": bin_width}))
    if result and result["statistics"]:
        stats = result["statistics"]
        metric_cols = st.columns(6)
        metric_cols[0].metric("平均分", stats["mean"])
        metric_cols[1].metric("中位數", stats["median"])
        metric_cols[2].metric("眾數", ", ".join(str(value) for value in stats["mode"][:3]) or "無")
        metric_cols[3].metric("標準差", stats["standard_deviation"])
        metric_cols[4].metric("最高分", stats["maximum"])
        metric_cols[5].metric("最低分", stats["minimum"])
        chart_col, grades_col = st.columns([1.4, 1])
        with chart_col:
            st.subheader("成績區間人數")
            figure = px.bar(result["histogram"], x="label", y="count", labels={"label": "成績區間", "count": "人數"}, color_discrete_sequence=["#176b59"])
            figure.update_layout(margin=dict(l=8, r=8, t=12, b=8))
            st.plotly_chart(figure, use_container_width=True)
        with grades_col:
            st.subheader("等級組成")
            grade_rows = [{"等級": grade, "人數": data["count"], "比例（%）": data["percentage"]} for grade, data in result["grade_counts"].items()]
            st.dataframe(grade_rows, hide_index=True, use_container_width=True)
            st.caption(f"及格率 {stats['pass_rate']}%　·　優良率 {stats['excellent_rate']}%")
        st.subheader("分析結論與建議")
        for conclusion in result["conclusions"]:
            st.write(f"• {conclusion}")
        if result["outliers"]:
            st.subheader("統計離群值，建議核對原始紀錄")
            st.dataframe(result["outliers"], hide_index=True, use_container_width=True)
        comparison = show_error(lambda: api_request("GET", "/api/analysis/compare", params={"baseline_mean": baseline, "baseline_label": "比較基準", "component": component_map[selected_component]}))
        if comparison:
            st.info(f"目前平均 {comparison['current_mean']} 分，相較 {comparison['baseline_label']} {comparison['baseline_mean']} 分為{comparison['summary']} {abs(comparison['difference'])} 分。")

elif page == "需協助學生":
    show_topline("需協助學生")
    options = st.columns(3)
    pass_mark = options[0].number_input("及格線", min_value=0.0, max_value=100.0, value=60.0, step=1.0)
    risk_range = options[1].number_input("接近及格線範圍（分）", min_value=0.0, max_value=50.0, value=10.0, step=1.0)
    sort_by = options[2].selectbox("排序方式", ["依成績", "先列不及格"], index=0)
    records = show_error(lambda: api_request("GET", "/api/at-risk", params={"pass_mark": pass_mark, "risk_range": risk_range, "sort_by": "score" if sort_by == "依成績" else "risk"}))
    if records is not None:
        if records:
            st.dataframe(records, hide_index=True, use_container_width=True, column_config={"final_score": st.column_config.NumberColumn("目前總成績", format="%.1f"), "gap_to_pass": st.column_config.NumberColumn("與及格線差距", format="%.1f")})
            csv_data = show_error(lambda: api_request("GET", "/api/at-risk/export", params={"pass_mark": pass_mark, "risk_range": risk_range}))
            if csv_data:
                st.download_button("下載需協助學生清單", csv_data, file_name="at-risk-students.csv", mime="text/csv")
            with st.expander("批次記錄提醒"):
                st.caption("目前採本機模擬記錄，不會實際寄送郵件或簡訊。")
                message = st.text_area("提醒內容", value="近期成績需要留意，請與授課教師聯繫安排學習協助。")
                if st.button("記錄提醒", type="primary"):
                    result = show_error(lambda: api_request("POST", "/api/notifications/batch", json={"student_ids": [row["student_id"] for row in records], "message": message}))
                    if result:
                        st.success(f"已為 {result['queued']} 位學生建立提醒紀錄。")
        else:
            st.success("此條件下沒有需要列入關注的學生。")

elif page == "學生資料":
    show_topline("學生個人成績")
    roster = show_error(lambda: api_request("GET", "/api/students"))
    if roster:
        selection = {f"{row['student_id']}　{row['name']}": row["student_id"] for row in roster}
        chosen = st.selectbox("選擇學生", list(selection))
        detail = show_error(lambda: api_request("GET", f"/api/students/{selection[chosen]}"))
        if detail:
            top = st.columns(5)
            top[0].metric("學號", detail["student_id"])
            top[1].metric("班級", detail["class_name"])
            top[2].metric("總成績", detail["final_score"])
            top[3].metric("班級排名", f"{detail['rank']} / {detail['class_size']}")
            top[4].metric("班級平均", detail["class_average"])
            left, right = st.columns([1.15, 1])
            with left:
                st.subheader("評分項目與趨勢")
                chart = px.line(detail["trend"], x="label", y="score", markers=True, labels={"label": "評分項目", "score": "分數"})
                chart.update_traces(line_color="#176b59", marker_size=10)
                chart.update_yaxes(range=[0, 100])
                chart.update_layout(margin=dict(l=8, r=8, t=12, b=8))
                st.plotly_chart(chart, use_container_width=True)
                st.dataframe([{"評分項目": item["label"], "成績": item["score"]} for item in detail["trend"]], hide_index=True, use_container_width=True)
            with right:
                st.subheader("編輯單項成績")
                component_map = {"平時": "coursework", "期中": "midterm", "期末": "final"}
                with st.form("edit_score_form"):
                    component = st.selectbox("成績項目", list(component_map))
                    score = st.number_input("新成績", min_value=0.0, max_value=100.0, value=float(detail["scores"][component_map[component]]), step=0.5)
                    reason = st.text_input("修改原因（必填）")
                    modified_by = st.text_input("修改人", value="教師")
                    submitted = st.form_submit_button("儲存修改", type="primary")
                if submitted:
                    if len(reason.strip()) < 3:
                        st.warning("請輸入至少 3 個字的修改原因。")
                    else:
                        result = show_error(lambda: api_request("PUT", f"/api/students/{detail['student_id']}/scores", json={"component": component_map[component], "score": score, "reason": reason, "modified_by": modified_by}))
                        if result:
                            st.success("成績已更新，排名與總成績已重新計算。")
                            st.rerun()
                if st.button("撤銷最近一次修改"):
                    result = show_error(lambda: api_request("POST", f"/api/students/{detail['student_id']}/undo"))
                    if result:
                        st.success("已還原上一個成績版本。")
                        st.rerun()
            st.subheader("稽核紀錄")
            if detail["audit_history"]:
                st.dataframe(detail["audit_history"], hide_index=True, use_container_width=True)
            else:
                st.caption("尚無成績修改紀錄。")

elif page == "評分方案":
    show_topline("評分方案")
    scheme_info = show_error(lambda: api_request("GET", "/api/schemes"))
    if scheme_info:
        st.caption(f"目前使用：{scheme_info['active_scheme'] or '預設方案'}")
        with st.expander("建立評分方案", expanded=not bool(scheme_info["schemes"])):
            with st.form("scheme_form"):
                scheme_name = st.text_input("方案名稱", placeholder="例如：期末加重方案")
                method_label = st.selectbox("計算方式", ["加權平均", "簡單平均", "單項最高分"])
                weights = {"coursework": 0.2, "midterm": 0.3, "final": 0.5}
                if method_label == "加權平均":
                    weight_cols = st.columns(3)
                    weights["coursework"] = weight_cols[0].number_input("平時權重", 0.0, 1.0, 0.2, 0.05)
                    weights["midterm"] = weight_cols[1].number_input("期中權重", 0.0, 1.0, 0.3, 0.05)
                    weights["final"] = weight_cols[2].number_input("期末權重", 0.0, 1.0, 0.5, 0.05)
                    st.caption(f"權重合計：{sum(weights.values()) * 100:.0f}%（必須為 100%）")
                save_scheme = st.form_submit_button("儲存方案")
            if save_scheme:
                method = {"加權平均": "weighted", "簡單平均": "average", "單項最高分": "highest"}[method_label]
                created = show_error(lambda: api_request("POST", "/api/schemes", json={"name": scheme_name, "method": method, "weights": weights}))
                if created:
                    st.success("評分方案已儲存。")
                    st.rerun()
        if scheme_info["schemes"]:
            scheme_names = [scheme["name"] for scheme in scheme_info["schemes"]]
            selected_scheme = st.selectbox("選擇方案", scheme_names)
            c1, c2, c3 = st.columns(3)
            if c1.button("預覽成績變化", type="primary"):
                preview = show_error(lambda: api_request("POST", f"/api/schemes/{selected_scheme}/preview"))
                if preview:
                    st.session_state["scheme_preview"] = preview
            if c2.button("確認套用方案"):
                applied = show_error(lambda: api_request("POST", f"/api/schemes/{selected_scheme}/apply"))
                if applied:
                    st.success(f"已套用方案，影響 {applied['students_affected']} 位學生。")
                    st.rerun()
            if c3.button("撤銷方案變更"):
                undone = show_error(lambda: api_request("POST", "/api/schemes/undo"))
                if undone:
                    st.success(f"已還原方案：{undone['active_scheme'] or '系統預設'}")
                    st.rerun()
            preview = st.session_state.get("scheme_preview")
            if preview:
                st.info(f"預覽：{preview['affected_count']} 位學生；目前方案為 {preview['active_scheme'] or '無'}。")
                st.dataframe(preview["records"], hide_index=True, use_container_width=True)
            st.subheader("已儲存方案")
            st.dataframe(scheme_info["schemes"], hide_index=True, use_container_width=True)

elif page == "自動調整規則":
    show_topline("自動調整規則")
    st.caption("規則需先預覽，再由教師確認套用；每條規則對每位學生只會生效一次。")
    with st.expander("建立調整規則"):
        with st.form("rule_form"):
            rule_name = st.text_input("規則名稱", placeholder="例如：缺席三次以上扣分")
            field_label = st.selectbox("判斷欄位", ["總成績", "出席率", "缺席次數"])
            field_key = {"總成績": "overall", "出席率": "attendance_rate", "缺席次數": "absences"}[field_label]
            comparison = st.selectbox("條件", ["小於等於", "大於等於", "小於", "大於"])
            operator = {"小於等於": "<=", "大於等於": ">=", "小於": "<", "大於": ">"}[comparison]
            threshold = st.number_input("條件門檻", min_value=0.0, value=3.0 if field_key == "absences" else 60.0, step=1.0)
            adjustment_label = st.selectbox("調整方式", ["扣分", "加分", "按比例增加"])
            adjustment_type = {"扣分": "deduct", "加分": "bonus", "按比例增加": "percentage"}[adjustment_label]
            amount = st.number_input("調整幅度（分或百分比）", min_value=0.1, max_value=100.0, value=5.0, step=0.5)
            save_rule = st.form_submit_button("儲存規則")
        if save_rule:
            created = show_error(lambda: api_request("POST", "/api/rules", json={"name": rule_name, "field": field_key, "operator": operator, "threshold": threshold, "adjustment_type": adjustment_type, "amount": amount}))
            if created:
                st.success("規則已儲存。")
                st.rerun()
    rules = show_error(lambda: api_request("GET", "/api/rules"))
    if rules:
        rule_map = {f"{rule['name']}（#{rule['id']}）": rule["id"] for rule in rules}
        selected = st.selectbox("已儲存規則", list(rule_map))
        selected_id = rule_map[selected]
        actions = st.columns(3)
        if actions[0].button("預覽影響學生", type="primary"):
            preview = show_error(lambda: api_request("POST", f"/api/rules/{selected_id}/preview"))
            if preview:
                st.session_state["rule_preview"] = preview
        if actions[1].button("確認套用規則"):
            applied = show_error(lambda: api_request("POST", "/api/rules/apply", json={"rule_id": selected_id}))
            if applied:
                st.success(f"已調整 {applied['applied_count']} 位學生；已套用過的學生不會重複計算。")
                st.rerun()
        if actions[2].button("撤銷此規則"):
            undone = show_error(lambda: api_request("POST", f"/api/rules/{selected_id}/undo"))
            if undone:
                st.success(f"已撤銷 {undone['reverted_count']} 筆調整。")
                st.rerun()
        preview = st.session_state.get("rule_preview")
        if preview:
            st.info(f"符合條件 {preview['affected_count']} 位；已套用過 {preview['already_applied_count']} 位。")
            if preview["records"]:
                st.dataframe(preview["records"], hide_index=True, use_container_width=True)
            else:
                st.caption("目前沒有符合條件的學生。")
        st.subheader("規則範本")
        st.dataframe(rules, hide_index=True, use_container_width=True)
    else:
        st.caption("尚未建立規則。")

elif page == "報表匯出":
    show_topline("成績報表匯出")
    form_cols = st.columns(3)
    format_label = form_cols[0].selectbox("檔案格式", ["CSV", "Excel", "PDF"])
    privacy_label = form_cols[1].selectbox("隱私級別", ["完整資料", "遮蔽姓名與學號", "匿名資料"])
    include_stats = form_cols[2].checkbox("附上班級統計", value=True)
    title = st.text_input("報表標題", value="班級成績報告")
    batch_export = st.checkbox("批次匯出全班個人成績單（ZIP）")
    selected_student = None
    if batch_export:
        st.caption("將依目前隱私設定，為全班每位學生分別產生一份成績單。")
    else:
        roster = show_error(lambda: api_request("GET", "/api/students"))
        student_options = ["全班"] + ([f"{row['student_id']}　{row['name']}" for row in roster] if roster else [])
        selected = st.selectbox("匯出範圍", student_options)
        selected_student = None if selected == "全班" else selected.split()[0]
    include_qr = st.checkbox("在 PDF 報表中加入識別 QR Code") if format_label == "PDF" else False
    if st.button("產生報表", type="primary"):
        format_value = {"CSV": "csv", "Excel": "xlsx", "PDF": "pdf"}[format_label]
        privacy_value = {"完整資料": "full", "遮蔽姓名與學號": "masked", "匿名資料": "anonymous"}[privacy_label]
        report_path = "/api/reports/batch" if batch_export else "/api/reports/export"
        params = {"format": format_value, "privacy": privacy_value, "title": title, "include_qr": include_qr}
        if not batch_export:
            params.update({"student_id": selected_student, "include_stats": include_stats})
        content = show_error(lambda: api_request("GET", report_path, params=params))
        if content:
            file_extension = "zip" if batch_export else format_value
            mime = "application/zip" if batch_export else {"csv": "text/csv", "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "pdf": "application/pdf"}[format_value]
            st.download_button("下載成績報表", content, file_name=f"grade-report.{file_extension}", mime=mime)
            st.success("批次個人成績單已打包完成。" if batch_export else "報表已產生，可下載檔案。")
    st.caption("可匯出班級或個人成績；匿名模式會移除學號、姓名與班級。")

elif page == "備份管理":
    show_topline("備份管理")
    st.info("系統每日午夜自動執行 AES-256-GCM 加密備份，保留最近 30 天且最多 30 份。備份金鑰請另外安全保存。")
    if st.button("立即建立加密備份", type="primary"):
        result = show_error(lambda: api_request("POST", "/api/backups"))
        if result:
            st.success(f"備份完成：{result['filename']}（{result['size_bytes']:,} bytes）")
    history = show_error(lambda: api_request("GET", "/api/backups"))
    if history:
        st.subheader("備份紀錄")
        st.dataframe(history, hide_index=True, use_container_width=True, column_config={"size_bytes": st.column_config.NumberColumn("檔案大小（bytes）", format="%d")})
    elif history is not None:
        st.caption("尚無備份紀錄。")