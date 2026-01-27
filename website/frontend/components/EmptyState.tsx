"use client";

import { motion } from "framer-motion";
import { Search, Zap, Users, Star, Mail, Filter, MapPin, Sparkles, PlayCircle } from "lucide-react";
import Image from "next/image";

export function EmptyState() {
  const examples = [
    "CEO at healthcare company with startup experience",
    "Senior Python engineers in San Francisco",
    "Stanford CS graduates who worked at Google",
    "AI engineers with 5+ years experience",
  ];

  const walkthroughSteps = [
    {
      image: "/images/step1_search_bar.png",
      title: "Step 1: Start Your Search",
      description: "Welcome to UltraLink! Start by entering your search in the main search bar. Choose between 'Fast Response' for quick results, or 'Relevance Ranking' for AI-powered scoring and match explanations. The homepage shows three key features: AI-Powered Search that understands natural language, Smart Ranking that scores every candidate, and Rich Profiles with detailed information."
    },
    {
      image: "/images/step3_select_connections.png",
      title: "Step 2: Filter by Your Connections",
      description: "Use the dropdown menu to filter candidates by which mutual connection knows them. You can search through All connections at once, or narrow down to specific people like Dan, Linda, Jon, Mary, and others. This helps you leverage your network for warm introductions and see who can make the best introduction to each candidate."
    },
    {
      image: "/images/step4_results_loading.png",
      title: "Step 3: See Your Results Summary",
      description: "The results page shows how many total candidates were found (297 in this example) and breaks them down by match quality. Strong Matches (245) are candidates with AI scores of 70-100 who closely fit your requirements. The system automatically organizes results by relevance so the best matches appear first."
    },
    {
      image: "/images/step5_results_list.png",
      title: "Step 4: Explore Candidate Details",
      description: "Click on any candidate to see their full profile. Strong Matches appear first with detailed explanations of why they're a good fit. Each profile includes their location, seniority level (like C-Level), years of experience, relevant skills, and which connections you have in common. Three quick-access buttons let you add Notes, check Lever hiring status, or view AI Insights."
    },
    {
      image: "/images/step8_more_candidates.png",
      title: "Step 5: Add Private Notes",
      description: "Click 'Notes' to add private recruitment notes for your team. This example shows Abtin Tondar who scored 100 as a perfect match for a healthcare CEO role, with a detailed AI explanation of why he fits the criteria. Use the notes section to track your recruitment feedback, next steps, or interview scheduling information."
    },
    {
      image: "/images/step6_candidate_details.png",
      title: "Step 6: Check Lever Integration",
      description: "Click 'Lever' to see if this candidate is already in your hiring system. If they've previously applied or been considered, their Lever opportunities will show up here with their current status. This helps you avoid duplicate outreach and stay organized. You can also use the 'Hide hired' toggle at the top to filter out candidates who have already been hired."
    },
    {
      image: "/images/step7_ai_insights.png",
      title: "Step 7: Discover AI-Generated Insights",
      description: "Click 'AI Insights' to see professional highlights about the candidate from across the web. The system automatically researches and summarizes awards, keynote speeches, podcast appearances, publications, and other achievements that aren't on their LinkedIn. Each insight includes a source link so you can verify the information and learn more."
    },
    {
      image: "/images/step2_enter_query.png",
      title: "Step 8: Access Past Searches & Bookmarks",
      description: "Click the menu icon (three horizontal lines) in the top-left to open the navigation sidebar. Here you can access 'Past Searches' to revisit any previous search with all results preserved, or 'Bookmarks' to see candidates you've starred. The 'Back to Search' button takes you to the main search page. Your searches and bookmarks are private to you."
    },
    {
      image: "/images/step9_additional_results.png",
      title: "Step 9: Review Your Search History",
      description: "The Search History page shows all your previous searches with the original query, how many results were found, when you ran the search, and completion status. Click any search to instantly reload the full results with all AI scores and explanations exactly as they were. This makes it easy to track your recruitment pipeline and return to promising candidate pools without starting over."
    },
    {
      image: "/images/step11_request_intro.png",
      title: "Step 10: Request an Introduction",
      description: "When you find a great candidate, click to request an introduction through your mutual connection. A dialog appears showing which connection knows the candidate (in this case, Dan). Click 'Generate Email' to create a personalized introduction request. The email will be sent from your account to your mutual connection asking them to make the introduction."
    },
    {
      image: "/images/step12_send_email.png",
      title: "Step 11: Review and Send the Email",
      description: "The system generates a personalized email with a subject line and body text. The email explains why you're interested in the candidate and highlights their relevant background from their profile. You can edit the text before sending - double line breaks create new paragraphs. When ready, click 'Send Email' to request the introduction, or 'Cancel' to go back."
    },
    {
      image: "/images/step10_complete_view.png",
      title: "Step 12: Organize Your Bookmarks",
      description: "The Bookmarks page displays all candidates you've starred for later review. Each card shows their profile picture, name, current role, and headline. Click the star to remove a bookmark, or use 'Notes' to add private recruitment comments. You can access their LinkedIn profiles directly from here. All bookmarks are saved to your account and available whenever you need them."
    }
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="max-w-4xl mx-auto py-6"
    >
      {/* Main Card */}
      <div className="bg-card rounded-2xl border shadow-sm p-8">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-primary/10 mb-4">
            <Search className="w-7 h-7 text-primary" />
          </div>
          <h2 className="text-2xl font-bold mb-2">Find Your Perfect Candidate</h2>
          <p className="text-muted-foreground">
            Search through profiles using natural language. AI understands your requirements.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 gap-4 mb-10">
          {/* Feature 1 */}
          <div className="flex gap-4 p-4 rounded-xl bg-muted/30 border border-border/50">
            <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
              <Zap className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <h3 className="font-semibold mb-1">Two Search Modes</h3>
              <p className="text-sm text-muted-foreground">
                Fast Response for quick results, or Relevance Ranking for AI-scored matches with fit explanations.
              </p>
            </div>
          </div>

          {/* Feature 2 */}
          <div className="flex gap-4 p-4 rounded-xl bg-muted/30 border border-border/50">
            <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
              <Star className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <h3 className="font-semibold mb-1">AI Match Scoring</h3>
              <p className="text-sm text-muted-foreground">
                Every candidate scored 0-100. See Strong, Partial, and No Matches with AI-written explanations.
              </p>
            </div>
          </div>

          {/* Feature 3 */}
          <div className="flex gap-4 p-4 rounded-xl bg-muted/30 border border-border/50">
            <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
              <Filter className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <h3 className="font-semibold mb-1">Connection Filtering</h3>
              <p className="text-sm text-muted-foreground">
                Filter by mutual connections. See who you know in common with each candidate.
              </p>
            </div>
          </div>

          {/* Feature 4 */}
          <div className="flex gap-4 p-4 rounded-xl bg-muted/30 border border-border/50">
            <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
              <MapPin className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <h3 className="font-semibold mb-1">Location Search</h3>
              <p className="text-sm text-muted-foreground">
                Search by city and automatically include nearby areas within 25 miles.
              </p>
            </div>
          </div>

          {/* Feature 5 */}
          <div className="flex gap-4 p-4 rounded-xl bg-muted/30 border border-border/50">
            <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
              <Users className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <h3 className="font-semibold mb-1">Lever Integration</h3>
              <p className="text-sm text-muted-foreground">
                See &quot;Hired&quot; status from Lever. Toggle to hide candidates already in the ecosystem.
              </p>
            </div>
          </div>

          {/* Feature 6 */}
          <div className="flex gap-4 p-4 rounded-xl bg-muted/30 border border-border/50">
            <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
              <Mail className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <h3 className="font-semibold mb-1">Intro Emails</h3>
              <p className="text-sm text-muted-foreground">
                Generate personalized introduction emails with one click. Send directly to mutual connections.
              </p>
            </div>
          </div>
        </div>

        {/* Example Searches */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-4 h-4 text-primary" />
            <h3 className="font-semibold text-sm">Try these searches</h3>
          </div>
          <div className="grid sm:grid-cols-2 gap-2">
            {examples.map((example, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: 0.1 + i * 0.05 }}
                className="flex items-center gap-2 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors cursor-default"
              >
                <Search className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
                <span className="text-sm text-muted-foreground">{example}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Walkthrough Section */}
      <div className="bg-card rounded-2xl border shadow-sm p-8 mt-6">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-br from-primary/20 to-primary/10 mb-4">
            <PlayCircle className="w-7 h-7 text-primary" />
          </div>
          <h2 className="text-2xl font-bold mb-2">See How It Works</h2>
          <p className="text-muted-foreground">
            Follow this example search to understand the full workflow
          </p>
        </div>

        <div className="space-y-12">
          {walkthroughSteps.map((step, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 + i * 0.1 }}
              className="flex flex-col gap-4"
            >
              {/* Step Header */}
              <div className="flex items-center gap-3">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold shadow-lg">
                  {i + 1}
                </div>
                <h3 className="text-xl font-bold">{step.title}</h3>
              </div>

              {/* Screenshot */}
              <div className="relative overflow-hidden rounded-xl border-2 bg-muted/30 shadow-md">
                <div className="relative w-full aspect-video">
                  <Image
                    src={step.image}
                    alt={step.title}
                    fill
                    className="object-contain"
                  />
                </div>
              </div>

              {/* Description */}
              <p className="text-base text-muted-foreground leading-relaxed pl-[52px]">
                {step.description}
              </p>

              {/* Divider (except for last item) */}
              {i < walkthroughSteps.length - 1 && (
                <div className="w-full h-px bg-border/50 mt-4" />
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
