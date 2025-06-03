from pymilvus import connections, list_collections, Collection
import os

# Replace these with your Zilliz credentials
ZILLIZ_URI = os.getenv("ZILLIZ_URI", "https://your-cluster.zillizcloud.com")
ZILLIZ_TOKEN = os.getenv("ZILLIZ_TOKEN", "your-zilliz-api-key")

def connect_to_zilliz():
    print("Connecting to Zilliz...")
    connections.connect(
        alias="default",
        uri=ZILLIZ_URI,
        token=ZILLIZ_TOKEN
    )
    print("✅ Connected")

def inspect_collections():
    collections = list_collections()
    if not collections:
        print("No collections found.")
        return

    for name in collections:
        print(f"\n📦 Collection: {name}")
        collection = Collection(name)
        
        print("📄 Schema:")
        for field in collection.schema.fields:
            print(f"  - {field.name} ({field.dtype})")

        print(f"🔢 Total entries: {collection.num_entities}")

        print("🔍 Fetching sample entries...")
        try:
            collection.load()
            sample = collection.query(
                expr="",
                output_fields=[f.name for f in collection.schema.fields],
                limit=5
            )
            for entry in sample:
                print("  ➤", entry)
        except Exception as e:
            print(f"⚠️ Could not query collection: {e}")

if __name__ == "__main__":
    connect_to_zilliz()
    inspect_collections()
