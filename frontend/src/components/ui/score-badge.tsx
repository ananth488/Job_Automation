import React from 'react';
import { cn } from '@/lib/utils';

export interface ScoreBadgeProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export const ScoreBadge: React.FC<ScoreBadgeProps> = ({
  score,
  size = 'md',
  showLabel = false,
}) => {
  const getColors = (s: number) => {
    if (s >= 85) return 'text-emerald-700 bg-emerald-50 border-emerald-200';
    if (s >= 70) return 'text-indigo-700 bg-indigo-50 border-indigo-200';
    if (s >= 50) return 'text-amber-700 bg-amber-50 border-amber-200';
    return 'text-rose-700 bg-rose-50 border-rose-200';
  };

  const sizes = {
    sm: 'text-xs px-2 py-0.5 font-semibold',
    md: 'text-xs px-2.5 py-1 font-bold',
    lg: 'text-sm px-3.5 py-1.5 font-extrabold',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full border shadow-xs',
        getColors(score),
        sizes[size]
      )}
    >
      <span>{Math.round(score)}%</span>
      {showLabel && <span className="text-[10px] font-medium opacity-80">Match</span>}
    </span>
  );
};

