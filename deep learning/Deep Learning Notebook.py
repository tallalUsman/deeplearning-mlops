# Databricks notebook source
# MAGIC %md
# MAGIC # Deep Learning: Feed-Forward model to Predict scores

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import Libraries

# COMMAND ----------

from pyspark.sql import SparkSession
import pyspark.pandas as ps
from pyspark.ml.feature import StringIndexer



# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Spark Dataframe and apply transformations

# COMMAND ----------


# Create a Spark session
spark = SparkSession.builder.getOrCreate()

# Read a table into a Spark DataFrame
spark_df = spark.table("football.gold_dl_table")


# COMMAND ----------

# MAGIC %md
# MAGIC ### Label encodings for categorical variables

# COMMAND ----------

# List of categorical columns to encode
categorical_cols = ['coach_id_home', 'league_id', 'season', 'coach_id_away']

# Loop through categorical columns and apply StringIndexer
for col in categorical_cols:
    indexer = StringIndexer(inputCol=col, outputCol=col+"Index")
    spark_df = indexer.fit(spark_df).transform(spark_df)

# COMMAND ----------

spark_df = spark_df.drop('fixture_date', 'fixture_id', 'referee', 'venue_id', 'status', 'away_team_id', 'home_team_id', 'match_result', 'coach_id_home', 'coach_id_away','league_id', 'season')

# COMMAND ----------

spark_df.show(10)
