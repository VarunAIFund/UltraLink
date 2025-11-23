"""
Backend Configuration Constants

Centralized configuration for all backend services including:
- Database query limits
- AI model parameters
- Ranking pipeline settings
- API rate limits
- Cost tracking
"""

# ============================================================================
# DATABASE QUERY LIMITS
# ============================================================================

# Maximum number of candidates to return from SQL queries
SQL_QUERY_LIMIT = 500

# Maximum number of candidates to fetch for ranking
MAX_CANDIDATES_TO_RANK = 500

# Batch size for database upsert operations
DB_BATCH_SIZE = 100


# ============================================================================
# AI MODEL IDENTIFIERS
# ============================================================================

# SQL Generation (search.py)
SQL_GENERATION_MODEL = "gpt-4o"

# Ranking Stage 1 - Classification (ranking_stage_1_nano.py)
RANKING_STAGE_1_MODEL = "gpt-5-nano"

# Ranking Stage 2 - Gemini ranking (ranking_stage_2_gemini.py)
RANKING_STAGE_2_MODEL = "gemini-2.5-pro"


# ============================================================================
# RANKING STAGE 1 - CONNECTION POOL SETTINGS
# ============================================================================

# Maximum concurrent HTTP connections for httpx client
RANKING_STAGE_1_MAX_CONNECTIONS = 500

# Maximum keepalive connections in the pool
RANKING_STAGE_1_MAX_KEEPALIVE_CONNECTIONS = 100