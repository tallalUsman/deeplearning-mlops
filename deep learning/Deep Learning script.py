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
categorical_cols = ["coach_id_home", "league_id", "season", "coach_id_away"]

# Loop through categorical columns and apply StringIndexer
for col in categorical_cols:
    indexer = StringIndexer(inputCol=col, outputCol=col + "Index")
    spark_df = indexer.fit(spark_df).transform(spark_df)

# COMMAND ----------

spark_df = spark_df.drop(
    "fixture_date",
    "fixture_id",
    "referee",
    "venue_id",
    "status",
    "away_team_id",
    "home_team_id",
    "match_result",
    "coach_id_home",
    "coach_id_away",
    "league_id",
    "season",
)

spark_df = spark_df.dropna()

# COMMAND ----------

spark_df.show(10)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Training and Testing Set: Load

# COMMAND ----------

pandas_df = spark_df.toPandas()
pandas_df.head(5)

# COMMAND ----------

targets1 = pandas_df["away_goals"].values.flatten()
targets2 = pandas_df["home_goals"].values.flatten()

features = pandas_df.drop(["away_goals", "home_goals"], axis=1).values

# COMMAND ----------

test_size = int(0.08 * 22603)  # represents size of validation set
val_size = test_size
train_size = 22603 - test_size * 2
train_size, val_size, test_size

# COMMAND ----------

dataset = torch.utils.data.TensorDataset(
    torch.tensor(features).float(),
    torch.tensor(targets1).unsqueeze(-1),
    torch.tensor(targets2).unsqueeze(-1),
)
train_ds, val_ds, test_ds = random_split(dataset, [train_size, val_size, test_size])
batch_size = 256

# COMMAND ----------

train_loader = DataLoader(
    train_ds, batch_size, shuffle=True, num_workers=4, pin_memory=False
)
val_loader = DataLoader(val_ds, batch_size * 2, num_workers=4, pin_memory=False)
test_loader = DataLoader(test_ds, batch_size * 2, num_workers=4, pin_memory=False)

# COMMAND ----------

for x, y1, y2 in test_loader:
    print(x.shape, y1.shape, y2.shape)
    break

# COMMAND ----------

train_loader

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup PyTorch Model

# COMMAND ----------

input_size = 14
output_size = 1

# COMMAND ----------

output_size = 1


class FootballModelMk2(nn.Module):
    def __init__(self, input_size, output_size):
        super().__init__()
        self.fc1 = nn.Linear(input_size, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3_1 = nn.Linear(32, output_size)  # output for target1
        self.fc3_2 = nn.Linear(32, output_size)  # output for target2
        self.dp = nn.Dropout(0.5)
        self.bn1 = nn.BatchNorm1d(64)
        self.bn2 = nn.BatchNorm1d(32)

    def forward(self, x):
        x = F.relu(self.bn1(self.fc1(x)))
        x = self.dp(x)
        x = F.relu(self.bn2(self.fc2(x)))
        x = self.dp(x)
        out1 = self.fc3_1(x)  # prediction for target1
        out2 = self.fc3_2(x)  # prediction for target2
        return out1, out2

# COMMAND ----------

crit = nn.L1Loss()  # criterion
opt_func = torch.optim.SGD  # optimizer function (w/o params or lr)

# COMMAND ----------

def fit(epochs, lr, model, train_loader, val_loader, crit, opt_func, device):
    history = []
    # define optimizer
    opt = opt_func(model.parameters(), lr=lr)
    # loop for num of epochs
    for epoch in range(epochs):
        # training per epoch (iterate through each batch)
        for inputs, target1, target2 in train_loader:
            # put inputs to the same device as model (GPU or CPU)
            inputs, target1, target2 = (
                inputs.to(device),
                target1.to(device),
                target2.to(device),
            )
            # using optimizer & loss
            opt.zero_grad()
            (outs1, outs2), (loss1, loss2) = step(inputs, target1, target2, model, crit)
            loss = (
                loss1 + loss2
            )  # consider if this is the appropriate way to handle multiple losses
            loss.backward()
            opt.step()
        # evaluate model on validation set every epoch
        val_results = evaluate(model, val_loader, crit, device)
        # printing as output every 5 epochs
        if (epoch + 1) % 5 == 0 or (epoch + 1) == epochs:
            print(f'Epoch #{epoch + 1} ==> Val Loss: {val_results["avg_loss"]}')
        history.append(val_results)
    return history


def evaluate(model, loader, crit, device):
    losses = []
    accuracies = []
    # define the tolerance level
    tol = 0.4
    model.eval()
    # tracking gradient not needed
    with torch.no_grad():
        # looping over data loader
        for inputs, target1, target2 in train_loader:
            inputs, target1, target2 = (
                inputs.to(device),
                target1.to(device),
                target2.to(device),
            )
            (outs1, outs2), (loss1, loss2) = step(
                inputs, target1, target2, model, crit, evaluate=True
            )
            loss = (
                loss1 + loss2
            )  # consider if this is the appropriate way to handle multiple losses
            losses.append(loss.item())
            acc1 = ((outs1 - target1).abs() <= tol).float().mean()
            acc2 = ((outs2 - target2).abs() <= tol).float().mean()
            accuracies.append((acc1 + acc2) / 2)  # average of the two accuracies

    avg_loss = sum(losses) / len(losses)
    avg_acc = sum(accuracies) / len(accuracies)  # compute average "accuracy"
    return {"avg_loss": avg_loss, "avg_acc": avg_acc}


# function to input features into model (used for training + validation)
def step(inputs, target1, target2, model, crit, evaluate=False):
    outs1, outs2 = model(inputs)
    loss1 = crit(outs1, target1)
    loss2 = crit(outs2, target2)
    return (outs1, outs2), (loss1, loss2)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Use GPU if available

# COMMAND ----------

if torch.cuda.is_available():
    device = torch.device("cuda")
else:
    device = torch.device("cpu")

# COMMAND ----------

device

# COMMAND ----------

model = FootballModelMk2(input_size, output_size).to(device)
model

# COMMAND ----------

# MAGIC %md
# MAGIC ### Visualization Setup

# COMMAND ----------

import matplotlib.pyplot as plt


def visualize(hist, acc=False):
    losses = [x["avg_loss"] for x in hist]
    accs = [x["avg_acc"] for x in hist]
    if acc:
        plt.plot(accs)
        plt.ylabel("Accuracy (%)")
        plt.title("Accuracy over Epochs")
    else:
        plt.plot(losses)
        plt.ylabel("Losses")
        plt.title("Losses over Epochs")
    plt.xlabel("Epochs")
    plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run Model

# COMMAND ----------

before_train = evaluate(model, train_loader, crit, device)
before_train

hist = [evaluate(model, val_loader, crit, device)]

# COMMAND ----------

hist += fit(25, 1e-3, model, train_loader, val_loader, crit, opt_func, device)

# COMMAND ----------

hist += fit(50, 1e-4, model, train_loader, val_loader, crit, opt_func, device)

# COMMAND ----------

after_train = evaluate(model, test_loader, crit, device)
after_train

# COMMAND ----------

visualize(hist)

# COMMAND ----------

visualize(hist, acc=True)
