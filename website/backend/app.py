"""
Minimal Flask backend for candidate search
"""
import io
import sys
import time
import json
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from search import execute_search
from ranking import rank_candidates
from ranking_gemini import rank_candidates_gemini
from highlights import generate_highlights
from save_search import save_search_session, get_search_session
from add_note import update_candidate_note, get_candidate_note

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

def format_sse(data: dict) -> str:
    """Format data as Server-Sent Event message"""
    return f"data: {json.dumps(data)}\n\n"

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

    # Capture stdout to save as logs
    log_buffer = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = log_buffer

    # Start timer for execution time tracking
    start_time = time.time()

    try:
        print(f"[DEBUG] Starting search for query: {query}")

        # Search with connection filter
        search_result = execute_search(query, connected_to)
        search_cost = search_result.get('cost', {})
        print(f"[DEBUG] Search completed. Found {len(search_result['results'])} results")

        # Rank with two-stage pipeline (GPT-5-nano classification + Gemini ranking)
        print(f"[DEBUG] Starting two-stage ranking pipeline...")
        ranked, ranking_cost = rank_candidates(query, search_result['results'])
        print(f"[DEBUG] Two-stage ranking completed. Ranked {len(ranked)} candidates")

        # Calculate total cost
        sql_cost = search_cost.get('total_cost', 0.0)
        stage_1_cost = ranking_cost.get('stage_1', {}).get('total_cost', 0.0)
        stage_2_cost = ranking_cost.get('stage_2', {}).get('total_cost', 0.0)
        total_cost = sql_cost + stage_1_cost + stage_2_cost

        # Print cost breakdown
        print(f"\n{'='*60}")
        print(f"💰 TOTAL SEARCH COST")
        print(f"{'='*60}")
        print(f"   • SQL Generation (GPT-4o): ${sql_cost:.4f}")
        print(f"   • Classification (GPT-5-nano): ${stage_1_cost:.4f}")
        print(f"   • Ranking (Gemini 2.5 Pro): ${stage_2_cost:.4f}")
        print(f"   • TOTAL: ${total_cost:.4f}")
        print(f"{'='*60}\n")

        # Calculate total execution time
        elapsed_time = time.time() - start_time

        # Get captured logs
        logs = log_buffer.getvalue()

        # Restore stdout
        sys.stdout = original_stdout

        # Also print logs to actual stdout for real-time monitoring
        print(logs, end='')

        # Save search session with logs and execution time
        search_id = save_search_session(query, connected_to, search_result['sql'], ranked, total_cost, logs, elapsed_time, ranking=True)
        print(f"[DEBUG] Saved search session with ID: {search_id}")
        print(f"[DEBUG] Total execution time: {elapsed_time:.2f} seconds")

        return jsonify({
            'success': True,
            'id': search_id,
            'sql': search_result['sql'],
            'results': ranked,
            'total': len(ranked),
            'total_cost': total_cost,
            'total_time': elapsed_time,
            'logs': logs
        })
    except Exception as e:
        # Capture error in logs
        print(f"[ERROR] Exception occurred: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

        # Get captured logs (including error)
        logs = log_buffer.getvalue()

        # Restore stdout
        sys.stdout = original_stdout

        # Print error to actual stdout
        print(logs, end='')

        return jsonify({'error': str(e)}), 500

@app.route('/search-and-rank-stream', methods=['POST'])
def search_and_rank_stream():
    """Combined endpoint with Server-Sent Events for real-time progress"""
    data = request.json
    query = data.get('query', '').strip()
    connected_to = data.get('connected_to', 'all')
    ranking = data.get('ranking', True)  # Default to True for backward compatibility

    if not query:
        return jsonify({'error': 'Query required'}), 400

    def generate():
        # Capture stdout to save as logs
        log_buffer = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = log_buffer

        # Start timer for execution time tracking
        start_time = time.time()

        try:
            # Step 1: Generate SQL query
            yield format_sse({'step': 'generating_query', 'message': 'Generating search query...'})

            search_result = execute_search(query, connected_to)
            search_cost = search_result.get('cost', {})

            # Step 2: Searching database
            yield format_sse({'step': 'searching', 'message': 'Searching database...'})

            # Step 3: Always run Stage 1 (GPT-5-nano classification)
            yield format_sse({'step': 'classifying', 'message': 'Analyzing candidates...'})

            # Import stage functions directly for real-time progress
            from ranking_stage_1_nano import classify_all_candidates
            from ranking_stage_2_gemini import rank_all_candidates
            import asyncio

            stage_1_results = asyncio.run(classify_all_candidates(query, search_result['results']))
            stage_1_cost = stage_1_results.get('cost', {})

            # Calculate SQL + Stage 1 costs
            sql_cost = search_cost.get('total_cost', 0.0)
            stage_1_total = stage_1_cost.get('total_cost', 0.0)

            # Conditionally run Stage 2 (Gemini ranking) based on ranking flag
            if ranking:
                # Step 4: Ranking matches (Stage 2 - Gemini ranking)
                yield format_sse({'step': 'ranking', 'message': 'Ranking matches...'})

                ranked, stage_2_cost = rank_all_candidates(query, stage_1_results)
                stage_2_total = stage_2_cost.get('total_cost', 0.0)
                total_cost = sql_cost + stage_1_total + stage_2_total

                # Print cost breakdown
                print(f"\n{'='*60}")
                print(f"💰 TOTAL SEARCH COST")
                print(f"{'='*60}")
                print(f"   • SQL Generation (GPT-4o): ${sql_cost:.4f}")
                print(f"   • Classification (GPT-5-nano): ${stage_1_total:.4f}")
                print(f"   • Ranking (Gemini 2.5 Pro): ${stage_2_total:.4f}")
                print(f"   • TOTAL: ${total_cost:.4f}")
                print(f"{'='*60}\n")
            else:
                # Stage 2 disabled - return Stage 1 classified results without Gemini ranking
                print(f"\n[DEBUG] Stage 2 ranking disabled - returning classified results without Gemini ranking")

                # Combine results from Stage 1 without Gemini ranking
                stage_1_candidates = (
                    stage_1_results.get('strong_matches', []) +
                    stage_1_results.get('partial_matches', []) +
                    stage_1_results.get('no_matches', [])
                )

                # Flatten Stage 1 format to match Stage 2 format
                # Stage 1 has: {candidate: {...}, analysis: "...", match_type: "..."}
                # Stage 2 expects: {name: "...", match: "...", fit_description: "...", ...}
                ranked = []
                for item in stage_1_candidates:
                    # Extract the nested candidate object
                    candidate = item.get('candidate', {})

                    # Add Stage 1 classification fields to candidate
                    confidence = item.get('confidence', 0)
                    candidate['match'] = item.get('match_type', 'no_match')  # match_type -> match
                    candidate['fit_description'] = item.get('analysis', '')  # analysis -> fit_description
                    candidate['relevance_score'] = None  # No Gemini ranking
                    candidate['stage_1_confidence'] = confidence
                    candidate['score'] = confidence  # Use Stage 1 confidence as sortable score

                    ranked.append(candidate)

                total_cost = sql_cost + stage_1_total

                print(f"\n{'='*60}")
                print(f"💰 TOTAL SEARCH COST (No Stage 2 Ranking)")
                print(f"{'='*60}")
                print(f"   • SQL Generation (GPT-4o): ${sql_cost:.4f}")
                print(f"   • Classification (GPT-5-nano): ${stage_1_total:.4f}")
                print(f"   • TOTAL: ${total_cost:.4f}")
                print(f"{'='*60}\n")

            # Calculate execution time
            elapsed_time = time.time() - start_time

            # Get captured logs
            logs = log_buffer.getvalue()

            # Restore stdout
            sys.stdout = original_stdout

            # Print logs to actual stdout
            print(logs, end='')

            # Save search session
            search_id = save_search_session(query, connected_to, search_result['sql'], ranked, total_cost, logs, elapsed_time, ranking)
            print(f"[DEBUG] Saved search session with ID: {search_id}")

            # Step 5: Complete - send final results
            yield format_sse({
                'step': 'complete',
                'message': 'Complete',
                'data': {
                    'success': True,
                    'id': search_id,
                    'sql': search_result['sql'],
                    'results': ranked,
                    'total': len(ranked),
                    'total_cost': total_cost,
                    'total_time': elapsed_time,
                    'logs': logs
                }
            })

        except Exception as e:
            # Capture error in logs
            print(f"[ERROR] Exception occurred: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()

            logs = log_buffer.getvalue()
            sys.stdout = original_stdout
            print(logs, end='')

            # Send error event
            yield format_sse({
                'step': 'error',
                'message': str(e)
            })

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/search/<search_id>', methods=['GET'])
def get_search(search_id):
    """Retrieve saved search by UUID"""
    try:
        result = get_search_session(search_id)

        if not result:
            return jsonify({'error': 'Search not found'}), 404

        # Add profile_pic URLs to saved results (for backward compatibility)
        from utils import add_profile_pic_urls
        if 'results' in result and result['results']:
            result['results'] = add_profile_pic_urls(result['results'])
            print(f"[DEBUG] Added profile_pic URLs to {len(result['results'])} saved candidates")

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
