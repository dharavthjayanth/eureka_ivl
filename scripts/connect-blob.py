import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.ml import MLClient
from azure.ai.ml.entities import AzureBlobDatastore, Data
from azure.ai.ml.constants import AssetTypes

load_dotenv()

subscription_id         = os.getenv("AZURE_SUBSCRIPTION_ID")
resource_group          = os.getenv("AZURE_RESOURCE_GROUP")
workspace_name          = os.getenv("AZURE_WORKSPACE_NAME")
storage_account_name    = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
container_name          = os.getenv("AZURE_BLOB_CONTAINER_NAME")
datastore_name          = os.getenv("AZURE_DATASTORE_NAME")
data_asset_name         = os.getenv("AZURE_DATA_ASSET_NAME")

print("🔌 Connecting to Azure ML workspace...")
ml_client = MLClient(
    DefaultAzureCredential(),
    subscription_id=subscription_id,
    resource_group_name=resource_group,
    workspace_name=workspace_name
)
print(f"✅ Connected to workspace: {workspace_name}")

# Register the Blob container as a datastore
print(f"📦 Registering Blob container '{container_name}' as datastore '{datastore_name}'...")
datastore = AzureBlobDatastore(
    name=datastore_name,
    account_name=storage_account_name,
    container_name=container_name
)
ml_client.datastores.create_or_update(datastore)
print(f"✅ Datastore '{datastore_name}' registered successfully.")

# Register dataset asset pointing to the whole container
print("📁 Registering dataset from blob storage...")
data_asset = Data(
    path=f"azureml://datastores/{datastore_name}/paths/",
    type=AssetTypes.URI_FOLDER,
    name=data_asset_name,
    description="Prototype GenAI dataset for LLM fine-tuning (RBAC scoped)",
)

ml_client.data.create_or_update(data_asset)
print(f"✅ Dataset asset '{data_asset_name}' registered.")
