import streamlit as st

# --- 简单的登录逻辑 ---
def check_password():
    """如果输入正确密码则返回 True"""
    if "password_correct" not in st.session_state:
        # 还没输入过密码，显示输入框
        st.text_input("请输入车间看板访问密码", type="password", key="password_input")
        st.button("登录", on_click=lambda: st.session_state.update({"password_correct": st.session_state.password_input == "123456"})) # 把 123456 改成你想要的密码
        return False
    elif not st.session_state["password_correct"]:
        # 密码输错了
        st.error("密码错误，请重新输入")
        st.text_input("请输入车间看板访问密码", type="password", key="password_input")
        st.button("登录", on_click=lambda: st.session_state.update({"password_correct": st.session_state.password_input == "123456"}))
        return False
    else:
        # 密码正确
        return True

if not check_password():
    st.stop()  # 密码不对，停止运行后面的代码
# ---------------------

# 这里往下就是你原来的代码了...import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# --- 1. 页面基本配置 ---
st.set_page_config(page_title="车间项目看板-高精版", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 注入“强化边界·高对比” CSS ---
st.markdown("""
    <style>
    /* 全局背景：极简白，带淡灰色细微网格 */
    .stApp {
        background-color: #FFFFFF;
        background-image: linear-gradient(#F1F5F9 1.5px, transparent 1.5px), 
                          linear-gradient(90deg, #F1F5F9 1.5px, transparent 1.5px);
        background-size: 40px 40px;
    }
    
    /* 核心指标卡：强化边框，更有分量感 */
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 2px solid #334155; /* 深色边框，边界极度清晰 */
        border-radius: 8px;
        padding: 20px;
        box-shadow: 4px 4px 0px #CBD5E1; /* 工业感硬阴影 */
    }

    /* 指标文字：深蓝色，对比度最高 */
    div[data-testid="stMetricValue"] {
        color: #0F172A !important;
        font-family: 'Segoe UI Bold', sans-serif;
        font-weight: 800;
    }
    div[data-testid="stMetricLabel"] {
        color: #475569 !important;
        font-size: 1.1rem !important;
        font-weight: bold;
    }

    /* 标题：加粗黑体 */
    .main-title {
        font-size: 32px;
        font-weight: 900;
        color: #0F172A;
        border-bottom: 4px solid #0F172A;
        display: inline-block;
        margin-bottom: 30px;
    }

    /* 自定义清晰表格样式 */
    .styled-table {
        border-collapse: collapse;
        margin: 10px 0;
        font-size: 0.9em;
        font-family: sans-serif;
        width: 100%;
        border: 2px solid #334155; /* 表格大外框 */
    }
    .styled-table thead tr {
        background-color: #334155;
        color: #ffffff;
        text-align: left;
    }
    .styled-table th, .styled-table td {
        padding: 12px 15px;
        border: 1px solid #CBD5E1; /* 内部网格线：清晰的浅灰色 */
    }
    .styled-table tbody tr {
        border-bottom: 1px solid #dddddd;
    }
    .styled-table tbody tr:nth-of-type(even) {
        background-color: #f8fafc; /* 隔行变色，防止看串行 */
    }

    /* 隐藏多余按钮 */
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=5)
def load_data():
    file_path = "项目进度跟踪表.xlsx"
    if not Path(file_path).exists(): return pd.DataFrame()
    df = pd.read_excel(file_path)
    df.columns = [c.strip() for c in df.columns]

    # --- 关键列清洗：去空格、处理 NaN/空值 ---
    for col in ["项目号", "项目负责人", "生产负责人", "状态"]:
        if col in df.columns:
            s = df[col].fillna("").astype(str).str.strip()
            s = s.mask(s.isin(["", "nan", "None", "NaN"]), "")
            df[col] = s

    # 状态空值填充（你原本逻辑保留）
    if "状态" in df.columns:
        df["状态"] = df["状态"].mask(df["状态"].eq(""), "未启动")

    # --- 脏数据过滤 ---
    # 过滤掉：项目号长度 < 2，或 项目负责人长度 < 2，或 生产负责人长度 < 2 的记录
    for col in ["项目号", "项目负责人", "生产负责人"]:
        if col not in df.columns:
            return pd.DataFrame()

    df = df[
        (df["项目号"].str.len() >= 2)
        & (df["项目负责人"].str.len() >= 2)
        & (df["生产负责人"].str.len() >= 2)
    ].copy()

    return df

df = load_data()

if not df.empty:
    st.markdown('<p class="main-title">车间项目智慧管理看板</p>', unsafe_allow_html=True)
    
    # --- 顶栏筛选区 ---
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1: owners = st.multiselect("👤 负责人", df['项目负责人'].unique(), default=df['项目负责人'].unique())
    with col_f2: producers = st.multiselect("🛠️ 生产负责人", df['生产负责人'].unique(), default=df['生产负责人'].unique())
    with col_f3: status_list = st.multiselect("📊 状态筛选", df['状态'].unique(), default=df['状态'].unique())
    
    f_df = df[(df['项目负责人'].isin(owners)) & (df['生产负责人'].isin(producers)) & (df['状态'].isin(status_list))]

    # --- 核心指标卡 (强化边界) ---
    st.markdown("###")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("项目总量", f"{len(f_df)}")
    c2.metric("装配阶段", f"{len(f_df[f_df['状态'].str.contains('装配')])}")
    c3.metric("调试阶段", f"{len(f_df[f_df['状态'].str.contains('调试')])}")
    c4.metric("完成/待发", f"{len(f_df[f_df['状态'].str.contains('运输|验收')])}")

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns([1, 1])
    
    with col_l:
        st.markdown("**各状态项目分布统计**")
        counts = f_df['状态'].value_counts().reset_index()
        counts.columns = ['状态', '数量']
        fig = px.bar(counts, x='数量', y='状态', orientation='h', text_auto=True,
                     color='数量', color_continuous_scale='Blues')
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            font_color="#0F172A", height=450,
            margin=dict(l=0, r=20, t=10, b=0),
            xaxis=dict(showgrid=True, gridcolor='#E2E8F0') # 给图表也加上清晰的网格背景
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col_r:
        st.markdown("**实时明细清单 (清晰网格版)**")
        # --- 重点：手动构建一个边界清晰的 HTML 表格 ---
        html_table = "<table class='styled-table'><thead><tr><th>项目号</th><th>项目名称</th><th>状态</th></tr></thead><tbody>"
        for _, row in f_df[['项目号', '项目名称', '状态']].iterrows():
            html_table += f"<tr><td>{row['项目号']}</td><td>{row['项目名称']}</td><td>{row['状态']}</td></tr>"
        html_table += "</tbody></table>"
        st.markdown(html_table, unsafe_allow_html=True)

else:
    st.info("💡 请检查 Excel 文件。")