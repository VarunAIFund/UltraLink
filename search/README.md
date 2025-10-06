# 🔍 UltraLink Candidate Search

A comprehensive search platform for the LinkedIn candidate database with both CLI and web interfaces.

## 🚀 Features

### Web Interface (Flask App)
- **Beautiful Modern UI** with gradient design and smooth animations
- **Dashboard Stats** - Total candidates, seniority distribution, startup experience
- **Multiple Search Types**:
  - View All Candidates (paginated)
  - Search by Skills (e.g., Python, React, AI)
  - Search by Seniority (Director, C-Level, etc.)
  - Search by Location (San Francisco, New York, etc.)
  - Search by Company (Google, Meta, etc.)
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Pagination** - Navigate through large result sets
- **Rich Candidate Cards** - Shows skills, location, experience, LinkedIn links

### CLI Interface (Command Line)
- **Natural Language Search** using AI (GPT-4o-mini)
- **Abbreviation Expansion** - Automatically expands VC, AI, ML, NLP, etc.
- **Smart Queries** - Understands complex queries like "Senior Python developers in SF"
- **Multiple Output Formats** - JSON or formatted table

## 📊 Database Stats
- **987 Total Candidates**
- **10 Seniority Levels** (Intern to C-Level)
- **835 with Startup Experience** (84.6%)
- **Top Skills**: Venture Capital, AI, Portfolio Management

## 🎯 Usage

### Web Interface

```bash
# Start the Flask web server
python3 search/app.py

# Access in browser
open http://localhost:5001
```

**Search Examples:**
1. Click "View All" → Browse all 987 candidates with pagination
2. Click "Search by Skills" → Enter: `Python, machine learning, React`
3. Click "Search by Seniority" → Enter: `Director` or `C-Level`
4. Click "Search by Location" → Enter: `San Francisco` or `New York`
5. Click "Search by Company" → Enter: `Google` or `Meta`

### Command Line Interface

```bash
# Basic searches
python search/candidate_search.py "Find Python developers" --table
python search/candidate_search.py "Senior engineers in San Francisco" --table
python search/candidate_search.py "Find someone with VC experience" --table

# Advanced searches
python search/candidate_search.py "AI developers with RAG experience" --table
python search/candidate_search.py "Directors who worked at startups" --table
python search/candidate_search.py "C-Level with 10+ years experience" --table

# Interactive mode
python search/candidate_search.py
```

## 🔧 Technical Details

### Web App (app.py)
- **Framework**: Flask (Python)
- **Database**: Supabase PostgreSQL
- **Frontend**: Vanilla JavaScript with modern CSS
- **API Endpoints**:
  - `GET /` - Main search page
  - `POST /api/search` - Search candidates
  - `GET /api/stats` - Database statistics

### CLI (candidate_search.py)
- **AI Model**: OpenAI GPT-4o-mini
- **Features**: SQL generation, abbreviation expansion, smart filtering
- **Database**: Direct PostgreSQL connection to Supabase

### Database Schema
```sql
Table: candidates
- linkedin_url (TEXT) PRIMARY KEY
- name, headline, location, phone, email
- seniority, skills (TEXT[]), years_experience
- worked_at_startup (BOOLEAN)
- experiences (JSONB) - work history with industry_tags, business_model
- education (JSONB) - educational background
```

## 🎨 Web UI Features

- **Gradient Background** - Modern purple gradient design
- **Stats Dashboard** - Real-time database statistics
- **Tab Navigation** - Easy switching between search types
- **Skill Badges** - Visual skill tags on candidate cards
- **Hover Effects** - Smooth animations and transitions
- **LinkedIn Integration** - Direct links to profiles
- **Loading States** - User-friendly loading indicators
- **Error Handling** - Clear error messages

## 📝 Best Performing Searches

### Skills-Based
- "Find Python developers"
- "Senior ML engineers"
- "AI developers with NLP experience"

### Experience-Based
- "Directors who worked at startups"
- "C-Level with 10+ years experience"
- "People who worked at Google"

### Location-Based
- "ML engineers in San Francisco"
- "Senior developers in New York"

### Abbreviations (Auto-Expanded)
- "VC experience" → "venture capital OR VC"
- "AI developers" → "artificial intelligence OR AI"
- "ML engineers" → "machine learning OR ML"

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install flask psycopg2-binary openai python-dotenv
   ```

2. **Configure Environment** (`.env` file should already exist)
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_DB_PASSWORD=your-password
   OPENAI_API_KEY=your-key
   ```

3. **Start Web App**
   ```bash
   python3 search/app.py
   ```

4. **Open Browser**
   ```
   http://localhost:5001
   ```

## 🎯 Use Cases

- **Recruiting** - Find candidates with specific skills and experience
- **Talent Pool Analysis** - Understand the distribution of seniority and skills
- **Network Mapping** - See who worked at which companies
- **Skill Gap Analysis** - Identify missing skills in your pipeline
- **Location-Based Hiring** - Find candidates in specific regions

## 📸 Screenshots

The web interface includes:
- Purple gradient hero section with branding
- Real-time stats dashboard (total candidates, seniority levels, startup exp)
- Tab-based search interface
- Elegant candidate cards with skills badges
- Pagination controls
- Responsive mobile-friendly design

## 🔒 Security Note

The web app uses the service role key for database access. In production, implement proper authentication and use Row Level Security (RLS) policies.

---

Built with ❤️ for UltraLink Candidate Search Platform
