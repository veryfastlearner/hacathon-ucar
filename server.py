from flask import Flask, request, jsonify
from flask_cors import CORS
from agents import run_pipeline
import os

app = Flask(__name__)
CORS(app) # Allow React to talk to this API

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    question = data.get('question')
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
        
    try:
        print(f"\n🌐 [API Request] Processing: {question}")
        response = run_pipeline(question)
        return jsonify({"answer": response})
    except Exception as e:
        print(f"❌ [API Error] {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 UCAR API Server starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
