with employees as (
    select * from SALES_DB.RAW.RAW_EMPLOYEE_PERFORMANCE
),

summary as (
    select
        DEPARTMENT,
        count(*) as TOTAL_EMPLOYEES,
        round(avg(PERFORMANCE_SCORE), 2) as AVG_PERFORMANCE,
        round(avg(MONTHLY_SALARY), 2) as AVG_SALARY,
        round(avg(EMPLOYEE_SATISFACTION_SCORE), 2) as AVG_SATISFACTION,
        sum(case when RESIGNED = true then 1 else 0 end) as TOTAL_RESIGNED,
        sum(case when PERFORMANCE_SCORE >= 4 then 1 else 0 end) as HIGH_PERFORMERS,
        sum(case when PERFORMANCE_SCORE < 3 then 1 else 0 end) as LOW_PERFORMERS,
        round(avg(TRAINING_HOURS), 1) as AVG_TRAINING_HOURS,
        round(avg(PROJECTS_HANDLED), 1) as AVG_PROJECTS
    from employees
    group by DEPARTMENT
)

select * from summary