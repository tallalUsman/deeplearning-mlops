{{ config(materialized='table') }}

SELECT * FROM football.bronze_fixture_stat bf
    WHERE bf.team_id IN (SELECT DISTINCT team_id FROM football.bronze_standings)