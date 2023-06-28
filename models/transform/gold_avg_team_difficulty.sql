WITH fixture_dates AS (
    SELECT DISTINCT fixture_date, fixture_id, season
    FROM {{ ref('silver_fixture') }}
)

, standing AS (
    SELECT DISTINCT season, team_id, rank AS prior_season_rank
    FROM {{ ref('silver_standing') }}
)

, stat AS (
    SELECT DISTINCT season, team_id, rank AS prior_season_rank
    FROM {{ ref('silver_fixture_stat') }}
)
