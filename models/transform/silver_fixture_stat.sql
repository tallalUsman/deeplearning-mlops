{{ config(materialized='table') }}

SELECT fixture_id
    , team_id
    , total_shots::DOUBLE
    , REGEXP_REPLACE(possession, '%', '')::DOUBLE AS possession
    , IFNULL(red_cards::DOUBLE, 0) AS red_cards
    , gk_saves::DOUBLE
    , fouls::DOUBLE
    , tot_passes::DOUBLE
    , a_passes::DOUBLE
FROM football.bronze_fixture_stat bf
    WHERE bf.team_id IN (SELECT DISTINCT team_id FROM football.bronze_standings)
    AND total_shots IS NOT NULL