WITH fixture_dates AS (
    SELECT DISTINCT fixture_date, fixture_id
    FROM {{ ref('silver_fixture') }}
)

SELECT silver_fixture_stat.* 
, fixture_dates.fixture_date
FROM {{ ref('silver_fixture_stat') }}
INNER JOIN fixture_dates
USING (fixture_id)
ORDER BY team_id, fixture_date