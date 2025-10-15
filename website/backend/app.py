"""
Minimal Flask backend for candidate search
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from search import execute_search
from ranking import rank_candidates

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

@app.route('/search', methods=['POST'])
def search():
    """Search candidates - returns raw results"""
    data = request.json
    query = data.get('query', '').strip()

    if not query:
        return jsonify({'error': 'Query required'}), 400

    try:
        result = execute_search(query)
        return jsonify({
            'success': True,
            'sql': result['sql'],
            'results': result['results'],
            'total': result['total']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/rank', methods=['POST'])
def rank():
    """Rank candidates - takes search results, returns ranked with AI insights"""
    data = request.json
    query = data.get('query', '').strip()
    candidates = data.get('candidates', [])

    if not query or not candidates:
        return jsonify({'error': 'Query and candidates required'}), 400

    try:
        ranked = rank_candidates(query, candidates)
        return jsonify({
            'success': True,
            'ranked_candidates': ranked,
            'total': len(ranked)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search-and-rank', methods=['POST'])
def search_and_rank():
    """Combined endpoint - search then rank"""
    data = request.json
    query = data.get('query', '').strip()
    connected_to = data.get('connected_to', 'all')

    if not query:
        return jsonify({'error': 'Query required'}), 400

    try:
        # Search with connection filter
        search_result = execute_search(query, connected_to)

        # Rank
        ranked = rank_candidates(query, search_result['results'])

        return jsonify({
            'success': True,
            'sql': search_result['sql'],
            'results': ranked,
            'total': len(ranked)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
