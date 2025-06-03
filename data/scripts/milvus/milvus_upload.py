from pymilvus import connections, utility # Import utility
from pymilvus import (FieldSchema, DataType, CollectionSchema, Collection)
import numpy as np
import pandas as pd

# Milvus connection details -  Ensure these are correct for your instance
ENDPOINT = "https://in03-360d7a6acbd9660.serverless.gcp-us-west1.cloud.zilliz.com"
TOKEN = "0655b3db6ad52e4419627358025db8c966d6de3929cf4894e14fcc54cc5d16252ec0ce468937a2f478cb9c09a5932dfdee73e180" # Replace with your actual token if different
connections.connect(uri=ENDPOINT, token=TOKEN, alias="default")

# 1. Define the target collection name
TARGET_COLLECTION_NAME = "ucla_spring2025_events"

# 2. Define Schema (event_id as INT64 primary key)
fields = [
    FieldSchema(name="event_id", dtype=DataType.INT64, is_primary=True, auto_id=False), # auto_id=False to use your provided IDs
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),  # OpenAI embedding size
    FieldSchema(name="event_name", dtype=DataType.VARCHAR, max_length=512),
    FieldSchema(name="event_tags", dtype=DataType.VARCHAR, max_length=512),
    FieldSchema(name="event_programe", dtype=DataType.VARCHAR, max_length=512),
    FieldSchema(name="event_location", dtype=DataType.VARCHAR, max_length=512),
    FieldSchema(name="event_description", dtype=DataType.VARCHAR, max_length=4096),
]
schema = CollectionSchema(fields, description="UCLA Spring 2025 Club Events Database")

# 3. Clear existing data: Drop the collection if it exists
if utility.has_collection(TARGET_COLLECTION_NAME, using="default"):
    print(f"Collection '{TARGET_COLLECTION_NAME}' exists. Dropping it to clear data...")
    utility.drop_collection(TARGET_COLLECTION_NAME, using="default")
    print(f"Collection '{TARGET_COLLECTION_NAME}' dropped.")

# 4. Create the new collection
print(f"Creating collection '{TARGET_COLLECTION_NAME}'...")
collection = Collection(name=TARGET_COLLECTION_NAME, schema=schema, using="default")
print(f"Collection '{TARGET_COLLECTION_NAME}' created successfully.")

# 5. Create index for the 'embedding' field
print(f"Creating index for field 'embedding' in collection '{TARGET_COLLECTION_NAME}'...")
index_params = {
    "metric_type": "L2",      # Or "IP" for cosine similarity
    "index_type": "AUTOINDEX", # Or "IVF_FLAT", "HNSW" depending on Zilliz Cloud/Milvus version and needs
    "params": {} # For AUTOINDEX, params are usually not needed. For IVF_FLAT: {"nlist": 128}
}
collection.create_index(field_name="embedding", index_params=index_params)
print("Index created successfully.")

# Load collection into memory for searching
collection.load()
print(f"Collection '{TARGET_COLLECTION_NAME}' loaded.")

# 6. Load data from CSV
print("Loading data from processed_embeddings.csv...")
try:
    embedding_df = pd.read_csv("processed_embeddings_20250602.csv")
    # Ensure event_id is integer
    embedding_df["event_id"] = embedding_df["event_id"].astype(np.int64)
    # Ensure other text fields are strings and handle NaNs
    for col in ["event_name", "event_tags", "event_programe", "event_location", "event_description"]:
        embedding_df[col] = embedding_df[col].fillna("").astype(str)

except FileNotFoundError:
    print("ERROR: processed_embeddings.csv not found. Please run process_and_embed_data.py first.")
    exit()
except Exception as e:
    print(f"ERROR: Could not read or process processed_embeddings.csv: {e}")
    exit()

if embedding_df.empty:
    print("WARNING: processed_embeddings.csv is empty. No data to insert.")
    exit()

# 7. Prepare data for insertion
# The order of lists must match the order of fields in your schema (event_id, embedding, event_name, ...)
data_to_insert = [
    embedding_df["event_id"].tolist(),
    embedding_df["embedding"].apply(lambda x: eval(x) if isinstance(x, str) else x).tolist(), # Convert string representation of list to actual list
    embedding_df["event_name"].tolist(),
    embedding_df["event_tags"].tolist(),
    embedding_df["event_programe"].tolist(),
    embedding_df["event_location"].tolist(),
    embedding_df["event_description"].tolist(),
]

# 8. Insert data into Milvus
print(f"Inserting {len(embedding_df)} rows into '{TARGET_COLLECTION_NAME}'...")
try:
    insert_result = collection.insert(data_to_insert)
    collection.flush() # Ensure data is persisted
    print(f"Data inserted. Number of entities in collection: {collection.num_entities}")
    # You can check insert_result.insert_count if needed
except Exception as e:
    print(f"ERROR: Failed to insert data into Milvus: {e}")
    exit()

print(f"Data upload to '{TARGET_COLLECTION_NAME}' complete.")
print(f"Total entities in collection: {collection.num_entities}")

# Optional: You can add a small query here to verify, e.g.:
# results = collection.query(expr="event_id > 0", limit=2, output_fields=["event_id", "event_name"])
# print("\nSample of inserted data:")
# for res in results:
#     print(res)
