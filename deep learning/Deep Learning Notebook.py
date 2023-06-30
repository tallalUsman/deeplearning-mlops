# Databricks notebook source
# MAGIC %md
# MAGIC # Deep Learning: Feed-Forward model to Predict scores

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import Libraries

# COMMAND ----------

!pip install torch

# COMMAND ----------

from pyspark.sql import SparkSession
import pyspark.pandas as ps
from pyspark.ml.feature import StringIndexer

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import random_split, TensorDataset, DataLoader

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

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Training and Testing Set

# COMMAND ----------

train_df, test_df = spark_df.randomSplit([0.8, 0.2], seed=42)


# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup PyTorch Model

# COMMAND ----------

input_size = 15
output_size = 2

# COMMAND ----------

class LOLModelmk2(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(input_size, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 16)
        self.fc4 = nn.Linear(16, output_size)
#adding dropout between layers to avoid overfitting
        self.dp = nn.Dropout(0.5)

    def forward(self, x):
        x = self.fc1(x)
        x = F.relu(x)
        x = self.fc2(x)
        x = F.relu(x)
        x = self.fc3(x)
        x = F.relu(x)
        x = self.fc4(x)
        return x

# COMMAND ----------

crit = nn.L1Loss() #criterion
opt_func = torch.optim.SGD #optimizer function (w/o params or lr)

# COMMAND ----------

def fit(epochs, lr, model, train_loader, val_loader):
    h = []
    # define optimizer
    opt = opt_func(model.parameters(), lr=lr)
    # loop for num of epochs
    for epoch in range(epochs):
        # training per epoch (iterate tru each batch)
        for inputs, labels in train_loader:
            # put inputs to gpu (explained later)
            inputs, labels = inputs.to(device), labels.to(device)
            # using optimizer & loss
            opt.zero_grad()
            _, loss = step(inputs, labels)
            loss.backward()
            opt.step()
        # evaluate model on validation set every epoch
        val_results = evaluate(model, val_loader)
        # printing as output every 5 epochs
        if (epoch + 1) % 5 == 0 or (epoch + 1) == epochs:
            print(f'Epoch #{epoch + 1} ==> Val Loss: {val_results["avg_loss"]} | Val Acc: {val_results["avg_acc"]}')
        h.append(val_results)
    return h
        
def evaluate(model, loader):
    losses = []
    accs = []
    # tracking gradient not needed
    with torch.no_grad():
        # looping over data loader
        for inputs, labels in loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outs, loss = step(inputs, labels, evaluate=True)
            # computing accuracy (function below)
            acc = accuracy(outs, labels)
            losses.append(loss)
            accs.append(acc)
    # avg loss + acc for all data on loader
    avg_loss = sum(losses) / len(losses)
    avg_acc = sum(accs) / len(accs)
    return {'avg_loss':avg_loss, 'avg_acc':avg_acc}
            
# function to input features into model (used for training + validation)
def step(inputs, labels, evaluate=False):
    if evaluate:
        model.eval()
    else:
        model.train()
    outs = model(inputs)
    loss = crit(outs, labels)
    return outs, loss

def accuracy(outs, labels):
    # find the highest probability of the two categories
    _, preds = torch.max(outs, dim=1)
    # return % of correct predictions (matched w/ labels)
    return (torch.tensor(torch.sum(preds==labels).item() / len(preds))) * 100    

# COMMAND ----------

if torch.cuda.is_available():
    device = torch.device('cuda')
else:
    device = torch.device('cpu')

# COMMAND ----------

device

# COMMAND ----------

model = LOLModelmk2().to(device)
model

