"""
Minimal Flask backend for candidate search
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from search import execute_search
from ranking import rank_candidates
from ranking_gemini import rank_candidates_gemini
from highlights import generate_highlights
from save_search import save_search_session, get_search_session
from add_note import update_candidate_note, get_candidate_note

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

@app.route('/search', methods=['POST'])
def search():
    """Search candidates - returns raw results"""
    data = request.json
    query = data.get('query', '').strip()
    print(f"[DEBUG] Search request received for query: {query}")

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
    """Rank candidates - two-stage pipeline (GPT-5-nano classification → Gemini ranking)"""
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

@app.route('/rank-gemini', methods=['POST'])
def rank_gemini():
    """Rank candidates with Gemini - handles ALL candidates with large context window"""
    data = request.json
    query = data.get('query', '').strip()
    candidates = data.get('candidates', [])

    if not query or not candidates:
        return jsonify({'error': 'Query and candidates required'}), 400

    try:
        print(f"[DEBUG] Gemini ranking {len(candidates)} candidates")
        ranked = rank_candidates_gemini(query, candidates)
        print(f"[DEBUG] Gemini ranked {len(ranked)} candidates")
        return jsonify({
            'success': True,
            'ranked_candidates': ranked,
            'total': len(ranked)
        })
    except Exception as e:
        print(f"[ERROR] Gemini ranking failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/search-and-rank', methods=['POST'])
def search_and_rank():
    """Combined endpoint - search then rank with two-stage pipeline (GPT-5-nano + Gemini)"""
    data = request.json
    query = data.get('query', '').strip()
    connected_to = data.get('connected_to', 'all')

    if not query:
        return jsonify({'error': 'Query required'}), 400

    try:
        print(f"[DEBUG] Starting search for query: {query}")

        # Search with connection filter
        search_result = execute_search(query, connected_to)
        print(f"[DEBUG] Search completed. Found {len(search_result['results'])} results")

        # Rank with two-stage pipeline (GPT-5-nano classification + Gemini ranking)
        print(f"[DEBUG] Starting two-stage ranking pipeline...")
        ranked = rank_candidates(query, search_result['results'])
        print(f"[DEBUG] Two-stage ranking completed. Ranked {len(ranked)} candidates")

        # Save search session
        search_id = save_search_session(query, connected_to, search_result['sql'], ranked)
        print(f"[DEBUG] Saved search session with ID: {search_id}")

        return jsonify({
            'success': True,
            'id': search_id,
            'sql': search_result['sql'],
            'results': ranked,
            'total': len(ranked)
        })
    except Exception as e:
        print(f"[ERROR] Exception occurred: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/search/<search_id>', methods=['GET'])
def get_search(search_id):
    """Retrieve saved search by UUID"""
    try:
        result = get_search_session(search_id)

        if not result:
            return jsonify({'error': 'Search not found'}), 404

        return jsonify({
            'success': True,
            **result
        })
    except Exception as e:
        print(f"[ERROR] Exception occurred: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/generate-highlights', methods=['POST'])
def generate_highlights_endpoint():
    """Generate detailed highlights with sources for a candidate"""
    data = request.json
    candidate = data.get('candidate')

    if not candidate:
        return jsonify({'error': 'Candidate data required'}), 400

    try:
        print(f"[DEBUG] Generating highlights for: {candidate.get('name')}")
        result = generate_highlights(candidate)
        print(f"[DEBUG] Generated {len(result['highlights'])} highlights from {result['total_sources']} sources")

        return jsonify({
            'success': True,
            'highlights': result['highlights'],
            'total_sources': result['total_sources']
        })
    except Exception as e:
        print(f"[ERROR] Highlights generation failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/notes/<path:linkedin_url>', methods=['GET'])
def get_note(linkedin_url):
    """Get note for a candidate"""
    try:
        note = get_candidate_note(linkedin_url)
        return jsonify({
            'success': True,
            'linkedin_url': linkedin_url,
            'note': note
        })
    except Exception as e:
        print(f"[ERROR] Failed to get note: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/notes', methods=['POST'])
def add_note():
    """Add or update note for a candidate"""
    data = request.json
    linkedin_url = data.get('linkedin_url', '').strip()
    note = data.get('note', '').strip()

    if not linkedin_url:
        return jsonify({'error': 'LinkedIn URL required'}), 400

    try:
        success = update_candidate_note(linkedin_url, note)

        if success:
            return jsonify({
                'success': True,
                'message': 'Note updated successfully',
                'linkedin_url': linkedin_url,
                'note': note
            })
        else:
            return jsonify({'error': 'Candidate not found'}), 404

    except Exception as e:
        print(f"[ERROR] Failed to update note: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
