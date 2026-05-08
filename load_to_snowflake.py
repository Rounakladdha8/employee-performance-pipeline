import snowflake.connector
import pandas as pd
from dotenv import load_dotenv
import os

# Load credentials from .env file
load_dotenv()

# --- READ CSV ---
print("📂 Reading CSV file...")
df = pd.read_csv('Extended_Employee_Performance_and_Productivity_Data.csv')

# --- CLEAN DATA ---
print("🧹 Cleaning data...")
# Fix hire date - remove the timestamp part
df['Hire_Date'] = pd.to_datetime(df['Hire_Date']).dt.date
# Make column names uppercase for Snowflake
df.columns = [col.upper() for col in df.columns]

print(f"✅ Loaded {len(df)} rows, {len(df.columns)} columns")

# --- CONNECT TO SNOWFLAKE ---
print("\n❄️ Connecting to Snowflake...")
conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE')
)

cursor = conn.cursor()
print("✅ Connected to Snowflake!")

# --- CREATE DATABASE AND SCHEMA ---
print("\n🏗️ Setting up database and schema...")
cursor.execute("CREATE DATABASE IF NOT EXISTS SALES_DB")
cursor.execute("USE DATABASE SALES_DB")
cursor.execute("CREATE SCHEMA IF NOT EXISTS RAW")
cursor.execute("USE SCHEMA RAW")

# --- CREATE TABLE ---
print("📋 Creating table...")
cursor.execute("""
    CREATE OR REPLACE TABLE RAW_EMPLOYEE_PERFORMANCE (
        EMPLOYEE_ID INTEGER,
        DEPARTMENT VARCHAR(100),
        GENDER VARCHAR(20),
        AGE INTEGER,
        JOB_TITLE VARCHAR(100),
        HIRE_DATE DATE,
        YEARS_AT_COMPANY INTEGER,
        EDUCATION_LEVEL VARCHAR(50),
        PERFORMANCE_SCORE FLOAT,
        MONTHLY_SALARY FLOAT,
        WORK_HOURS_PER_WEEK FLOAT,
        PROJECTS_HANDLED INTEGER,
        OVERTIME_HOURS FLOAT,
        SICK_DAYS INTEGER,
        REMOTE_WORK_FREQUENCY VARCHAR(50),
        TEAM_SIZE INTEGER,
        TRAINING_HOURS FLOAT,
        PROMOTIONS INTEGER,
        EMPLOYEE_SATISFACTION_SCORE FLOAT,
        RESIGNED BOOLEAN
    )
""")
print("✅ Table created!")

# --- LOAD DATA IN BATCHES ---
print(f"\n⬆️ Loading {len(df)} rows to Snowflake...")
batch_size = 5000
total_batches = len(df) // batch_size + 1

for i in range(0, len(df), batch_size):
    batch = df.iloc[i:i+batch_size]
    batch_num = i // batch_size + 1
    
    # Convert to list of tuples for insertion
    rows = [tuple(row) for row in batch.itertuples(index=False)]
    
    cursor.executemany("""
        INSERT INTO RAW_EMPLOYEE_PERFORMANCE VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """, rows)
    
    print(f"  Batch {batch_num}/{total_batches} uploaded ✓")

# --- VERIFY ---
cursor.execute("SELECT COUNT(*) FROM RAW_EMPLOYEE_PERFORMANCE")
count = cursor.fetchone()[0]
print(f"\n🎉 SUCCESS! {count} rows loaded into Snowflake!")

cursor.execute("""
    SELECT DEPARTMENT, COUNT(*) as COUNT, 
    ROUND(AVG(PERFORMANCE_SCORE), 2) as AVG_PERFORMANCE
    FROM RAW_EMPLOYEE_PERFORMANCE 
    GROUP BY DEPARTMENT 
    ORDER BY COUNT DESC
""")
print("\n📊 Quick summary by department:")
print(f"{'Department':<20} {'Count':<10} {'Avg Performance'}")
print("-" * 45)
for row in cursor.fetchall():
    print(f"{row[0]:<20} {row[1]:<10} {row[2]}")

cursor.close()
conn.close()
print("\n✅ Done! Your data is now in Snowflake.")