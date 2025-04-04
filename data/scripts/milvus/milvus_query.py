from pymilvus import connections, Collection
import openai

ENDPOINT = "https://in03-360d7a6acbd9660.serverless.gcp-us-west1.cloud.zilliz.com"
TOKEN = "0655b3db6ad52e4419627358025db8c966d6de3929cf4894e14fcc54cc5d16252ec0ce468937a2f478cb9c09a5932dfdee73e180"
COLLECTION_NAME = "ucla_club_events"

openai.api_key = "api-key-here" # Replace with your key
embedding_model = "text-embedding-ada-002"

# Connect to Milvus
connections.connect(uri=ENDPOINT, token=TOKEN)
collection = Collection(COLLECTION_NAME)
collection.load()

# Function to get embeddings from OpenAI
def get_openai_embedding(text):
    response = openai.embeddings.create(
        model=embedding_model,
        input=[text]
    )
    return response.data[0].embedding

# Query by event_id
def get_event_by_id(event_id):
    expr = f"event_id == {event_id}"
    results = collection.query(
        expr,
        output_fields=["event_name", "event_tags", "event_programe", "event_location", "event_description"]
    )
    return results

# Search using semantic similarity
def search_events(query_text, top_k=5):
    query_embedding = get_openai_embedding(query_text)
    
    search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
    results = collection.search(
        data=[query_embedding],
        anns_field="embedding",
        param=search_params,
        limit=top_k,
        output_fields=["event_id", "event_name", "event_tags", "event_programe", "event_location", "event_description"]
    )
    
    return results

# Example usage
event_id = 2
print("Searching by Event ID:")
print(get_event_by_id(event_id))

query = "Networking event for graduate students"
print("\nSemantic Search Results:")
print(search_events(query))