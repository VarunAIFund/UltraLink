import { motion } from "framer-motion";
import { HiSearch, HiLightningBolt, HiUserGroup } from "react-icons/hi";

export function EmptyState() {
  const examples = [
    "CEO at healthcare company with startup experience",
    "Senior software engineer with Python and ML experience",
    "Stanford CS graduates who worked at Google",
    "AI engineers with 5+ years experience in San Francisco",
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="max-w-4xl mx-auto py-4"
    >
      {/* Main Content Box */}
      <div className="bg-[#faf9f7] dark:bg-card rounded-3xl shadow-lg border border-border/50 p-8 md:p-10">
        <div className="mb-12 text-center">
          <div className="flex items-center justify-center gap-4 mb-4">
            <motion.div
              animate={{
                scale: [1, 1.1, 1],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            >
              <HiSearch className="w-12 h-12 text-primary" />
            </motion.div>
            <h2 className="text-3xl font-bold">Find Your Perfect Candidate</h2>
          </div>
          <p className="text-muted-foreground text-lg mb-8">
            Search through thousands of profiles using natural language. Our AI
            understands your requirements and finds the best matches.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="p-6 border rounded-lg bg-card text-center"
          >
            <HiLightningBolt className="w-8 h-8 text-primary mx-auto mb-3" />
            <h3 className="font-semibold mb-2">AI-Powered Search</h3>
            <p className="text-sm text-muted-foreground">
              Natural language queries converted to precise database searches
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="p-6 border rounded-lg bg-card text-center"
          >
            <HiUserGroup className="w-8 h-8 text-primary mx-auto mb-3" />
            <h3 className="font-semibold mb-2">Smart Ranking</h3>
            <p className="text-sm text-muted-foreground">
              Candidates ranked by relevance with AI-generated insights
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="p-6 border rounded-lg bg-card text-center"
          >
            <HiSearch className="w-8 h-8 text-primary mx-auto mb-3" />
            <h3 className="font-semibold mb-2">Rich Profiles</h3>
            <p className="text-sm text-muted-foreground">
              View skills, experience, connections, and more
            </p>
          </motion.div>
        </div>

        <div className="text-left">
          <h3 className="text-lg font-semibold mb-4 text-center">
            Try these example searches:
          </h3>
          <div className="space-y-2">
            {examples.map((example, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.4, delay: 0.4 + i * 0.1 }}
                className="flex items-center gap-3 p-3 border rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
              >
                <HiSearch className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                <span className="text-sm text-muted-foreground">{example}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
