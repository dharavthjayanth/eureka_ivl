from flask import Flask, request, jsonify, render_template_string
import pandas as pd
import os
import openai
from pandasai import SmartDataframe
from pandasai.llm.openai import OpenAI as PandasOpenAI
import threading
from azure.storage.blob import BlobServiceClient
import tempfile

app = Flask(__name__)

# ✅ Set OpenAI API Key
API_KEY = os.getenv("API_KEY")
openai.api_key = API_KEY

# ✅ Azure Blob Configuration
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
BLOB_CONTAINER_NAME = "salespkg"
blob_name = "sales_PKG.clsx" 

# ✅ Load Datasets from Azure Blob
def load_datasets_from_blob():
    try:
        global df, smart_df
        print("🔄 Connecting to Azure Blob Storage...")

        blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)

        blobs = container_client.list_blobs()
        dfs = []

        for blob in blobs:
            if not (blob.name.endswith(".csv") or blob.name.endswith(".xlsx")):
                continue

            blob_client = container_client.get_blob_client(blob.name)
            print(f"📥 Downloading blob: {blob.name}")

            # Use temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv" if blob.name.endswith(".csv") else ".xlsx") as temp_file:
                temp_file.write(blob_client.download_blob().readall())
                temp_path = temp_file.name

            # Load into DataFrame
            if temp_path.endswith(".csv"):
                dfs.append(pd.read_csv(temp_path, encoding="ISO-8859-1"))
            elif temp_path.endswith(".xlsx"):
                dfs.append(pd.read_excel(temp_path, engine="openpyxl"))

            os.remove(temp_path)

        df = pd.concat(dfs, ignore_index=True)

        # ✅ Wrap with SmartDataframe
        llm = PandasOpenAI(api_token=API_KEY)
        smart_df = SmartDataframe(df, config={
            "llm": llm,
            "enable_cache": False,
            "enable_plotting": True,
            "enforce_privacy": True
        })

        print(f"✅ Loaded {len(dfs)} datasets from Azure Blob successfully!")
        return smart_df

    except Exception as e:
        print(f"❌ Error loading datasets from blob: {e}")
        return None

# ✅ Initialize SmartDataframe
smart_df = load_datasets_from_blob()

# ✅ Frontend Route
@app.route('/')
def index():
    return render_template_string(open("templates/index.html").read())

# ✅ Query Processing Route
@app.route('/query', methods=['POST'])
def process_query():
    data = request.json
    user_query = data.get("query", "").strip()

    if not user_query:
        return jsonify({"response": "❌ Please enter a query."}), 400

    try:
        # Step 1: Interpret query with GPT-4
        prompt = f"""
        You are an AI assistant analyzing a user's query.

        **User Query:** "{user_query}"

        - Determine whether the query requires dataset calculations.
        - If dataset calculations are needed, structure the query for PandasAI.
        """

        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=200
        )

        formatted_query = response["choices"][0]["message"]["content"].strip()

        if "no dataset calculations are required" in formatted_query.lower():
            return jsonify({"response": formatted_query})

        # Step 2: PandasAI execution
        pandasai_result = smart_df.chat(formatted_query)

        # Step 3: Summarize the result
        summary_prompt = f"""
        You are an AI assistant reviewing dataset results.

        **User Query:** {user_query}
        **Extracted Data from PandasAI:** {pandasai_result}

        Provide key insights, trends, and recommended actions based on the data.
        """

        summary_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.5,
            max_tokens=500
        )

        insights = summary_response["choices"][0]["message"]["content"]

        return jsonify({
            "query": user_query,
            "formatted_query": formatted_query,
            "pandasai_result": str(pandasai_result),
            "insights": insights
        })

    except Exception as e:
        return jsonify({"response": f"❌ Error processing query: {e}"}), 500

# ✅ Run Flask App
def run_flask_app():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()