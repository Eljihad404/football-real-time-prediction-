from pyspark.sql import SparkSession
from pyspark.ml.feature import StringIndexer, VectorAssembler, IndexToString
from pyspark.ml import Pipeline
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from xgboost.spark import SparkXGBClassifier

# 1. Initialize Spark
spark = SparkSession.builder \
    .appName("FootballPredictionXGBoost") \
    .master("local[*]") \
    .config("spark.driver.memory", "2g") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR") # Reduce noise in console

# 2. Load Data (Mapped volume path)
data_path = "data/SP1.csv"
print(f"Loading data from {data_path}...")

try:
    df = spark.read.csv(data_path, header=True, inferSchema=True)
except Exception as e:
    print("Error loading file. Make sure SP1.csv is in the 'data' folder.")
    raise e

# 3. Select Features (Betting Odds)
raw_data = df.select("HomeTeam", "AwayTeam", "B365H", "B365D", "B365A", "FTR").dropna()

# 4. Feature Engineering
home_indexer = StringIndexer(inputCol="HomeTeam", outputCol="HomeTeamIdx", handleInvalid="keep")
away_indexer = StringIndexer(inputCol="AwayTeam", outputCol="AwayTeamIdx", handleInvalid="keep")
label_indexer = StringIndexer(inputCol="FTR", outputCol="label")

assembler = VectorAssembler(
    inputCols=["HomeTeamIdx", "AwayTeamIdx", "B365H", "B365D", "B365A"],
    outputCol="features"
)

# 5. XGBoost Classifier
xgb_classifier = SparkXGBClassifier(
    features_col="features",
    label_col="label",
    num_workers=1,              # IMPORTANT: Set to 1 for local docker testing to avoid resource lock
    num_class=3
)

# 6. Pipeline & Training
pipeline = Pipeline(stages=[home_indexer, away_indexer, label_indexer, assembler, xgb_classifier])
train_data, test_data = raw_data.randomSplit([0.8, 0.2], seed=42)

print("Starting training...")
model = pipeline.fit(train_data)
print("Training Complete.")

# 7. Evaluate
predictions = model.transform(test_data)
evaluator = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="accuracy")
accuracy = evaluator.evaluate(predictions)
print(f"Model Accuracy: {accuracy:.2%}")

# 8. Save Model
model_save_path = "data/football_xgb_model"
model.write().overwrite().save(model_save_path)
print(f"Model saved to {model_save_path}")

spark.stop()