from flask import Flask, request, jsonify, render_template
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.knowledge_graph.knowledgeGraph import KnowledgeGraph
from core.orchestrator.index import orchestrate

app = Flask(__name__)

# Load knowledge graph once at startup
kg = KnowledgeGraph()
kg.load_from_json("output/knowledge_graph.json")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def process_query():
    data = request.json
    query = data.get('query')
    openai_key = data.get('openai_key') or os.environ.get('OPENAI_API_KEY')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    if not openai_key:
        return jsonify({"error": "OpenAI API key required"}), 400
    
    result = orchestrate(
        query=query,
        knowledge_graph=kg,
        openai_key=openai_key,
        run_validation=True,
        alignment_profile=data.get("alignment_profile"),
    )
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)