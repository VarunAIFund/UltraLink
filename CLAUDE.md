# CLAUDE.md - UltraLink

Comprehensive guidance for Claude Code when working with the UltraLink LinkedIn data processing and search platform.

## Table of Contents

- [Overview](#overview)
- [Directory Structure](#directory-structure)
- [Quick Start Commands](#quick-start-commands)
- [Complete Pipeline Flow](#complete-pipeline-flow)
- [Component Details](#component-details)
- [Database Architecture](#database-architecture)
- [API Integrations](#api-integrations)
- [Environment Configuration](#environment-configuration)
- [Troubleshooting](#troubleshooting)

---

## Overview

UltraLink is a comprehensive LinkedIn data processing and candidate search platform with three main subsystems:

1. **Data Collection Pipeline** (`get_data/`) - LinkedIn profile scraping via Apify API with intelligent batch processing
2. **AI Transformation Pipeline** (`transform_data/`) - OpenAI GPT-5-nano powered profile enhancement with structured outputs
3. **Search Platform** (`search/`) - Flask web app + CLI with AI-powered natural language search and GPT-4o reranking

### Current System Status
- **13,432 candidates** being processed (including Mary's connections)
- **AI-enhanced profiles** with inferred seniority, skills, and company insights
- **Web + CLI interfaces** for natural language candidate search
- **Connection filtering** by Dan, Linda, Jon, and Mary
- **Shareable search links** with UUID-based persistent search sessions
- **AI-generated highlights** via Perplexity search + GPT-4o analysis
- **HR Notes feature** for candidate annotations with edit/view modes
- **Supabase Storage profile pictures** with automatic HiUser icon fallback for missing images (5,383 uploaded, 99.1% success rate)
- **Real-time cost tracking** for all AI operations (SQL generation, classification, ranking) with backend logs and frontend display
- **Introduction email requests** - AI-generated casual emails asking mutual connections for introductions, with sender selection and dynamic recipient routing

---

## Directory Structure

```
UltraLink/
├── website/                     # Main web application
│   ├── backend/                 # Flask API backend
│   │   ├── app.py              # Main Flask app with all endpoints
│   │   ├── search.py           # Natural language to SQL generation (supports multi-connection filtering)
│   │   ├── utils.py            # Profile picture URL generation (Railway-compatible)
│   │   ├── ranking.py          # GPT-4o candidate reranking (top 30)
│   │   ├── ranking_gemini.py   # Gemini 2.5 Pro ranking (ALL candidates)
│   │   ├── ranking_stage_1.py  # Async parallel classification (strong vs partial matches)
│   │   ├── highlights.py       # Perplexity + GPT-4o highlights
│   │   ├── save_search.py      # Search session persistence
│   │   ├── add_note.py         # HR notes for candidates
│   │   ├── email_intro/        # Introduction email generation and sending
│   │   │   ├── generate_template.py  # GPT-4o email generation
│   │   │   └── send_email.py         # Resend API email sending
│   │   ├── db_schema.py        # Database schema for AI context
│   │   └── requirements.txt    # Python dependencies (includes google-generativeai)
│   │
│   ├── frontend/                # Next.js frontend
│   │   ├── app/
│   │   │   ├── page.tsx        # Main search page (handles both new & saved)
│   │   │   ├── globals.css     # Global styles & theme
│   │   │   └── search/[[...id]]/page.tsx  # Catch-all for /search/[uuid]
│   │   │   ├── components/
│   │   │   ├── SearchBar.tsx           # Multi-select connection filter
│   │   │   ├── CandidateList.tsx
│   │   │   ├── CandidateCard.tsx       # With HR notes and email intro dialog
│   │   │   ├── IntroductionEmailDialog.tsx  # Email generation modal
│   │   │   ├── CandidateHighlights.tsx
│   │   │   ├── SqlDisplay.tsx
│   │   │   └── ui/
│   │   │       ├── textarea.tsx        # Textarea component for notes
│   │   │       └── multi-select.tsx    # Custom multi-select dropdown
│   │   ├── lib/
│   │   │   └── api.ts          # API client functions
│   │   └── next.config.ts      # Next.js configuration
│   │
│   ├── tests/                   # Test files
│   │   ├── test_highlights.py
│   │   ├── test_save_search.py
│   │   ├── test_notes.py
│   │   ├── test_ranking_stage_1.py   # Test classification pipeline
│   │   ├── test_ranking_gemini.py    # Test Gemini ranking
│   │   └── test_prompt_experiments.py
│   │
│   └── .env                     # API keys and environment variables
│
├── get_data/                    # LinkedIn scraping and data collection
│   ├── get_data.py             # Main Apify scraper with batch processing
│   ├── evaluate_data_quality.py
│   ├── filter_profiles.py
│   ├── connections_data/       # CSV files with LinkedIn URLs
│   └── results/                # Scraped JSON profiles
│
├── transform_data/              # AI transformation and database import
│   ├── transform.py            # GPT-5-nano AI transformation engine (Tier 2: 250 req/min)
│   ├── models.py               # Pydantic data models
│   ├── upload_to_supabase.py   # Supabase database upload
│   ├── supabase_config.py      # Supabase client setup
│   ├── count_unique_linkedin_urls.py   # Validate LinkedIn URL uniqueness
│   ├── download_profile_pictures.py    # Download profile pictures locally (no default copies)
│   ├── upload_pictures/        # Profile picture upload utilities
│   │   └── upload_profile_pictures_to_supabase.py  # Upload to Supabase Storage
│   ├── profile_pictures/       # Local profile picture storage (5,383 images)
│   └── create_candidates_table.sql
│
└── CLAUDE.md                    # This file
```

---

## Quick Start Commands

### Data Collection Pipeline

```bash
# Scrape LinkedIn profiles from CSV connections
cd get_data
python get_data.py                    # Process connections in batches of 100

# Evaluate data quality
python evaluate_data_quality.py      # Comprehensive field analysis

# Filter incomplete profiles
python filter_profiles.py            # Remove null fullName or empty experiences

# Add connection tracking
python add_connection_source.py      # Add connected_to field
```

### AI Transformation Pipeline

```bash
cd transform_data

# Complete sequential pipeline
python main.py                        # Run entire pipeline automatically

# Individual steps
python clean_profiles.py              # Clean raw LinkedIn data
python transform.py                   # AI transform with GPT-5-nano
python upload_to_supabase.py          # Upload to Supabase database
python analyze_data_stats.py          # Generate data quality report

# Database operations
python -c "from supabase_config import test_connection; test_connection()"
```

### Search Platform

```bash
cd search

# Start web application
python app.py                         # Open http://localhost:5001

# CLI search examples
python candidate_search.py "Find Python developers" --table
python candidate_search.py "Senior engineers in San Francisco" --table
python candidate_search.py "AI developers with RAG experience" --table
python candidate_search.py "Directors who worked at startups" --table

# Interactive mode
python candidate_search.py
```

---

## Complete Pipeline Flow

### End-to-End Data Flow

```
LinkedIn Connections CSV
        ↓
┌──────────────────────┐
│  1. DATA COLLECTION  │  get_data/get_data.py
│  (Apify API)         │  • Batch processing (100 URLs)
│                      │  • Duplicate detection
│                      │  • Connection tracking
└──────────────────────┘
        ↓
   connections.json (3,123 profiles)
        ↓
┌──────────────────────┐
│  2. DATA CLEANING    │  transform_data/clean_profiles.py
│                      │  • Remove invalid data
│                      │  • Standardize formats
│                      │  • Company enrichment
└──────────────────────┘
        ↓
   cleaned_profiles.json
        ↓
┌──────────────────────┐
│  3. AI ENHANCEMENT   │  transform_data/transform.py
│  (GPT-5-nano)        │  • Infer seniority levels
│                      │  • Extract skills
│                      │  • Business model analysis
│                      │  • Generate summaries
└──────────────────────┘
        ↓
   structured_profiles.json (987 profiles)
        ↓
┌──────────────────────┐
│  4. DATABASE UPLOAD  │  transform_data/upload_to_supabase.py
│  (Supabase)          │  • Batch upsert operations
│                      │  • Duplicate handling
│                      │  • JSONB storage
└──────────────────────┘
        ↓
   Supabase PostgreSQL Database
        ↓
┌──────────────────────┐
│  5. SEARCH PLATFORM  │  search/app.py + candidate_search.py
│  (Flask + CLI)       │  • Natural language queries
│                      │  • GPT-4o-mini SQL generation
│                      │  • GPT-4o reranking
│                      │  • Web + CLI interfaces
└──────────────────────┘
```

---

## Component Details

### 1. Data Collection (`get_data/`)

#### Core Scraper: `get_data.py`

**Purpose:** Scrape LinkedIn profiles using Apify API with intelligent batch processing

**Key Features:**
- **Batch Processing:** 100 URLs per batch (Apify optimal batch size)
- **Duplicate Detection:** Checks existing profiles to avoid re-scraping
- **Connection Tracking:** Automatically adds `connected_to: ["name"]` field
- **Incremental Saving:** Saves after each batch to prevent data loss
- **Interactive Mode:** User selects number of batches to process

**Configuration:**
```python
input_file = "connections_data/jon_connections.csv"  # or linda_connections.csv
batch_size = 100
```

**Input Format (CSV):**
```csv
First Name,Last Name,URL,Email Address,Company,Position,Connected On
John,Doe,https://www.linkedin.com/in/johndoe/,john@email.com,Company,Engineer,Oct 15 2024
```

**Output Format (JSON):**
```json
{
  "linkedinUrl": "https://www.linkedin.com/in/profile",
  "fullName": "John Doe",
  "headline": "Software Engineer at Company",
  "connections": 500,
  "followers": 1200,
  "connected_to": ["linda", "jon"],
  "experiences": [...],
  "educations": [...],
  "scraped_at": "2024-12-30T10:30:00.123456"
}
```

#### Data Quality Tools

**`evaluate_data_quality.py`** - Comprehensive data quality analysis
- Field completeness percentages
- Experience and education statistics
- Contact information coverage
- Duplicate detection

**`filter_profiles.py`** - Remove incomplete profiles
- Filters profiles with null fullName OR empty experiences
- Preserves filtered data in separate file
- Backup creation before filtering

**`add_connection_source.py`** - Add connection tracking
- Adds `connected_to` field to all profiles
- Tracks which LinkedIn connection sourced each profile

#### Current Dataset Statistics
- **Total Profiles:** 3,123
- **Field Completeness:**
  - fullName: 100%
  - experiences: 100% (non-empty)
  - headline: ~95%
  - email: ~15% (LinkedIn privacy limits)
  - connections/followers: ~90%

---

### 2. AI Transformation (`transform_data/`)

#### AI Engine: `transform.py`

**Purpose:** Transform raw LinkedIn profiles into structured, AI-enhanced data using OpenAI GPT-5-nano

**Model:** `gpt-5-nano` with structured outputs via Pydantic schemas

**Rate Limiting (OpenAI Usage Tier 2):**
- **TPM Limit:** 2,000,000 tokens/minute (10x increase from Tier 1)
- **Batch Size:** 250 requests (1,000,000 TPM = 50% utilization)
- **Request Interval:** 0.24 seconds between requests
- **Batch Wait:** 60 seconds between batches for TPM reset
- **Performance:** ~250 profiles/minute (6.25x faster than Tier 1)

**AI Capabilities:**

1. **Seniority Classification** (10 levels)
   - Intern → Entry → Junior → Mid → Senior → Lead → Manager → Director → VP → C-Level
   - Based on title patterns, tenure, and responsibilities

2. **Skills Extraction**
   - Technical skills from job descriptions
   - Company-specific skills (e.g., Google: distributed systems, ML, cloud)
   - Domain expertise identification

3. **Career Analytics**
   - Total years of experience calculation
   - Average tenure per position
   - Startup employment history (considers company status at time of employment)

4. **Company Analysis**
   - Business model classification (B2B, B2C, B2B2C, C2C, B2G)
   - Product type categorization (SaaS, Platform, Mobile App, API/Developer Tools)
   - Industry tag assignment (fintech, healthcare, edtech, ai/ml, etc.)

5. **Summary Generation**
   - Full job description summaries
   - Short 1-2 sentence role descriptions
   - Standardized narrative format

6. **Location Standardization**
   - "City, State/Province, Country" format
   - Remote work identification
   - Handles missing components gracefully

#### Data Models (`models.py`)

**Pydantic Schemas for Type Safety:**

```python
class AIInferredProfile(BaseModel):
    name: str
    headline: str
    location: str
    seniority: Literal["Intern", "Entry", "Junior", "Mid", "Senior",
                       "Lead", "Manager", "Director", "VP", "C-Level"]
    years_experience: int
    worked_at_startup: bool
    education: List[Education]
    experiences: List[Experience]

class Experience(BaseModel):
    org: str
    company_url: str
    title: str
    summary: str
    short_summary: str
    location: str
    company_skills: List[str]
    business_model: Literal["B2B", "B2C", "B2B2C", "C2C", "B2G"]
    product_type: str
    industry_tags: List[str]

class Education(BaseModel):
    school: str
    degree: str
    field: str
```

#### Pipeline Runner: `main.py`

**Sequential Pipeline Execution:**
1. Extract company URLs from profiles
2. Clean company data
3. Clean profile data with company enrichment
4. AI transformation with GPT-5-nano
5. Data quality analysis
6. Database import

```bash
python main.py  # Runs complete pipeline automatically
```

#### Database Upload: `upload_to_supabase.py`

**Features:**
- Batch upsert operations (100 profiles per batch)
- Duplicate handling via linkedin_url primary key
- JSONB field conversion for experiences and education
- Error recovery with individual retry logic
- Upload verification with sample records

**Usage:**
```bash
python upload_to_supabase.py
# Uploads structured_profiles_test.json to Supabase
```

#### Data Quality Analysis: `analyze_data_stats.py`

**Generates comprehensive reports:**
- Field completeness percentages
- Seniority distribution
- Skills frequency analysis
- Experience tenure statistics
- Education distribution
- Geographic analysis

**Sample Output:**
```
Total Profiles: 987
Average Years Experience: 8.3 years
Seniority Distribution:
  - Senior: 35%
  - Mid: 28%
  - Director: 15%
  - Manager: 12%
  - C-Level: 10%
```

#### Profile Picture Download: `download_profile_pictures.py`

**Purpose:** Download LinkedIn profile pictures locally (one-time setup for new candidates)

**Key Features:**
- **Batch Downloads:** 50 concurrent downloads for speed
- **Expiration Handling:** LinkedIn profile picture URLs expire (contain `e=timestamp`)
- **No Default Copies:** No longer creates default.jpg copies (website handles fallback)
- **Status Tracking:** Returns status for each download (success/failed/no_image)

**Directory Structure:**
```
transform_data/
├── profile_pictures/        # 5,383 downloaded images
│   ├── in-shalinmantri.jpg
│   ├── in-josephleblanc.jpg
│   └── ...
└── upload_pictures/
    └── upload_profile_pictures_to_supabase.py  # Uploads to Supabase Storage
```

**Usage:**
```bash
cd transform_data

# Step 1: Download from LinkedIn
python download_profile_pictures.py
# Downloads 100x100 profile pictures for all candidates

# Step 2: Upload to Supabase Storage
python upload_pictures/upload_profile_pictures_to_supabase.py
# Uploads to profile-pictures bucket (skips already uploaded)
```

**Statistics:**
- 5,383 images uploaded to Supabase Storage (99.1% success)
- 48 failed uploads due to special characters
- Average image size: 10-20KB
- Total storage: ~54-108MB

**Note:** Website dynamically generates Supabase Storage URLs - no mapping file needed for runtime operation.

#### LinkedIn URL Validation: `count_unique_linkedin_urls.py`

**Purpose:** Validate LinkedIn URL uniqueness and detect duplicates

**Usage:**
```bash
cd transform_data
python count_unique_linkedin_urls.py
# Analyzes structured_profiles_test.json for duplicate URLs
```

---

### 3. Search Platform (`search/`)

#### Web Application: `app.py`

**Purpose:** Flask web application for AI-powered candidate search

**Technology Stack:**
- **Backend:** Flask (Python)
- **Database:** Supabase PostgreSQL
- **AI Models:**
  - GPT-4o-mini (SQL generation)
  - GPT-4o (candidate reranking)
- **Frontend:** Vanilla JavaScript + Modern CSS

**API Endpoints:**

1. **`POST /search-and-rank`** - Combined search and rank with auto-save
   - **Input:** `{"query": "Find Python developers in SF", "connected_to": "all"}` or `{"query": "...", "connected_to": "dan,linda"}`
   - **Process:**
     1. Expand abbreviations (VC → venture capital, AI → artificial intelligence)
     2. Generate SQL with GPT-4o-mini (supports multi-connection OR filtering)
     3. Execute query on Supabase
     4. Rank ALL results with Gemini 2.5 Pro (no 30 limit)
     5. Generate fit descriptions and ranking insights
     6. **Auto-save search session to database**
   - **Output:**
     ```json
     {
       "success": true,
       "id": "abc-123-uuid",
       "results": [...],
       "total": 100,
       "sql": "SELECT ..."
     }
     ```

1a. **`POST /rank`** - Rank candidates with GPT-4o (legacy, top 30 only)
   - **Input:** `{"query": "...", "candidates": [...]}`
   - **Output:** Ranked top 30 candidates with relevance scores

1b. **`POST /rank-gemini`** - Rank candidates with Gemini 2.5 Pro (ALL candidates)
   - **Input:** `{"query": "...", "candidates": [...]}`
   - **Output:** All candidates ranked with relevance scores

2. **`GET /search/<uuid>`** - Retrieve saved search session
   - **Input:** UUID in URL path
   - **Output:** Same format as POST /search-and-rank with additional metadata:
     ```json
     {
       "success": true,
       "id": "abc-123-uuid",
       "query": "Find Python developers in SF",
       "connected_to": "all",
       "sql": "SELECT ...",
       "results": [...],
       "total": 47,
       "created_at": "2025-10-24T10:30:00Z"
     }
     ```

3. **`POST /generate-highlights`** - AI-generated candidate insights
   - **Input:** `{"candidate": {...}}`
   - **Process:**
     1. Search Perplexity for professional background (20 sources)
     2. Analyze with GPT-4o to extract specific facts
     3. Filter irrelevant sources (contact databases, wrong person, etc.)
     4. Rank by importance (awards, major publications, funding, etc.)
   - **Output:**
     ```json
     {
       "success": true,
       "highlights": [
         {
           "text": "Named to TIME100 AI list in 2024",
           "source": "time.com",
           "url": "https://..."
         }
       ],
       "total_sources": 8
     }
     ```

4. **`GET /health`** - Health check endpoint

5. **`POST /notes`** - Add or update HR note for a candidate
   - **Input:** `{"linkedin_url": "...", "note": "..."}`
   - **Process:**
     1. Update notes field in candidates table
     2. Return success/error status
   - **Output:**
     ```json
     {
       "success": true,
       "message": "Note updated successfully",
       "linkedin_url": "https://...",
       "note": "Great candidate! Follow up next week."
     }
     ```

6. **`GET /notes/<linkedin_url>`** - Get HR note for a candidate
   - **Input:** LinkedIn URL in path (URL-encoded)
   - **Output:**
     ```json
     {
       "success": true,
       "linkedin_url": "https://...",
       "note": "Great candidate! Follow up next week."
     }
     ```

#### Ranking Pipelines

**Three ranking approaches available:**

1. **Gemini 2.5 Pro Ranking** (`ranking_gemini.py`) - **DEFAULT in /search-and-rank**
   - Ranks ALL candidates (no limit)
   - Uses Gemini's 2M token context window
   - Single API call for entire result set
   - Returns relevance scores + fit descriptions
   - Best for: Large result sets (50-100+ candidates)

2. **GPT-4o Ranking** (`ranking.py`) - Legacy approach
   - Ranks top 30 candidates only
   - More expensive per candidate
   - Higher quality fit descriptions
   - Best for: Small result sets where quality > quantity

3. **Stage 1 Classification** (`ranking_stage_1.py`) - Experimental
   - Async parallel classification (one GPT call per candidate)
   - Classifies as "strong" or "partial" match
   - Returns fit descriptions explaining gaps for partial matches
   - Use case: Pre-filter before expensive Stage 2 ranking
   - Test with: `python tests/test_ranking_stage_1.py`

**Multi-Connection Filtering:**
- Frontend: Multi-select dropdown for Dan, Linda, Jon, and Mary
- Backend: Converts to comma-separated string ("dan,linda,mary")
- SQL: Generates OR conditions for multiple connections
- Example SQL: `WHERE (array_to_string(connected_to, ',') ~* '\mdan\M' OR array_to_string(connected_to, ',') ~* '\mlinda\M' OR array_to_string(connected_to, ',') ~* '\mmary\M')`

**Key Features:**

**Abbreviation Expansion:**
- VC → "venture capital OR VC"
- AI → "artificial intelligence OR AI"
- ML → "machine learning OR ML"
- RAG → "retrieval augmented generation OR RAG"
- LLM → "large language model OR LLM"

**GPT-4o Reranking:**
- Analyzes top 30 candidates for relevance
- Generates relevance scores (0-100)
- Creates fit descriptions (1-2 sentences)
- Provides ranking insights explaining score factors
- Handles full profile data (skills, experiences, education)

**Safety Features:**
- SQL injection protection
- Query validation (SELECT only)
- Dangerous keyword blocking (DROP, DELETE, UPDATE, etc.)

**Web UI Features:**
- Modern Next.js 15 App Router with TypeScript
- Framer Motion animations
- shadcn/ui components with Tailwind CSS
- AI-generated highlights per candidate (click to expand)
- Candidate cards with skill badges and relevance scores
- LinkedIn profile links
- Responsive mobile design
- **Shareable search links** (auto-generated UUID URLs)
- **HR Notes** - Collapsible notes section on each candidate card with edit/view modes

#### Shareable Search Links Feature

**Purpose:** Allow users to save and share exact search results via unique URLs

**How It Works:**

1. **Auto-Save on Search**
   - Every search is automatically saved to `search_sessions` table
   - Returns UUID in response: `{"id": "abc-123-uuid", ...}`
   - Frontend updates URL to `/search/[uuid]` without page reload

2. **URL Format**
   - New search: `ultralink.com/` → Search → `ultralink.com/search/abc-123-uuid`
   - Shared link: Anyone visiting `/search/abc-123-uuid` sees exact results

3. **Frontend Implementation** (`page.tsx`)
   - Single page handles both new searches and saved searches
   - On mount: Checks URL for UUID pattern
   - If UUID found: Loads saved search via `GET /search/<uuid>`
   - If no UUID: Normal search page
   - Search bar populated with original query
   - All features work: AI highlights, edit search, new search

4. **Backend Implementation** (`save_search.py`)
   - `save_search_session()` - Saves to database, returns UUID
   - `get_search_session()` - Retrieves by UUID
   - Handles Railway connection pooler vs local direct connection
   - Results stored as JSONB for fast retrieval

5. **Database Storage**
   - Query text, SQL, results, filters, timestamp
   - No authentication required (public sharing)
   - UUID provides security through obscurity

**Use Cases:**
- Share candidate shortlists with team
- Bookmark searches for later reference
- Send specific search results to hiring managers
- Track search history via created_at timestamp

#### HR Notes Feature

**Purpose:** Allow HR team to add private notes about candidates during recruitment process

**How It Works:**

1. **Collapsible Notes Section**
   - Each candidate card has a "Notes" button next to "AI Insights"
   - Click to expand notes section (lazy loads from database)
   - Notes are fetched on-demand, not with initial search results

2. **Edit/View Mode**
   - **View Mode (default for existing notes)**: Textarea is read-only, shows "Edit Note" button
   - **Edit Mode (default for empty notes)**: Textarea is editable, shows "Save Note" + "Cancel" buttons
   - After saving, automatically switches to view mode to prevent accidental edits

3. **Frontend Implementation** (`CandidateCard.tsx`)
   - State management: `note`, `isEditingNote`, `loadingNote`, `savingNote`
   - `handleToggleNotes()` - Fetches note from backend, waits for data before showing UI
   - `handleSaveNote()` - Saves to database, switches to view mode
   - `handleEditNote()` - Enables editing
   - Uses Framer Motion for smooth expand/collapse animations

4. **Backend Implementation** (`add_note.py`)
   - `update_candidate_note(linkedin_url, note)` - Updates notes field in database
   - `get_candidate_note(linkedin_url)` - Retrieves note for a candidate
   - Uses same connection logic as other endpoints (Railway pooler vs local direct)

5. **Database Storage**
   - `notes TEXT` column in `candidates` table
   - Defaults to `NULL` for all candidates
   - No length limit - can store long-form notes

**Features:**
- Lazy loading - Notes only fetched when user clicks "Notes" button
- Caching - Once loaded, notes aren't refetched when toggling visibility
- Read-only protection - Saved notes require clicking "Edit Note" to modify
- Error handling - Shows error messages if save/load fails
- Disabled states - UI is disabled during save/load operations

**Use Cases:**
- Record interview feedback
- Track recruitment pipeline status
- Share internal assessments with hiring team
- Document concerns or red flags
- Add follow-up reminders

#### Profile Picture System

**Purpose:** Display LinkedIn profile pictures from Supabase Storage with HiUser icon fallback for missing images

**How it works:**
- Backend (`utils.py`) dynamically generates Supabase Storage URLs from LinkedIn URLs
- Frontend (`CandidateCard.tsx`) uses regular `<img>` tag with `onError` handler
- Missing images (404) automatically trigger HiUser icon fallback
- Railway-compatible environment variable loading (detects Railway vs local)

**Storage:**
- 5,383 images in Supabase Storage `profile-pictures` bucket (99.1% success)
- Failed uploads (~48 files) due to special characters show HiUser fallback

**Key files:**
- `website/backend/utils.py` - URL generation logic
- `website/frontend/components/CandidateCard.tsx` - Image display with fallback
- `transform_data/download_profile_pictures.py` - Download from LinkedIn (one-time)
- `transform_data/upload_pictures/upload_profile_pictures_to_supabase.py` - Upload to storage (one-time)

#### CLI Search: `candidate_search.py`

**Purpose:** Command-line interface for natural language candidate search

**Usage Modes:**

1. **Interactive Mode:**
   ```bash
   python candidate_search.py
   Query: Find Python developers in San Francisco
   ```

2. **Command Line Mode:**
   ```bash
   python candidate_search.py "Senior engineers with AI experience" --table
   ```

**Output Formats:**
- `--table` - ASCII table format for terminal
- `--json` (default) - Full JSON output

**Features:**
- Natural language query processing
- Abbreviation expansion
- GPT-4o-mini SQL generation
- Direct Supabase PostgreSQL connection
- Safety validation (SELECT only)
- Example queries on demand (`help` command)

**Example Queries:**
```bash
# Skills-based
"Find Python developers"
"AI developers with RAG experience"
"Senior ML engineers"

# Experience-based
"Directors who worked at startups"
"C-Level with 10+ years experience"
"People who worked at Google"

# Location-based
"ML engineers in San Francisco"
"Senior developers in New York"

# Combined
"Senior Python developers in SF with startup experience"
```

#### Database Schema Helper: `db_schema_info.py`

**Purpose:** Provides database schema context for AI SQL generation

**Schema Information:**
- Complete table structure with field types
- JSONB field documentation
- Query rules and best practices
- Example queries for common patterns

**Query Rules:**
1. Always return candidate records (not aggregations)
2. Include core fields: linkedin_url, name, location, seniority, skills, headline
3. Use exact skill matches: `'Python' = ANY(skills)`
4. Use regex for broad searches: `skills ~* '\mAI\M'`
5. Search JSONB fields: `experiences::text ILIKE '%term%'`
6. Always add LIMIT 100

---

## Database Architecture

### Supabase PostgreSQL Schema

**Primary Table: `candidates`** (Denormalized single-table design)

```sql
CREATE TABLE candidates (
    -- Primary Key
    linkedin_url TEXT PRIMARY KEY,

    -- Basic Profile
    name TEXT NOT NULL,
    headline TEXT,
    location TEXT,
    phone TEXT,
    email TEXT,
    profile_pic TEXT,
    profile_pic_high_quality TEXT,

    -- Connections
    connected_to TEXT[],

    -- Career Information
    seniority TEXT,  -- Enum: Intern | Entry | Junior | Mid | Senior |
                     --       Lead | Manager | Director | VP | C-Level
    skills TEXT[],
    years_experience INTEGER,
    average_tenure NUMERIC(4,2),
    worked_at_startup BOOLEAN DEFAULT FALSE,

    -- Nested Data (JSONB)
    experiences JSONB,  -- Array of work experiences
    education JSONB,    -- Array of educational background

    -- HR Team Notes
    notes TEXT,  -- HR notes for recruitment process (added 2025-10-25)

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Indexes for Performance:**

```sql
-- Standard B-tree indexes
CREATE INDEX idx_candidates_name ON candidates(name);
CREATE INDEX idx_candidates_location ON candidates(location);
CREATE INDEX idx_candidates_seniority ON candidates(seniority);
CREATE INDEX idx_candidates_worked_at_startup ON candidates(worked_at_startup);

-- GIN indexes for arrays and JSONB
CREATE INDEX idx_candidates_skills ON candidates USING GIN(skills);
CREATE INDEX idx_candidates_experiences ON candidates USING GIN(experiences);
CREATE INDEX idx_candidates_education ON candidates USING GIN(education);
```

**Experience JSONB Structure:**
```json
{
  "org": "Google",
  "company_url": "https://linkedin.com/company/google",
  "title": "Senior Software Engineer",
  "summary": "Led development of...",
  "short_summary": "Senior engineer leading distributed systems development.",
  "location": "San Francisco, CA, USA",
  "company_skills": ["distributed systems", "machine learning", "cloud computing"],
  "business_model": "B2B",
  "product_type": "Platform",
  "industry_tags": ["technology", "cloud", "ai/ml"]
}
```

**Education JSONB Structure:**
```json
{
  "school": "Stanford University",
  "degree": "Bachelor of Science",
  "field": "Computer Science"
}
```

**Search Sessions Table: `search_sessions`** (Shareable search links)

```sql
CREATE TABLE search_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    connected_to TEXT[],
    sql_query TEXT NOT NULL,
    results JSONB NOT NULL,
    total_results INTEGER NOT NULL,
    total_cost DECIMAL(10, 6) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Purpose:** Stores search sessions for shareable links
- Each search is automatically saved with a UUID
- URL pattern: `ultralink.com/search/[uuid]`
- Results stored as JSONB for fast retrieval
- Total cost tracked for each search (SQL + classification + ranking)
- No user authentication required - public sharing

### Database Configuration

**Supabase Connection (`supabase_config.py`):**
```python
from supabase import create_client

SUPABASE_URL = "https://[project-id].supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOi..."

client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
```

**Direct PostgreSQL Connection:**
```python
# Used by search/app.py and search/candidate_search.py
conn_string = f"postgresql://postgres:{password}@db.[project-id].supabase.co:5432/postgres"
conn = psycopg2.connect(conn_string)
```

### Database Operations

**Create Table:**
```bash
# Run in Supabase SQL Editor
cat transform_data/create_candidates_table.sql | pbcopy
# Then paste into Supabase dashboard
```

**Upload Profiles:**
```bash
cd transform_data
python upload_to_supabase.py
# Batch upsert of structured_profiles_test.json
```

**Verify Data:**
```bash
python -c "from supabase_config import test_connection; test_connection()"
```

---

## API Integrations

### 1. Apify LinkedIn Scraper

**Actor ID:** `2SyF0bVxmgGr8IVCZ`

**Configuration:**
```python
from apify_client import ApifyClient
client = ApifyClient(os.getenv('APIFY_KEY'))

run_input = {
    "profileUrls": [
        "https://www.linkedin.com/in/profile1/",
        "https://www.linkedin.com/in/profile2/"
    ]
}

run = client.actor("2SyF0bVxmgGr8IVCZ").call(run_input=run_input)
```

**Rate Limits:**
- Batch size: 100-200 URLs optimal
- Processing time: ~30-60 seconds per 100 profiles
- Cost: Varies based on Apify plan

**Output Fields:**
- `fullName`, `headline`, `linkedinUrl`
- `connections`, `followers`
- `addressWithCountry`
- `experiences[]` - Work history with nested fields
- `educations[]` - Educational background
- `mobileNumber`, `email` - Limited availability

### 2. OpenAI API

**Models Used:**

1. **GPT-5-nano** (`transform.py`)
   - Purpose: Profile transformation with structured outputs
   - Rate Limit: 200,000 TPM
   - Average tokens per profile: 3,000-5,500
   - Response format: Pydantic structured outputs

2. **GPT-4o-mini** (`search/app.py`, `search/candidate_search.py`)
   - Purpose: Natural language to SQL generation
   - Temperature: 0.1 (deterministic)
   - Context: Full database schema + example queries

3. **GPT-4o** (`search/app.py`)
   - Purpose: Candidate reranking and fit analysis
   - Temperature: 0.3 (balanced creativity)
   - Input: Top 30 candidates + search query
   - Output: Relevance scores + fit descriptions

**Configuration:**
```python
from openai import OpenAI, AsyncOpenAI
client = OpenAI()  # Sync client
async_client = AsyncOpenAI()  # Async for batch processing

# GPT-5-nano structured outputs
response = await async_client.responses.parse(
    model="gpt-5-nano",
    input=[
        {"role": "system", "content": "Extract profile data"},
        {"role": "user", "content": prompt}
    ],
    text_format=AIInferredProfile,
)

# GPT-4o-mini SQL generation
completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ],
    temperature=0.1
)
```

### 3. Supabase PostgreSQL

**Connection Methods:**

1. **Supabase Python Client** (recommended for CRUD operations)
   ```python
   from supabase import create_client
   supabase = create_client(url, service_role_key)

   # Insert/upsert
   supabase.table('candidates').upsert(data).execute()

   # Query
   result = supabase.table('candidates') \
       .select('*') \
       .eq('seniority', 'Senior') \
       .execute()
   ```

2. **Direct PostgreSQL** (recommended for complex queries)
   ```python
   import psycopg2
   conn = psycopg2.connect(connection_string)
   cursor = conn.cursor()
   cursor.execute(sql_query)
   results = cursor.fetchall()
   ```

**Best Practices:**
- Use service role key for admin operations
- Use anon key for public read-only operations
- Enable RLS (Row Level Security) for production
- Create indexes on frequently queried fields
- Use JSONB operators for nested field queries

---

## Environment Configuration

### Required Environment Variables (`.env`)

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxx

# Google Gemini Configuration (for ranking)
GOOGLE_API_KEY=your_gemini_api_key

# Perplexity Configuration (for AI highlights)
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxx

# Apify Configuration
APIFY_KEY=apify_api_xxxxxxxxxxxxxxxxx

# Supabase Configuration
SUPABASE_URL=https://[project-id].supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_DB_PASSWORD=your_secure_password

# Frontend Configuration (Next.js)
NEXT_PUBLIC_API_URL=http://localhost:5000  # Local: http://localhost:5000, Railway: https://your-backend.railway.app

# Optional: Additional AI APIs
ANTHROPIC_API_KEY=sk-ant-api03-...
VOYAGE_API_KEY=pa-...
COHERE_API_KEY=...
```

### Python Dependencies

**Backend Requirements (website/backend/requirements.txt):**
```bash
flask==3.1.2
flask-cors==6.0.1
psycopg2-binary==2.9.10
openai==1.102.0
python-dotenv==1.0.0
perplexityai==0.17.0
google-generativeai
packaging
```

**Full Installation:**
```bash
pip install -r requirements.txt  # If available
# OR install individually as listed above
```

### Project Setup

**1. Clone and Navigate:**
```bash
git clone <repository-url>
cd UltraLink
```

**2. Create Environment File:**
```bash
cp .env.example .env  # If example exists
# OR create .env manually with required keys
```

**3. Set Up Supabase Database:**
```bash
# Run SQL migrations in Supabase SQL Editor
# 1. Create candidates table
cat transform_data/create_candidates_table.sql

# 2. Create search_sessions table (for shareable links)
CREATE TABLE search_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    connected_to TEXT[],
    sql_query TEXT NOT NULL,
    results JSONB NOT NULL,
    total_results INTEGER NOT NULL,
    total_cost DECIMAL(10, 6) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

# 3. Add notes column to candidates table (for HR notes feature)
ALTER TABLE candidates ADD COLUMN notes TEXT;
```

**4. Railway Deployment:**

**Backend Service:**
```bash
# Environment Variables to set in Railway:
OPENAI_API_KEY=sk-proj-...
GOOGLE_API_KEY=your_gemini_api_key
PERPLEXITY_API_KEY=pplx-...
SUPABASE_URL=https://[project-id].supabase.co
SUPABASE_DB_PASSWORD=your_password
RAILWAY_ENVIRONMENT_NAME=production  # Automatically set by Railway
```

**Frontend Service:**
```bash
# Environment Variables to set in Railway:
NEXT_PUBLIC_API_URL=https://ultralink-production.up.railway.app  # Your backend URL (NO SPACES!)
```

**Important Railway Notes:**
- Backend uses **connection pooler (port 6543)** on Railway, **direct connection (port 5432)** locally
- Frontend `NEXT_PUBLIC_API_URL` must have NO leading/trailing spaces
- The `next.config.ts` uses `.trim()` to handle whitespace
- Deploy backend first, then set `NEXT_PUBLIC_API_URL` to backend URL before deploying frontend

**5. Local Development:**
```bash
# Run SQL migration in Supabase SQL Editor
cat transform_data/create_candidates_table.sql
# Copy and execute in Supabase dashboard
```

**4. Test Connections:**
```bash
python -c "from transform_data.supabase_config import test_connection; test_connection()"
python -c "from transform_data.db_config import test_connection; test_connection()"
```

**5. Run Initial Pipeline:**
```bash
cd get_data
python get_data.py  # Scrape profiles

cd ../transform_data
python main.py  # Transform and upload

cd ../website/backend
python app.py  # Start backend API

cd ../website/frontend
npm run dev  # Start frontend
```

**6. Test Features:**
```bash
# Test HR notes API
cd website/tests
python test_notes.py

# Test search functionality
cd website/tests
python test_save_search.py

# Test highlights generation
cd website/tests
python test_highlights.py

# Test ranking stage 1 classification
cd website/tests
python test_ranking_stage_1.py

# Test Gemini ranking
cd website/tests
python test_ranking_gemini.py
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. API Rate Limits

**OpenAI Rate Limits:**
```
Error: Rate limit exceeded
```
**Solution:**
- Reduce batch size in `transform.py` (current: 40 requests/min)
- Increase `RATE_LIMIT_INTERVAL` for slower processing
- Wait 60 seconds between batches (automatic)

**Apify Rate Limits:**
```
Error: Maximum concurrent runs exceeded
```
**Solution:**
- Process fewer batches per run
- Use interactive mode to select batch count
- Check Apify dashboard for plan limits

#### 2. Database Connection Issues

**Supabase Connection Failed:**
```
Error: Connection refused or timeout
```
**Solution:**
```bash
# Verify environment variables
echo $SUPABASE_URL
echo $SUPABASE_DB_PASSWORD

# Test connection
python -c "from transform_data.supabase_config import test_connection; test_connection()"

# Check Supabase dashboard for database status
# Verify database password in .env matches Supabase settings
```

**PostgreSQL Connection String Issues:**
```
Error: Invalid connection string
```
**Solution:**
```python
# URL-encode special characters in password
from urllib.parse import quote_plus
encoded_password = quote_plus(password)
```

#### 3. Data Quality Issues

**Missing or Incomplete Profiles:**
```bash
# Evaluate data quality
cd get_data
python evaluate_data_quality.py

# Filter incomplete profiles
python filter_profiles.py
```

**AI Transformation Failures:**
```
Error: Pydantic validation error
```
**Solution:**
- Check input data format in `cleaned_profiles.json`
- Review Pydantic models in `models.py`
- Verify OpenAI response structure
- Use `assess_extraction_quality.py` for quality analysis

#### 4. Search Platform Issues

**SQL Generation Errors:**
```
Error: Invalid SQL query generated
```
**Solution:**
- Review `db_schema_info.py` for schema context accuracy
- Check abbreviation expansion in query
- Verify GPT-4o-mini temperature (should be 0.1)
- Test with simpler queries first

**Reranking Timeouts:**
```
Error: GPT-4o timeout or token limit
```
**Solution:**
- Reduce candidate count sent to GPT-4o (current: 30)
- Simplify candidate summaries
- Check OpenAI API status
- Use fallback to return unranked results

#### 5. File and Path Issues

**Module Import Errors:**
```
Error: ModuleNotFoundError: No module named 'transform_data'
```
**Solution:**
```python
# Add to Python path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'transform_data'))
```

**JSON File Not Found:**
```bash
# Verify file paths
ls -la get_data/results/connections.json
ls -la transform_data/structured_profiles_test.json

# Update file paths in scripts if needed
input_file = "../get_data/results/connections.json"
```

#### 6. Performance Optimization

**Slow AI Transformation:**
- Current: 40 requests/min = ~25 profiles/min
- Optimize: Increase to 50 requests/min if TPM allows
- Batch processing: Process overnight for large datasets

**Slow Database Queries:**
```sql
-- Verify indexes exist
SELECT indexname, indexdef FROM pg_indexes
WHERE tablename = 'candidates';

-- Add missing indexes if needed
CREATE INDEX idx_candidates_location ON candidates(location);
```

**Memory Issues with Large Files:**
```bash
# Use streaming or chunked processing
# For files >100MB, process in smaller batches
python test_set.py  # Create test datasets
```

---

## Best Practices

### Data Collection
1. **Process in batches** - Use interactive mode to control batch size
2. **Monitor progress** - Check incremental saves after each batch
3. **Validate data quality** - Run `evaluate_data_quality.py` regularly
4. **Track connections** - Maintain `connected_to` field for network analysis

### AI Transformation
1. **Use test datasets** - Run `test_set.py` before processing large files
2. **Monitor token usage** - Track OpenAI costs and TPM limits
3. **Validate outputs** - Use `assess_extraction_quality.py` for quality checks
4. **Handle errors gracefully** - Implement retry logic and error logging

### Database Operations
1. **Use upsert** - Prevent duplicates with linkedin_url primary key
2. **Batch operations** - Upload in chunks of 100 profiles
3. **Index frequently** - Create indexes on searched fields
4. **Backup regularly** - Export JSON backups of database

### Search Platform
1. **Abbreviation expansion** - Always expand before sending to AI
2. **Query validation** - Validate all SQL before execution
3. **Rate limit AI calls** - Implement caching for repeated queries
4. **User feedback** - Show SQL and reasoning to users

---

## Data Flow Summary

### Complete Pipeline Execution Time

**3,123 Profiles - Complete Pipeline:**
1. **Data Collection:** ~16 batches × 2 min/batch = **32 minutes**
2. **Data Cleaning:** **5 minutes**
3. **AI Transformation:** 987 profiles × 1.5s/profile = **25 minutes**
4. **Database Upload:** 10 batches × 30s/batch = **5 minutes**

**Total:** ~67 minutes for complete pipeline

### Current System Status

- **Raw Profiles Collected:** 3,123 (Apify)
- **Profiles After Filtering:** 987 (removed incomplete)
- **Database Records:** 987 (Supabase)
- **Search Interface:** Web + CLI operational
- **AI Models:** GPT-5-nano, GPT-4o-mini, GPT-4o integrated

---

## Future Enhancements

### Planned Features
1. **Vector Search** - Add embedding-based similarity search
2. **Company Database** - Separate table for company information
3. **Advanced Filters** - Multi-criteria search with AND/OR logic
4. **Export Functionality** - CSV/JSON export of search results
5. **User Authentication** - Secure access control for web app
6. **Batch Search** - Upload CSV of requirements for bulk matching
7. **Email Integration** - Direct outreach from search results

### Optimization Opportunities
1. **Caching Layer** - Redis for frequent queries
2. **Background Jobs** - Celery for async processing
3. **Rate Limit Handling** - Implement exponential backoff
4. **Data Versioning** - Track profile updates over time
5. **A/B Testing** - Test different AI prompts for quality

---

## Additional Resources

### Documentation Files
- `/get_data/CLAUDE.md` - Detailed data collection pipeline docs
- `/transform_data/CLAUDE.md` - Detailed AI transformation pipeline docs
- `/search/README.md` - Search platform documentation
- `/CLAUDE.md` - This comprehensive guide

### Key Scripts
- `get_data/get_data.py` - Main scraping engine
- `transform_data/transform.py` - AI transformation engine
- `transform_data/upload_to_supabase.py` - Database upload
- `search/app.py` - Web search application
- `search/candidate_search.py` - CLI search tool

### Configuration Files
- `.env` - API keys and credentials
- `transform_data/models.py` - Pydantic data models
- `transform_data/create_candidates_table.sql` - Database schema
- `search/db_schema_info.py` - Schema context for AI

---

**Built with:** OpenAI GPT-5-nano, GPT-4o, Google Gemini 2.5 Pro, Apify, Supabase, Flask, Next.js, Pydantic

**Last Updated:** 2025-10-29
