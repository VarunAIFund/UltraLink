'use client';

import { Menu } from 'lucide-react';
import { Button } from './ui/button';

interface HamburgerMenuProps {
  onOpen: () => void;
}

export default function HamburgerMenu({ onOpen }: HamburgerMenuProps) {
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={onOpen}
      className="fixed top-4 left-4 z-40"
      aria-label="Open menu"
    >
      <Menu className="h-6 w-6" />
    </Button>
  );
}
