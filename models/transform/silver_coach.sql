{{ config(materialized='table') }}

SELECT * 
, COALESCE(end_date, '2099-12-31') AS calc_end_date
FROM football.bronze_coach
WHERE team_id IS NOT NULL