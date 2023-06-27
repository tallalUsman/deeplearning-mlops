from pyspark.sql.functions import col, explode
from pyspark.sql import functions as F
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()

input_dir = "gs://football_data_api/raw/fixtures/*/"

# Load the entire file as a single record
json = spark.sparkContext.wholeTextFiles(input_dir).values()
df = spark.read.json(json)


df1 = (df.select(col("parameters").alias("fixture_date"), explode(col("response")))
        .withColumn('fixture_date', F.col('fixture_date.date'))
        .withColumn('fixture_id', F.col('col.fixture.id'))
        .withColumn('referee', F.col('col.fixture.referee'))
        .withColumn('status', F.col('col.fixture.status.short'))
        .withColumn('venue_id', F.col('col.fixture.venue.id'))
        .withColumn('away_goals', F.col('col.goals.away'))
        .withColumn('home_goals', F.col('col.goals.home'))
        .withColumn('league_id', F.col('col.league.id'))
        .withColumn('season', F.col('col.league.season'))
        .withColumn('away_team_id', F.col('col.teams.away.id'))
        .withColumn('home_team_id', F.col('col.teams.home.id'))
        .drop('col'))


df1.write.format("parquet").mode("overwrite").saveAsTable("football.bronze_fixture")