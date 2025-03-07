import openai
import pandas as pd
import numpy as np

# Load the dataset
file_path = "../../raw/events_calendar/w07_processed.xlsx"
df = pd.read_excel(file_path)

# Select relevant columns
df_filtered = df[['event_id', 'event_description', 'event_name', 'event_tags', 'event_programe', 'event_location']].copy()

# Drop rows where event_description is missing
df_filtered = df_filtered.dropna(subset=['event_description'])

# OpenAI Embedding API Setup
openai.api_key = "api-key-here" # Replace with your key
embedding_model = "text-embedding-ada-002"

# Function to chunk text into smaller segments
def chunk_text(text, max_tokens=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_tokens):
        chunks.append(" ".join(words[i:i+max_tokens]))
    return chunks

# Function to get embeddings from OpenAI
def get_openai_embedding(text):
    response = openai.embeddings.create(
        model=embedding_model,
        input=[text]
    )
    return response.data[0].embedding

# Process each row: chunk & embed
embedding_data = []
for _, row in df_filtered.iterrows():
    event_id = row["event_id"]

    # Create a unified text representation including all fields
    text_to_embed = f"{row['event_name']}. Tags: {row['event_tags']}. Program: {row['event_programe']}. Location: {row['event_location']}. Description: {row['event_description']}"

    # Chunk and embed
    chunks = chunk_text(text_to_embed)
    chunk_embeddings = [get_openai_embedding(chunk) for chunk in chunks]
    
    # Store in list
    for emb in chunk_embeddings:
        embedding_data.append({
            "event_id": event_id,
            "embedding": emb,
            "event_name": row["event_name"],
            "event_tags": row["event_tags"],
            "event_programe": row["event_programe"],
            "event_location": row["event_location"],
            "event_description": row["event_description"]
        })

# Convert to DataFrame
embedding_df = pd.DataFrame(embedding_data)
embedding_df.to_csv("processed_embeddings.csv", index=False)

print("✅ Embeddings saved to processed_embeddings.csv")
