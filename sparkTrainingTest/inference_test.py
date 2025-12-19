from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel
from pyspark.sql.functions import col, udf, lit
from pyspark.sql.types import StringType

# 1. Initialize Spark
spark = SparkSession.builder \
    .appName("FootballInference") \
    .master("local[*]") \
    .getOrCreate()

# 2. Load the Saved Model
model_path = "data/football_xgb_model"
print(f"Loading model from {model_path}...")
try:
    loaded_model = PipelineModel.load(model_path)
    print("Model loaded successfully!")
except Exception as e:
    print("Error loading model. Did you run train.py successfully?")
    exit(1)

# 3. Define New Data (Live Match Scenario)
# We want to predict: Real Madrid (Home) vs Barcelona (Away)
# Current Odds: Home=2.10, Draw=3.50, Away=3.20
# Note: We ADD a dummy "FTR" column because the pipeline expects it.
input_data = [
    ("Real Madrid", "Barcelona", 2.10, 3.50, 3.20, "?"),
    ("Man City", "Liverpool", 1.80, 4.00, 3.80, "?")
]

columns = ["HomeTeam", "AwayTeam", "B365H", "B365D", "B365A", "FTR"]

inference_df = spark.createDataFrame(input_data, columns)

# 4. Run Prediction
print("Running inference...")
predictions = loaded_model.transform(inference_df)

# 5. Decode the Results
# The model outputs a numeric prediction (e.g., 0.0, 1.0). 
# We need to know if 0.0 means "Home", "Draw", or "Away".
# We can retrieve this from the 'label_indexer' which is Stage 2 of your pipeline.

label_indexer_model = loaded_model.stages[2] 
labels = label_indexer_model.labels  # This is a list like ['H', 'A', 'D']
print(f"Model Labels Mapping: {dict(enumerate(labels))}")

# Create a UDF to convert the numeric prediction back to text
def decode_prediction(val):
    return labels[int(val)]

decode_udf = udf(decode_prediction, StringType())

# Add a readable text column
final_results = predictions.withColumn("PredictedResult", decode_udf(col("prediction")))

# 6. Show Final Output
final_results.select(
    "HomeTeam", 
    "AwayTeam", 
    "PredictedResult", 
    "probability" # Shows [Prob(Index 0), Prob(Index 1), Prob(Index 2)]
).show(truncate=False)

spark.stop()