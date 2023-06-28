{{ config(materialized='table') }}

SELECT * FROM football.bronze_coach
WHERE team_id IS NOT NULL