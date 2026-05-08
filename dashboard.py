import streamlit as st
import snowflake.connector
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Employee Performance Hub",
    page_icon="📊",
    layout="wide"
)

# --- CONNECT TO SNOWFLAKE ---
@st.cache_resource
def get_connection():
    return snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database='SALES_DB',
        schema='RAW'
    )

# --- LOAD DATA ---
@st.cache_data
def load_data():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT 
            DEPARTMENT,
            COUNT(*) as TOTAL_EMPLOYEES,
            ROUND(AVG(PERFORMANCE_SCORE), 2) as AVG_PERFORMANCE,
            ROUND(AVG(MONTHLY_SALARY), 2) as AVG_SALARY,
            ROUND(AVG(EMPLOYEE_SATISFACTION_SCORE), 2) as AVG_SATISFACTION,
            SUM(CASE WHEN RESIGNED = TRUE THEN 1 ELSE 0 END) as TOTAL_RESIGNED,
            SUM(CASE WHEN PERFORMANCE_SCORE >= 4 THEN 1 ELSE 0 END) as HIGH_PERFORMERS,
            SUM(CASE WHEN PERFORMANCE_SCORE < 3 THEN 1 ELSE 0 END) as LOW_PERFORMERS,
            ROUND(AVG(TRAINING_HOURS), 1) as AVG_TRAINING_HOURS
        FROM RAW_EMPLOYEE_PERFORMANCE
        GROUP BY DEPARTMENT
        ORDER BY AVG_PERFORMANCE DESC
    """, conn)
    return df

@st.cache_data
def load_all_employees():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT EMPLOYEE_ID, DEPARTMENT, JOB_TITLE, AGE,
               PERFORMANCE_SCORE, MONTHLY_SALARY, 
               EMPLOYEE_SATISFACTION_SCORE, RESIGNED,
               YEARS_AT_COMPANY, TRAINING_HOURS
        FROM RAW_EMPLOYEE_PERFORMANCE
        LIMIT 1000
    """, conn)
    return df

# --- AI INSIGHTS ---
def get_ai_insights(df):
    from groq import Groq
    client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    
    data_summary = df.to_string(index=False)
    
    prompt = f"""
    You are a senior HR analytics expert. Analyze this employee performance data and provide:
    1. A 2-sentence executive summary of overall workforce health
    2. Top 3 departments performing well and why
    3. Top 2 departments needing attention with recommendations
    4. One surprising insight from the data
    
    Keep it concise and professional.
    
    Data:
    {data_summary}
    """
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    
    return response.choices[0].message.content

# --- MAIN APP ---
st.title("📊 Employee Performance Analytics Hub")
st.markdown("*Powered by Snowflake + dbt + OpenAI*")

# Load data
with st.spinner("Loading data from Snowflake..."):
    df = load_data()
    df_employees = load_all_employees()

# --- KPI CARDS ---
st.subheader("🎯 Key Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Employees", f"{df['TOTAL_EMPLOYEES'].sum():,}")
with col2:
    st.metric("Avg Performance Score", f"{df['AVG_PERFORMANCE'].mean():.2f}/5.0")
with col3:
    st.metric("Avg Monthly Salary", f"${df['AVG_SALARY'].mean():,.0f}")
with col4:
    total_resigned = df['TOTAL_RESIGNED'].sum()
    total_emp = df['TOTAL_EMPLOYEES'].sum()
    resign_rate = (total_resigned/total_emp*100)
    st.metric("Resignation Rate", f"{resign_rate:.1f}%")

st.divider()

# --- DEPARTMENT TABLE ---
col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("📋 Department Performance")
    st.dataframe(
        df.style.background_gradient(subset=['AVG_PERFORMANCE'], cmap='RdYlGn'),
        use_container_width=True,
        hide_index=True
    )

with col2:
    st.subheader("🤖 AI Insights")
    if st.button("Generate AI Analysis", type="primary"):
        with st.spinner("AI is analyzing your workforce data..."):
            insights = get_ai_insights(df)
            st.session_state['insights'] = insights
    
    if 'insights' in st.session_state:
        st.markdown(st.session_state['insights'])

st.divider()

# --- FILTERS ---
st.subheader("🔍 Employee Explorer")
col1, col2 = st.columns(2)

with col1:
    dept_filter = st.selectbox(
        "Filter by Department",
        ["All"] + list(df_employees['DEPARTMENT'].unique())
    )

with col2:
    perf_filter = st.slider("Min Performance Score", 1.0, 5.0, 1.0)

filtered = df_employees.copy()
if dept_filter != "All":
    filtered = filtered[filtered['DEPARTMENT'] == dept_filter]
filtered = filtered[filtered['PERFORMANCE_SCORE'] >= perf_filter]

st.dataframe(filtered, use_container_width=True, hide_index=True)
st.caption(f"Showing {len(filtered):,} employees")