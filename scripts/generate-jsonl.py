import os
import pandas as pd
import json
from azure.storage.blob import ContainerClient
from dotenv import load_dotenv
import io

load_dotenv()

# Load from .env
CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("AZURE_BLOB_CONTAINER_NAME")
SUBFOLDERS = ["CPET/", "PACKAGING/"]

container_client = ContainerClient.from_connection_string(
    conn_str=CONNECTION_STRING,
    container_name=CONTAINER_NAME
)

samples = []

for folder in SUBFOLDERS:
    for blob in container_client.list_blobs(name_starts_with=folder):
        if blob.name.endswith(".xlsx"):
            data = container_client.download_blob(blob).readall()
            df = pd.read_excel(io.BytesIO(data)).dropna(how="all")

            df_sample = df.head(3)
            context = "\n".join(
                [", ".join(f"{col}: {val}" for col, val in row.items()) for _, row in df_sample.iterrows()]
            )

            prompt = f"Given the following data from file '{blob.name}':\n{context}\nWhat are the top 3 columns present?"
            response = f"The top 3 columns are: {', '.join(df.columns[:3])}."
            samples.append({"prompt": prompt, "response": response})

# Save to .jsonl
with open("train.jsonl", "w") as f:
    for s in samples:
        f.write(json.dumps(s) + "\n")

print("✅ train.jsonl created with", len(samples), "samples.")
