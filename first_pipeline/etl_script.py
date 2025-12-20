import time
import pandas as pd
import requests
import json
import io
import logging
from kafka import KafkaProducer
from minio import Minio
from sqlalchemy import create_engine, text

# --- Configuration & Data Sources ---

# Database Connection
DB_CONN = "postgresql://admin:password@postgres:5432/football_data"
KAFKA_TOPIC = "football_stream"
MINIO_BUCKET = "football-raw"

# League Metadata (ID, Name, Country)
LEAGUE_META = {
    'E0': {'id': 1, 'name': 'Premier League', 'country': 'England'},
    'D1': {'id': 2, 'name': 'Bundesliga', 'country': 'Germany'},
    'SP1': {'id': 3, 'name': 'La Liga', 'country': 'Spain'},
    'F1': {'id': 4, 'name': 'Ligue 1', 'country': 'France'},
    'I1': {'id': 5, 'name': 'Serie A', 'country': 'Italy'}
}

# 1. Live Monitoring (Season 2025/2026)
LIVE_URLS = {
    'E0': "https://www.football-data.co.uk/mmz4281/2526/E0.csv",
    'D1': "https://www.football-data.co.uk/mmz4281/2526/D1.csv",
    'SP1': "https://www.football-data.co.uk/mmz4281/2526/SP1.csv",
    'F1': "https://www.football-data.co.uk/mmz4281/2526/F1.csv",
    'I1': "https://www.football-data.co.uk/mmz4281/2526/I1.csv"
}

# 2. Historical Data (Past Seasons)
HISTORY_DATA = {
    "2024/2025": [
        "https://www.football-data.co.uk/mmz4281/2425/E0.csv",
        "https://www.football-data.co.uk/mmz4281/2425/D1.csv",
        "https://www.football-data.co.uk/mmz4281/2425/SP1.csv",
        "https://www.football-data.co.uk/mmz4281/2425/F1.csv",
        "https://www.football-data.co.uk/mmz4281/2425/I1.csv"
    ],
    "2023/2024": [
        "https://www.football-data.co.uk/mmz4281/2324/E0.csv",
        "https://www.football-data.co.uk/mmz4281/2324/D1.csv",
        "https://www.football-data.co.uk/mmz4281/2324/SP1.csv",
        "https://www.football-data.co.uk/mmz4281/2324/F1.csv",
        "https://www.football-data.co.uk/mmz4281/2324/I1.csv"
    ],
    "2022/2023": [
        "https://www.football-data.co.uk/mmz4281/2223/E0.csv",
        "https://www.football-data.co.uk/mmz4281/2223/D1.csv",
        "https://www.football-data.co.uk/mmz4281/2223/SP1.csv",
        "https://www.football-data.co.uk/mmz4281/2223/F1.csv",
        "https://www.football-data.co.uk/mmz4281/2223/I1.csv"
    ],
    "2021/2022": [
        "https://www.football-data.co.uk/mmz4281/2122/E0.csv",
        "https://www.football-data.co.uk/mmz4281/2122/D1.csv",
        "https://www.football-data.co.uk/mmz4281/2122/SP1.csv",
        "https://www.football-data.co.uk/mmz4281/2122/F1.csv",
        "https://www.football-data.co.uk/mmz4281/2122/I1.csv"
    ]
}

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

# --- Connection Helpers ---
def get_db_engine():
    return create_engine(DB_CONN)

def get_minio_client():
    client = Minio("minio:9000", access_key="minioadmin", secret_key="minioadmin", secure=False)
    if not client.bucket_exists(MINIO_BUCKET):
        client.make_bucket(MINIO_BUCKET)
    return client

def get_kafka_producer():
    while True:
        try:
            return KafkaProducer(bootstrap_servers=['kafka:29092'], value_serializer=lambda x: json.dumps(x).encode('utf-8'))
        except Exception:
            logger.info("⏳ Waiting for Kafka...")
            time.sleep(5)

# --- Database Helpers ---
def init_leagues(conn):
    """Inserts the top 5 leagues into the DB if not exists."""
    for code, data in LEAGUE_META.items():
        conn.execute(
            text("INSERT INTO leagues (id, name, country) VALUES (:id, :name, :country) ON CONFLICT (id) DO NOTHING"),
            {"id": data['id'], "name": data['name'], "country": data['country']}
        )
    conn.commit()

def get_or_create_club(conn, club_name, league_id):
    """Finds a club ID or creates it if new."""
    result = conn.execute(text("SELECT id FROM clubs WHERE name = :name"), {"name": club_name}).fetchone()
    if result:
        return result[0]
    else:
        result = conn.execute(
            text("INSERT INTO clubs (name, league_id) VALUES (:name, :lid) RETURNING id"),
            {"name": club_name, "lid": league_id}
        ).fetchone()
        conn.commit()
        return result[0]

