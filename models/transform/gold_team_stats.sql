WITH fixture_dates AS (
    SELECT DISTINCT fixture_date, fixture_id, season
    FROM {{ ref('silver_fixture') }}
)

, standing AS (
    SELECT DISTINCT season, team_id, rank AS prior_season_rank
    FROM {{ ref('silver_standing') }}
)

, temp_view AS (
    SELECT silver_fixture_stat.* 
    , fixture_dates.fixture_date
    , standing.prior_season_rank
FROM {{ ref('silver_fixture_stat') }}
INNER JOIN fixture_dates
    USING (fixture_id)
INNER JOIN standing
    ON standing.team_id = silver_fixture_stat.team_id AND (fixture_dates.season- 1) = standing.season
ORDER BY team_id, fixture_date
)

SELECT team_id
, fixture_id
, prior_season_rank
, AVG(total_shots) OVER (
        PARTITION BY team_id 
        ORDER BY fixture_date DESC
        ROWS BETWEEN 9 PRECEDING AND 1 PRECEDING
    ) as total_shots_avg
, AVG(possession) OVER (
        PARTITION BY team_id 
        ORDER BY fixture_date DESC
        ROWS BETWEEN 9 PRECEDING AND 1 PRECEDING
    ) as possession_avg
, AVG(red_cards) OVER (
        PARTITION BY team_id 
        ORDER BY fixture_date DESC
        ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING
    ) as red_cards
, AVG(gk_saves) OVER (
        PARTITION BY team_id 
        ORDER BY fixture_date DESC
        ROWS BETWEEN 9 PRECEDING AND 1 PRECEDING
    ) as gk_saves_avg
, AVG(fouls) OVER (
        PARTITION BY team_id 
        ORDER BY fixture_date DESC
        ROWS BETWEEN 9 PRECEDING AND 1 PRECEDING
    ) as fouls_avg
, AVG(a_passes/tot_passes) OVER (
        PARTITION BY team_id 
        ORDER BY fixture_date DESC
        ROWS BETWEEN 9 PRECEDING AND 1 PRECEDING
    ) as pass_accuracy_avg
FROM temp_view