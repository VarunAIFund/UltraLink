'use client';

import { X, Search, Star } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Button } from './ui/button';
import { getUser } from '@/lib/api';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  userName: string;
}

export default function Sidebar({ isOpen, onClose, userName }: SidebarProps) {
  const [userDisplayName, setUserDisplayName] = useState(userName);

  // Fetch user info to get display name
  useEffect(() => {
    if (userName) {
      getUser(userName)
        .then(data => {
          if (data.success) {
            setUserDisplayName(data.user.display_name);
          }
        })
        .catch(err => {
          console.error('Error fetching user info:', err);
        });
    }
  }, [userName]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-40"
          />

          {/* Sidebar */}
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed top-0 left-0 h-full w-80 bg-white dark:bg-gray-900 shadow-xl z-50 p-6"
          >
            {/* Close button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="absolute top-4 right-4"
              aria-label="Close menu"
            >
              <X className="h-6 w-6" />
            </Button>

            {/* User display name */}
            <div className="mt-2 mb-8">
              <h2 className="text-2xl font-bold">{userDisplayName}</h2>
            </div>

            {/* Navigation links */}
            <nav className="space-y-4">
              <Link
                href={`/${userName}/searches`}
                onClick={onClose}
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                <Search className="h-5 w-5" />
                <span className="text-lg">Searches</span>
              </Link>

              <Link
                href={`/${userName}/bookmarks`}
                onClick={onClose}
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                <Star className="h-5 w-5" />
                <span className="text-lg">Bookmarks</span>
              </Link>
            </nav>

            {/* Back to search */}
            <div className="absolute bottom-6 left-6 right-6">
              <Link
                href={`/${userName}`}
                onClick={onClose}
                className="block w-full p-3 text-center rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
              >
                Back to Search
              </Link>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