def process_batch(df, league_code, season, minio_client, engine, producer=None, raw_filename=None):
    """Handles the saving to MinIO, Postgres, and optionally Kafka."""
    
    # 1. Save Raw to MinIO
    if raw_filename:
        csv_bytes = df.to_csv(index=False).encode('utf-8')
        minio_client.put_object(
            MINIO_BUCKET, 
            raw_filename, 
            io.BytesIO(csv_bytes), 
            length=len(csv_bytes), 
            content_type="application/csv"
        )
        logger.info(f"   💾 Saved {raw_filename} to MinIO.")

    # 2. Process to Postgres (and Kafka if live)
    league_info = LEAGUE_META.get(league_code)
    if not league_info:
        logger.warning(f"Unknown league code {league_code}, skipping DB insert.")
        return

    with engine.connect() as conn:
        count = 0
        for _, row in df.iterrows():
            try:
                # Handle standard football-data.co.uk columns
                home_team = row.get('HomeTeam')
                away_team = row.get('AwayTeam')
                fthg = row.get('FTHG') # Full Time Home Goals
                ftag = row.get('FTAG') # Full Time Away Goals
                
                # Check for valid data
                if pd.isna(home_team) or pd.isna(away_team):
                    continue

                home_id = get_or_create_club(conn, home_team, league_info['id'])
                away_id = get_or_create_club(conn, away_team, league_info['id'])
                
                # Flexible Date Parsing
                date_str = str(row['Date'])
                time_str = str(row.get('Time', '00:00'))
                try:
                    match_date = pd.to_datetime(f"{date_str} {time_str}", dayfirst=True)
                except:
                    match_date = pd.to_datetime(date_str, dayfirst=True)

                # Send to Kafka (Only if producer is provided - i.e., Live Data)
                if producer:
                    producer.send(KAFKA_TOPIC, {
                        "league": league_info['name'],
                        "home": home_team,
                        "away": away_team,
                        "date": str(match_date),
                        "score": f"{fthg}-{ftag}"
                    })

                # Insert into DB
                query = text("""
                    INSERT INTO matches (league_id, home_club_id, away_club_id, match_date, home_score, away_score, status, season)
                    VALUES (:lid, :hid, :aid, :date, :h_score, :a_score, 'Finished', :season)
                    ON CONFLICT DO NOTHING
                """)
                conn.execute(query, {
                    "lid": league_info['id'], 
                    "hid": home_id, 
                    "aid": away_id, 
                    "date": match_date, 
                    "h_score": fthg, 
                    "a_score": ftag,
                    "season": season
                })
                count += 1
            except Exception as e:
                logger.error(f"Error row: {e}")
        conn.commit()
        logger.info(f"   ✅ Processed {count} matches for {league_info['name']} ({season}).")

# --- Main Pipeline ---
def run_pipeline():
    logger.info("🚀 Starting Football ETL Pipeline...")
    time.sleep(10) # Warmup

    engine = get_db_engine()
    minio_client = get_minio_client()
    producer = get_kafka_producer()

    # Init Leagues
    with engine.connect() as conn:
        init_leagues(conn)

    # --- PHASE 1: HISTORICAL DATA INGESTION (Once) ---
    logger.info("📚 Checking Historical Data...")
    for season, urls in HISTORY_DATA.items():
        for url in urls:
            try:
                # Derive league code from URL (e.g., .../E0.csv -> E0)
                league_code = url.split('/')[-1].replace('.csv', '')
                filename = f"history_{season.replace('/','-')}_{league_code}.csv"
                
                # Check if file already exists in MinIO to avoid re-processing
                try:
                    minio_client.stat_object(MINIO_BUCKET, filename)
                    logger.info(f"   ⏩ Skipping {filename}, already in MinIO.")
                except:
                    logger.info(f"   📥 Downloading history: {season} - {league_code}")
                    response = requests.get(url)
                    response.raise_for_status()
                    df = pd.read_csv(io.BytesIO(response.content))
                    
                    # Process (MinIO + Postgres, No Kafka)
                    process_batch(df, league_code, season, minio_client, engine, producer=None, raw_filename=filename)
            except Exception as e:
                logger.error(f"Failed history {url}: {e}")

    # --- PHASE 2: LIVE MONITORING (Loop) ---
    logger.info("🔴 Starting Live Monitor for 2025/2026...")
    
    # State tracking: { 'E0': last_row_count, 'D1': last_row_count ... }
    league_state = {code: 0 for code in LIVE_URLS.keys()}

    while True:
        for code, url in LIVE_URLS.items():
            try:
                response = requests.get(url)
                if response.status_code != 200:
                    continue
                
                df = pd.read_csv(io.BytesIO(response.content))
                current_count = len(df)
                last_count = league_state[code]

                if current_count > last_count:
                    new_rows = current_count - last_count
                    logger.info(f"⚡ NEW DATA: {code} ({new_rows} matches)")
                    
                    new_data = df.iloc[last_count:]
                    
                    # Generate Batch Filename
                    timestamp = int(time.time())
                    filename = f"live_{timestamp}_{code}.csv"

                    # Process (MinIO + Postgres + Kafka)
                    process_batch(new_data, code, "2025/2026", minio_client, engine, producer, raw_filename=filename)
                    
                    league_state[code] = current_count
                
            except Exception as e:
                logger.error(f"Live Error {code}: {e}")

        logger.info("... Sleeping 30s")
        time.sleep(30)

if __name__ == "__main__":
    run_pipeline()