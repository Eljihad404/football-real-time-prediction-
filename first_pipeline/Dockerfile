FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc

# Install Python libraries
RUN pip install pandas requests kafka-python minio psycopg2-binary sqlalchemy

CMD ["python", "-u", "etl_script.py"]