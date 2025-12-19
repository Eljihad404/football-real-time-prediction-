# Use your specific local image
FROM apache/spark:3.5.7-python3

# Switch to root to install packages
USER root

# Install required Python libraries for the model
# pyarrow is recommended for speeding up data transfer between Spark and XGBoost
RUN pip install --no-cache-dir xgboost pandas numpy pyarrow scikit-learn[alldeps]

# Switch back to the default Spark user (security best practice, though optional for local dev)
USER 185