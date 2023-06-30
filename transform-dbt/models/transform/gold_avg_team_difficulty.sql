WITH fixture_dates AS (
    SELECT DISTINCT fixture_date, fixture_id, season, away_team_id, home_team_id
    FROM {{ ref('silver_fixture') }}
)

, standing AS (
    SELECT DISTINCT season, team_id, rank AS prior_season_rank
    FROM {{ ref('silver_standing') }}
)

, away_team_CTE AS (
    SELECT fixture_dates.fixture_id
    , fixture_dates.away_team_id AS team_id
    , fixture_dates.fixture_date
    , fixture_dates.season
    , prior_season_rank
    FROM fixture_dates
    INNER JOIN standing
        ON (fixture_dates.season - 1) = standing.season AND standing.team_id = fixture_dates.home_team_id
)

, home_team_CTE AS (
    SELECT fixture_dates.fixture_id
    , fixture_dates.home_team_id AS team_id
    , fixture_dates.fixture_date
    , fixture_dates.season
    , prior_season_rank
    FROM fixture_dates
    INNER JOIN standing
        ON (fixture_dates.season - 1) = standing.season AND standing.team_id = fixture_dates.away_team_id
)

, combined_view AS (
SELECT * FROM home_team_CTE
UNION
SELECT * FROM away_team_CTE
)

SELECT fixture_id
, team_id
, AVG(prior_season_rank) OVER (
        PARTITION BY team_id 
        ORDER BY fixture_date DESC
        ROWS BETWEEN 9 PRECEDING AND 1 PRECEDING
    ) as rank_team_faced
FROM combined_view
ORDER BY fixture_id