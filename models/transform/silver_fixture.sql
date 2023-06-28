{{ config(materialized='table') }}

SELECT *
, CASE WHEN away_goals > home_goals
    THEN 'Away'
WHEN away_goals < home_goals
    THEN 'Home'
ELSE 'Draw'
END AS match_result
FROM football.bronze_fixture bf
    WHERE bf.league_id IN (SELECT DISTINCT league_id FROM football.bronze_standings)
    AND away_goals IS NOT NULL