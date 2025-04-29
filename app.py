from flask import Flask, request, jsonify, render_template_string
import pandas as pd
import os
import openai
from pandasai import SmartDataframe
from pandasai.llm.openai import OpenAI as PandasOpenAI

from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

app = Flask(__name__)

# ✅ Load OpenAI API Key securely (note: use os.getenv in production)
API_KEY = "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"

if not API_KEY:
    raise ValueError("❌ OpenAI API key is missing!")

openai.api_key = API_KEY

# ✅ Dataset path
folder_path = "C:\\Users\\azureadmin\\Desktop\\data"

# ✅ Load datasets
def load_datasets():
    try:
        global df, smart_df
        all_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith((".csv", ".xlsx"))]
        if not all_files:
            print("❌ No datasets found.")
            return None

        df_list = []
        for f in all_files:
            if f.endswith(".csv"):
                df_list.append(pd.read_csv(f, encoding="ISO-8859-1"))
            elif f.endswith(".xlsx"):
                df_list.append(pd.read_excel(f, engine="openpyxl"))

        df = pd.concat(df_list, ignore_index=True)

        llm = PandasOpenAI(api_token=API_KEY)
        smart_df = SmartDataframe(df, config={
            "llm": llm,
            "enable_cache": False,
            "enable_plotting": True,
            "enforce_privacy": True,
            "safe_code_execution": False
        })

        print(f"✅ Loaded {len(all_files)} dataset(s).")
        return smart_df

    except Exception as e:
        print(f"❌ Dataset loading error: {e}")
        return None

smart_df = load_datasets()

# ✅ Frontend HTML
HTML_CONTENT = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Eureka AI Assistant</title>
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: #0a1f44;
      font-family: 'Poppins', sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      color: #333;
    }
    .chat-container {
      background: #fff;
      border-radius: 20px;
      width: 90%;
      max-width: 900px;
      display: flex;
      flex-direction: column;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
      overflow: hidden;
    }
    .chat-header {
      background: linear-gradient(90deg, #0a1f44 0%, #1e3a8a 100%);
      color: white;
      padding: 25px;
      font-size: 22px;
      font-weight: 600;
      text-align: center;
    }
    #chatbox {
      flex: 1;
      padding: 20px;
      overflow-y: auto;
      background: #f8fafc;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .message {
      max-width: 75%;
      padding: 14px 18px;
      border-radius: 20px;
      line-height: 1.6;
      animation: fadeInUp 0.3s ease forwards;
    }
    .user {
      background: #1e3a8a;
      color: white;
      align-self: flex-end;
      border-bottom-right-radius: 6px;
    }
    .bot {
      background: #e2e8f0;
      color: #0a1f44;
      align-self: flex-start;
      border-bottom-left-radius: 6px;
    }
    .chat-input-section {
      display: flex;
      padding: 20px;
      border-top: 1px solid #e2e8f0;
      background: white;
    }
    .chat-input-section input {
      flex: 1;
      padding: 15px;
      border: 1px solid #cbd5e1;
      border-radius: 12px;
      font-size: 15px;
    }
    .chat-input-section button {
      background: #1e3a8a;
      color: white;
      border: none;
      padding: 15px 20px;
      border-radius: 12px;
      margin-left: 10px;
      cursor: pointer;
    }
    @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(15px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .typing {
      align-self: flex-start;
      display: flex;
      gap: 5px;
      padding: 14px 18px;
    }
    .dot {
      width: 8px;
      height: 8px;
      background: #0a1f44;
      border-radius: 50%;
      animation: blink 1.4s infinite both;
    }
    .dot:nth-child(2) { animation-delay: 0.2s; }
    .dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes blink {
      0%, 80%, 100% { transform: scale(0); }
      40% { transform: scale(1); }
    }
  </style>
</head>
<body>
<div class="chat-container">
  <div class="chat-header">Eureka AI Assistant</div>
  <div id="chatbox"></div>
  <div class="chat-input-section">
    <input type="text" id="userInput" placeholder="Ask your question..." onkeypress="handleKeyPress(event)">
    <button onclick="sendMessage()">Send</button>
  </div>
</div>
<script>
  function appendMessage(text, sender) {
    const chatbox = document.getElementById("chatbox");
    const message = document.createElement("div");
    message.classList.add("message", sender);
    message.innerHTML = text;
    chatbox.appendChild(message);
    chatbox.scrollTop = chatbox.scrollHeight;
  }

  function showTyping() {
    const chatbox = document.getElementById("chatbox");
    const typing = document.createElement("div");
    typing.classList.add("typing");
    typing.id = "typing-indicator";
    typing.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
    chatbox.appendChild(typing);
    chatbox.scrollTop = chatbox.scrollHeight;
  }

  function removeTyping() {
    const typing = document.getElementById("typing-indicator");
    if (typing) typing.remove();
  }

  function sendMessage() {
    const userInput = document.getElementById("userInput");
    const query = userInput.value.trim();
    if (!query) return;
    appendMessage(query, "user");
    userInput.value = "";
    showTyping();
    fetch("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query })
    })
    .then(response => response.json())
    .then(data => {
      removeTyping();
      appendMessage(data.response || data.insights || "No response.", "bot");
    })
    .catch(error => {
      removeTyping();
      appendMessage("❌ Error: " + error, "bot");
    });
  }

  function handleKeyPress(event) {
    if (event.key === "Enter") sendMessage();
  }
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_CONTENT)

@app.route('/query', methods=['POST'])
def process_query():
    data = request.json
    user_query = data.get("query", "").strip()

    if not user_query:
        return jsonify({"response": "❌ Please enter a query."}), 400

    try:
        prompt = f"""
        You are an AI assistant analyzing a user's query.

        User Query: "{user_query}"

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
            return jsonify({"response": f"<ul><li>{formatted_query}</li></ul>"})

        pandasai_result = smart_df.chat(formatted_query)

        summary_prompt = f"""
        You are an AI assistant reviewing dataset results.

        User Query: {user_query}
        Extracted Data from PandasAI: {pandasai_result}

        Provide key insights, trends, and recommended actions based on the data in HTML bullet points format using <ul><li>...</li></ul>. Only return HTML.
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



# ✅ Start server with Waitress
if __name__ == "__main__":
    app, host="0.0.0.0", port=5000
