# Introduction: Cloud-native Deep Learning MLOps Pipeline

## 1.1. Pipeline and Infra
Data is gathered from  ((https://www.api-football.com/), using the API.

### 1.12. Infrastructure
The project is hosted entirely in cloud-native environments. The entire pipeline is automated and meant to automatically pull data once new data becomes available for past matches.

### 1.13 Environment and CI/CD:
GitHub and Github actions to build docker images in Google Cloud Artifact Registry.

### 1.14 Extractor:
Using Go to extract data from the API above using channels to pull relevant data with greater speed than traditional Python extractor.
These images were deployed to Cloud Run on GCP.

### 1.15 Load:
Use PySpark to load the data tables into Databricks Hive.

### 1.16 Transform:
Use dbt and SQL on Databricks cluster to transform and feature engineer said data tables into appropriate data for Deep and Machine learning.

![alt text](https://github.com/tallalUsman/deeplearning-mlops/blob/main/pic/dag.png?raw=true)


### 1.17 Deep Learning and Machine Learning:
Use Databricks hosted jupyter notebook to run deep learning and machine learning models.

## 2. Background
This project aims to use football data for football players, matches, and stats to attempt to predict the outcomes for the recent 2022-23 football seasons for the top First and Second Football divisions in Spain, France, England, Germany, Italy, Belgium, Scotland, and the Netherlands. The 2014-15 to 2022-23 season match outcomes are used as a training set.


The project uses deep learning models and traditional machine learning best practices and methods such as cross-validation for parameter selection, and balancing classes in addition to advanced machine learning techniques such as Lasso regressions, Random Forests, and Principal component analysis.

Predicting match outcomes is an especially tricky exercise despite having a lot of metrics regarding the statistics of every player in a team, other factors such as morale, injuries, pitch/weather conditions, and the specific strategies employed by teams against each other tend to be very important and difficult to measure. Despite the use of fixed effects it is important to realize that there is some aspect of reinforcement learning, team strategies are constantly adapting, at times several times within the same game. A manager realizing that they lack in holding the opposing team back when they counter may choose to leave more defenders behind when they attack. Similarly, the opposing manager may realize the change in strategy and adapt as well.

This project aims to predict the matches with greater accuracy than existing odds regarding match outcomes, if so tries to adjust for the optimal betting strategy.

The project also assesses the importance of the dynamics of the game in recent years, with the inflow of foreign funding and the ability of teams to purchase the best players they please, we are seeing the rise of those clubs which possess the most money. However, is the rise due to their ability to buy the best players or the best staff to create the best tactics? Likely the answer is a mixture of both, but is strategy important enough that smaller teams that lack funding can pull off wins with a superior strategy?

While there are ways of controlling for the strategy they require more detailed non-public data and more computationally intensive techniques which we will discuss in detail later on.


## 3. The Results

We use techniques ranging from Multinomial Logit to Lasso regression to more complex and computationally intensive techniques such as Random Forests. 
Our results show that the Boosted Trees model achieves the greatest accuracy.

However, one consistent pattern illustrated in all implemented ML techniques shows that the models have more difficulty accurately predicting a draw as compared to a win or a loss. This might be explained by the fact that draws themselves are a product of idiosyncrasies or team strategies to "park the bus" (only play defensive) in the face of a far stronger opponent. 

Several football strategies such as playing on the counter, mean that strong teams can draw with teams that anticipate they have little probability of winning using usual strategies and therefore heavily rely on defense to secure a draw. Therefore we are likely to see a clear win/loss in teams that are closely matched in terms of metrics however if there exists an imbalance in the strength of the teams we might see a draw with greater likelihood as compared to a match with closely matched teams.

The results show that without the deficiency of draw predictions, our models do far better for loses and wins as compared to draw. For instance, the Boosted trees predict wins by an accuracy of 75%!
