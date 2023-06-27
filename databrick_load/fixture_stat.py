from pyspark.sql.functions import col, explode
from pyspark.sql import functions as F
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()

input_dir = "gs://football_data_api/raw/fixture-stats/*/"

# Load the entire file as a single record
json = spark.sparkContext.wholeTextFiles(input_dir).values()
df = spark.read.json(json)

df1 = (df.select(col("Data.parameters.fixture").alias("fixture_id"), explode(col("Data.response")))
               .withColumn('team_id', F.col('col.team.id'))
               .withColumn('total_shots', F.col('col.statistics').getItem(2).getField('value'))
               .withColumn('possession', F.col('col.statistics').getItem(9).getField('value'))
               .withColumn('red_cards', F.col('col.statistics').getItem(11).getField('value'))
               .withColumn('gk_saves', F.col('col.statistics').getItem(12).getField('value'))
               .withColumn('fouls', F.col('col.statistics').getItem(6).getField('value'))
               .withColumn('tot_passes', F.col('col.statistics').getItem(13).getField('value'))
               .withColumn('a_passes', F.col('col.statistics').getItem(14).getField('value'))
               .drop('col'))

df1.write.format("parquet").mode("overwrite").saveAsTable("football.bronze_fixture_stat")