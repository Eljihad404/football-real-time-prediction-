import time
import pandas as pd
import requests
import json
import io
import logging
from kafka import KafkaProducer
from minio import Minio
from sqlalchemy import create_engine, text

# --- Configuration ---
CSV_URL = "https://www.football-data.co.uk/mmz4281/2526/E0.csv"
# Note: Hostname is 'postgres' because we are inside the Docker network
DB_CONN = "postgresql://admin:password@postgres:5432/football_data"
KAFKA_TOPIC = "football_stream"
MINIO_BUCKET = "football-raw"

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

# --- Initialize Connections ---
def get_db_engine():
    return create_engine(DB_CONN)

def get_minio_client():
    # Hostname is 'minio' inside Docker network
    client = Minio(
        "minio:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )
    if not client.bucket_exists(MINIO_BUCKET):
        client.make_bucket(MINIO_BUCKET)
    return client

def get_kafka_producer():
    # Wait for Kafka to start
    while True:
        try:
            # Hostname is 'kafka' inside Docker network, port 29092
            return KafkaProducer(
                bootstrap_servers=['kafka:29092'],
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
        except Exception:
            logger.info("⏳ Waiting for Kafka to be ready...")
            time.sleep(5)

# --- Helper: Handle Foreign Keys (Get or Create ID) ---
def get_or_create_club(conn, club_name, league_id):
    # Check if club exists
    result = conn.execute(text("SELECT id FROM clubs WHERE name = :name"), {"name": club_name}).fetchone()
    if result:
        return result[0]
    else:
        # Insert new club
        result = conn.execute(
            text("INSERT INTO clubs (name, league_id) VALUES (:name, :lid) RETURNING id"),
            {"name": club_name, "lid": league_id}
        ).fetchone()
        conn.commit()
        return result[0]

# --- Main Logic ---
def run_pipeline():
    logger.info("🚀 Starting Football Data Pipeline...")
    
    # Wait a bit for DB to initialize
    time.sleep(10)
    
    engine = get_db_engine()
    minio_client = get_minio_client()
    producer = get_kafka_producer()
    
    # 1. Ensure League Exists
    with engine.connect() as conn:
        conn.execute(text("INSERT INTO leagues (id, name, country) VALUES (1, 'Premier League', 'England') ON CONFLICT (id) DO NOTHING"))
        conn.commit()
    
    last_row_count = 0
    
    logger.info("✅ Pipeline Ready. Monitoring CSV every 30 seconds...")

    while True:
        try:
            # Step 1: Fetch CSV
            response = requests.get(CSV_URL)
            response.raise_for_status()
            csv_content = response.content
            
            # Read into Pandas
            df = pd.read_csv(io.BytesIO(csv_content))
            current_row_count = len(df)
            
            # Step 2: Compare
            if current_row_count > last_row_count:
                new_rows_count = current_row_count - last_row_count
                logger.info(f"⚡ NEW DATA DETECTED: Found {new_rows_count} new matches.")
                
                # Get only new data
                new_data = df.iloc[last_row_count:]
                
                # Step 3: Send to MinIO (Raw Storage)
                timestamp = int(time.time())
                minio_client.put_object(
                    MINIO_BUCKET,
                    f"batch_{timestamp}.csv",
                    io.BytesIO(new_data.to_csv(index=False).encode('utf-8')),
                    length=len(new_data.to_csv(index=False).encode('utf-8')),
                    content_type="application/csv"
                )
                logger.info("   -> Saved raw CSV chunk to MinIO.")
                
                # Step 4: Process into Postgres & Kafka
                with engine.connect() as conn:
                    for _, row in new_data.iterrows():
                        # Handle Foreign Keys
                        home_id = get_or_create_club(conn, row['HomeTeam'], 1)
                        away_id = get_or_create_club(conn, row['AwayTeam'], 1)
                        
                        # Parse Date (CSV format is usually dd/mm/yyyy)
                        match_date = pd.to_datetime(f"{row['Date']} {row['Time']}", dayfirst=True)
                        
                        try:
                            # A. Send to Kafka
                            producer.send(KAFKA_TOPIC, row.to_dict())

                            # B. Insert into DB
                            query = text("""
                                INSERT INTO matches (league_id, home_club_id, away_club_id, match_date, home_score, away_score, status, season)
                                VALUES (:lid, :hid, :aid, :date, :h_score, :a_score, 'Finished', '2025/2026')
                                ON CONFLICT DO NOTHING
                            """)
                            conn.execute(query, {
                                "lid": 1, "hid": home_id, "aid": away_id, 
                                "date": match_date, 
                                "h_score": row['FTHG'], "a_score": row['FTAG']
                            })
                            conn.commit()
                        except Exception as e:
                            logger.error(f"   -> Error processing row: {e}")
                
                logger.info("   -> Synced to Postgres and Kafka.")
                last_row_count = current_row_count
                
            else:
                logger.info("... No new updates found.")
            
        except Exception as e:
            logger.error(f"Pipeline Error: {e}")
        
        time.sleep(30)

if __name__ == "__main__":
    run_pipeline()