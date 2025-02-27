from pymilvus import connections
from pymilvus import (FieldSchema, DataType, CollectionSchema, Collection)
import numpy as np

ENDPOINT = "https://in03-360d7a6acbd9660.serverless.gcp-us-west1.cloud.zilliz.com"
TOKEN = "0655b3db6ad52e4419627358025db8c966d6de3929cf4894e14fcc54cc5d16252ec0ce468937a2f478cb9c09a5932dfdee73e180"
connections.connect(uri=ENDPOINT, token=TOKEN)

# Creating a test collection
## 1. Define a minimum expandable schema.
fields = [
   FieldSchema("pk", DataType.INT64, is_primary=True, auto_id=True),
   FieldSchema("vector", DataType.FLOAT_VECTOR, dim=768),
]
schema = CollectionSchema(
   fields,
   enable_dynamic_field=True,
)

## 2. Create a collection.
mc = Collection("my_collection_name", schema)

## 3. Index the collection.
mc.create_index(field_name="vector",
   index_params={
       "Index_type": "AUTOINDEX",
       "Metric_type": "COSINE",
    }
)

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

## 2. Insert data into milvus.
mc.insert(data_rows)
mc.flush()