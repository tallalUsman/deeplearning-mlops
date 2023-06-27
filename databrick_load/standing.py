from pyspark.sql.functions import col, explode
from pyspark.sql import functions as F
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()

input_dir = "gs://football_data_api/raw/standing/144/2015.json"

# Load the entire file as a single record
json = spark.sparkContext.wholeTextFiles(input_dir).values()
df = spark.read.json(json)

df1 = (df.select(explode(col("response")))
        .withColumn('ranking', (F.col('col.league.standings').getItem(0)))
        .select(col("col").alias("col"),explode(col("ranking")).alias("new_ranking"))
        .withColumn('league_id', F.col('col.league.id'))
        .withColumn('season', F.col('col.league.season'))
        .withColumn('rank', F.col('new_ranking.rank'))
        .withColumn('team_id', F.col('new_ranking.team.id'))
        .withColumn('played', F.col('new_ranking.all.played'))
        .withColumn('won', F.col('new_ranking.all.win'))
        .withColumn('lost', F.col('new_ranking.all.lose'))
        .withColumn('draw', F.col('new_ranking.all.draw'))
        .drop('col', 'new_ranking')
       )


df1.write.format("parquet").mode("overwrite").saveAsTable("bronze_standings")
