WITH team_lvl AS (
    SELECT gold_team_stats.*
    , gold_avg_team_difficulty.rank_team_faced
    FROM {{ ref('gold_team_stats') }}
    INNER JOIN {{ ref('gold_avg_team_difficulty') }}
        ON gold_team_stats.fixture_id = gold_avg_team_difficulty.fixture_id AND gold_team_stats.team_id = gold_avg_team_difficulty.team_id
    WHERE total_shots_avg IS NOT NULL
)

SELECT silver_fixture.*
, away.rank_team_faced AS rank_team_faced_away
, home.rank_team_faced  AS rank_team_faced_home
, (away.total_shots_avg/home.total_shots_avg) AS total_shots_r
, (away.prior_season_rank/home.prior_season_rank) AS prior_season_rank
, (away.possession_avg/home.possession_avg) AS possession_r
, away.red_cards AS red_cards_away
, home.red_cards AS red_cards_home
, (away.gk_saves_avg/home.gk_saves_avg) AS gk_saves_r
, (away.fouls_avg/home.fouls_avg) AS fouls_r
, (away.pass_accuracy_avg/home.pass_accuracy_avg) AS pass_accuracy_r
, away_coach.coach_id AS coach_id_away
, home_coach.coach_id AS coach_id_home
FROM {{ ref('silver_fixture') }}
INNER JOIN team_lvl away
ON silver_fixture.fixture_id = away.fixture_id AND silver_fixture.away_team_id = away.team_id 
INNER JOIN team_lvl home
ON silver_fixture.fixture_id = home.fixture_id AND silver_fixture.home_team_id = home.team_id 
INNER JOIN {{ ref('silver_coach') }} away_coach
ON away_coach.team_id = silver_fixture.away_team_id  AND silver_fixture.fixture_date BETWEEN away_coach.start_date AND away_coach.calc_end_date
INNER JOIN {{ ref('silver_coach') }} home_coach
ON home_coach.team_id = silver_fixture.home_team_id  AND silver_fixture.fixture_date BETWEEN home_coach.start_date AND home_coach.calc_end_date
WHERE (away.total_shots_avg/home.total_shots_avg) IS NOT NULL
