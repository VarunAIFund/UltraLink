import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { motion } from "framer-motion";

export function CandidateCardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-start gap-4">
          <div className="flex gap-4 flex-1 items-center">
            {/* Profile pic skeleton */}
            <motion.div
              className="w-16 h-16 rounded-full bg-muted"
              animate={{
                opacity: [0.5, 1, 0.5],
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />
            <div className="flex-1 space-y-2">
              {/* Name skeleton */}
              <motion.div
                className="h-5 bg-muted rounded w-1/3"
                animate={{
                  opacity: [0.5, 1, 0.5],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              />
              {/* Headline skeleton */}
              <motion.div
                className="h-4 bg-muted rounded w-2/3"
                animate={{
                  opacity: [0.5, 1, 0.5],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: "easeInOut",
                  delay: 0.2,
                }}
              />
            </div>
          </div>
          {/* Score skeleton */}
          <motion.div
            className="w-12 h-12 bg-muted rounded"
            animate={{
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 0.1,
            }}
          />
        </div>
      </CardHeader>
      <CardContent>
        {/* Description skeleton */}
        <motion.div
          className="h-4 bg-muted rounded w-full mb-2"
          animate={{
            opacity: [0.5, 1, 0.5],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 0.3,
          }}
        />
        <motion.div
          className="h-4 bg-muted rounded w-4/5 mb-4"
          animate={{
            opacity: [0.5, 1, 0.5],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 0.4,
          }}
        />
        {/* Skills skeleton */}
        <div className="flex gap-2 mt-4">
          {[1, 2, 3, 4].map((i) => (
            <motion.div
              key={i}
              className="h-6 w-16 bg-muted rounded"
              animate={{
                opacity: [0.5, 1, 0.5],
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 0.5 + i * 0.1,
              }}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
