with source as (
    select * from SALES_DB.RAW.RAW_EMPLOYEE_PERFORMANCE
),

staged as (
    select
        EMPLOYEE_ID,
        DEPARTMENT,
        GENDER,
        AGE,
        JOB_TITLE,
        HIRE_DATE,
        YEARS_AT_COMPANY,
        EDUCATION_LEVEL,
        PERFORMANCE_SCORE,
        MONTHLY_SALARY,
        WORK_HOURS_PER_WEEK,
        PROJECTS_HANDLED,
        OVERTIME_HOURS,
        SICK_DAYS,
        REMOTE_WORK_FREQUENCY,
        TEAM_SIZE,
        TRAINING_HOURS,
        PROMOTIONS,
        EMPLOYEE_SATISFACTION_SCORE,
        RESIGNED,
        -- Add useful calculated fields
        case 
            when PERFORMANCE_SCORE >= 4 then 'High'
            when PERFORMANCE_SCORE >= 3 then 'Medium'
            else 'Low'
        end as PERFORMANCE_TIER,
        case
            when RESIGNED = true then 'Resigned'
            else 'Active'
        end as EMPLOYMENT_STATUS,
        current_timestamp() as LOADED_AT
    from source
)

select * from staged