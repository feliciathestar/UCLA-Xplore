from pymilvus import connections
from pymilvus import (FieldSchema, DataType, CollectionSchema, Collection)
import numpy as np
import pandas as pd

ENDPOINT = "https://in03-360d7a6acbd9660.serverless.gcp-us-west1.cloud.zilliz.com"
TOKEN = "0655b3db6ad52e4419627358025db8c966d6de3929cf4894e14fcc54cc5d16252ec0ce468937a2f478cb9c09a5932dfdee73e180"
connections.connect(uri=ENDPOINT, token=TOKEN)

# Define Schema
fields = [
    FieldSchema(name="event_id", dtype=DataType.INT64, is_primary=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),  # OpenAI embedding size
    FieldSchema(name="event_name", dtype=DataType.VARCHAR, max_length=512),
    FieldSchema(name="event_tags", dtype=DataType.VARCHAR, max_length=512),
    FieldSchema(name="event_programe", dtype=DataType.VARCHAR, max_length=512),
    FieldSchema(name="event_location", dtype=DataType.VARCHAR, max_length=512),
    FieldSchema(name="event_description", dtype=DataType.VARCHAR, max_length=4096),
]
schema = CollectionSchema(fields, description="UCLA Club Events Database")

# Create collection.
collection_name = "ucla_club_events"
collection = Collection(name=collection_name, schema=schema)

# Index the collection.
index_params = {"metric_type": "L2", "index_type": "IVF_FLAT", "params": {"nlist": 100}}
collection.create_index(field_name="embedding", index_params=index_params)
print(f"Collection '{collection_name}' created successfully.")

# Insert test data
## 1. Input data can be pandas dataframe or list of dicts.
data_rows = []
data_rows.extend([
   {"vector": np.random.randn(768).tolist(),
    "text": "This is a document",
    "source": "source_url_1"},
   {"vector": np.random.randn(768).tolist(),
    "text": "This is another document",
    "source": "source_url_2"},
])

#Insert data into milvus.
embedding_df = pd.read_csv("processed_embeddings.csv")
data_to_insert = [
    embedding_df["event_id"].tolist(),
    embedding_df["embedding"].apply(lambda x: eval(x)).tolist(),  # Convert string to list
    embedding_df["event_name"].fillna("").tolist(),
    embedding_df["event_tags"].fillna("").tolist(),
    embedding_df["event_programe"].fillna("").tolist(),
    embedding_df["event_location"].fillna("").tolist(),
    embedding_df["event_description"].fillna("").tolist(),
]

collection.insert(data_to_insert)
collection.load()
print(f"Data inserted into '{collection_name}' and collection is loaded.")
