from pyspark.sql.functions import col, explode
from pyspark.sql import functions as F
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()

input_dir = "gs://football_data_api/raw/coach/"

# Load the entire file as a single record
json = spark.sparkContext.wholeTextFiles(input_dir).values()
df = spark.read.json(json)

df1 = (df.select(explode(col("response")))
        .withColumn('coach_id', F.col('col.id'))
        .withColumn('career', F.col('col.career'))
        .select(col("coach_id") ,explode(col("career")))
        .withColumn('team_id', F.col('col.team.id'))
        .withColumn('start_date', F.col('col.start'))
        .withColumn('end_date', F.col('col.end'))
        .drop('col')
       )

df1.write.format("parquet").mode("overwrite").saveAsTable("football.bronze_coach")
