{{ config(materialized='table') }}

SELECT * FROM football.bronze_fixture bf
    WHERE bf.league_id IN (SELECT DISTINCT league_id FROM football.bronze_standings)
    AND away_goals IS NOT NULL