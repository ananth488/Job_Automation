'use client';

import React, { useState, useRef, useEffect } from 'react';
import { MapPin, X, Check, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';

export const TOP_TECH_LOCATIONS = [
  'Chennai',
  'Bengaluru',
  'Hyderabad',
  'Pune',
  'Mumbai',
  'Delhi / NCR',
  'Noida',
  'Gurugram',
  'Coimbatore',
  'Kochi',
  'Trivandrum',
  'Kolkata',
  'Ahmedabad',
  'Jaipur',
  'Chandigarh',
  'Indore',
  'Mysuru',
  'Bhubaneswar',
  'Remote (India)',
  'Remote (Worldwide)',
  'Singapore',
  'Dubai',
  'London',
  'San Francisco / Bay Area',
  'New York',
  'Seattle',
  'Austin',
  'Toronto',
];

interface LocationAutocompleteProps {
  label?: string;
  placeholder?: string;
  value: string;
  onChange: (val: string) => void;
  error?: string;
  helperText?: string;
  className?: string;
}

/**
 * Single Location Autocomplete input (ideal for Current Location)
 */
export const LocationAutocomplete: React.FC<LocationAutocompleteProps> = ({
  label,
  placeholder = 'e.g. Chennai, Bengaluru',
  value,
  onChange,
  error,
  helperText,
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const query = value.trim().toLowerCase();
  const filtered = query
    ? TOP_TECH_LOCATIONS.filter((loc) => loc.toLowerCase().includes(query))
    : TOP_TECH_LOCATIONS.slice(0, 8);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (loc: string) => {
    onChange(loc);
    setIsOpen(false);
  };

  return (
    <div ref={containerRef} className={cn('relative w-full', className)}>
      {label && (
        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
          {label}
        </label>
      )}

      <div className="relative">
        <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        <input
          type="text"
          value={value}
          onChange={(e) => {
            onChange(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          placeholder={placeholder}
          className={cn(
            'w-full pl-9 pr-8 py-2 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all duration-150',
            error && 'border-red-500 focus:border-red-600 focus:ring-red-500/20 bg-red-50/30 text-red-950'
          )}
        />
        {value && (
          <button
            type="button"
            onClick={() => onChange('')}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            aria-label="Clear location"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {error && (
        <p className="mt-1.5 text-xs text-red-600 font-semibold flex items-center gap-1.5">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-red-600 shrink-0"></span>
          <span>{error}</span>
        </p>
      )}

      {helperText && !error && (
        <p className="mt-1 text-xs text-slate-400">{helperText}</p>
      )}

      {/* Dropdown Suggestions */}
      {isOpen && filtered.length > 0 && (
        <div className="absolute z-50 left-0 right-0 mt-1 max-h-56 overflow-y-auto bg-white border border-slate-200 rounded-xl shadow-xl py-1 divide-y divide-slate-50">
          <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Suggested Locations
          </div>
          {filtered.map((loc) => {
            const isSelected = value.toLowerCase() === loc.toLowerCase();
            return (
              <button
                key={loc}
                type="button"
                onClick={() => handleSelect(loc)}
                className={cn(
                  'w-full px-3.5 py-2 text-left text-xs font-medium flex items-center justify-between hover:bg-indigo-50/80 hover:text-indigo-900 transition-colors',
                  isSelected ? 'bg-indigo-50 text-indigo-700 font-semibold' : 'text-slate-700'
                )}
              >
                <div className="flex items-center gap-2">
                  <MapPin className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                  <span>{loc}</span>
                </div>
                {isSelected && <Check className="w-3.5 h-3.5 text-indigo-600" />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

interface MultiLocationInputProps {
  label?: string;
  placeholder?: string;
  locations: string[];
  onChange: (locs: string[]) => void;
  error?: string;
  helperText?: string;
  className?: string;
}

/**
 * Multi Location chip selector with autocomplete suggestions (ideal for Preferred Locations)
 */
export const MultiLocationInput: React.FC<MultiLocationInputProps> = ({
  label,
  placeholder = 'Type a city and select (e.g. Chennai, Remote)...',
  locations,
  onChange,
  error,
  helperText,
  className,
}) => {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const cleanQuery = query.trim().toLowerCase();
  const filtered = cleanQuery
    ? TOP_TECH_LOCATIONS.filter(
        (loc) =>
          loc.toLowerCase().includes(cleanQuery) &&
          !locations.some((l) => l.toLowerCase() === loc.toLowerCase())
      )
    : TOP_TECH_LOCATIONS.filter(
        (loc) => !locations.some((l) => l.toLowerCase() === loc.toLowerCase())
      ).slice(0, 6);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleAddLocation = (loc: string) => {
    const trimmed = loc.trim();
    if (trimmed && !locations.some((l) => l.toLowerCase() === trimmed.toLowerCase())) {
      onChange([...locations, trimmed]);
      setQuery('');
      setIsOpen(false);
    }
  };

  const handleRemoveLocation = (locToRemove: string) => {
    onChange(locations.filter((l) => l !== locToRemove));
  };

  return (
    <div ref={containerRef} className={cn('relative w-full', className)}>
      {label && (
        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
          {label} {locations.length > 0 && `(${locations.length})`}
        </label>
      )}

      {/* Input box */}
      <div className="relative">
        <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              if (query.trim()) {
                handleAddLocation(query.trim());
              }
            }
          }}
          placeholder={placeholder}
          className={cn(
            'w-full pl-9 pr-20 py-2 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all duration-150',
            error && 'border-red-500 focus:border-red-600 focus:ring-red-500/20 bg-red-50/30 text-red-950'
          )}
        />
        {query.trim() && (
          <button
            type="button"
            onClick={() => handleAddLocation(query.trim())}
            className="absolute right-2 top-1/2 -translate-y-1/2 px-2.5 py-1 text-xs font-semibold bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded-md transition-colors"
          >
            Add
          </button>
        )}
      </div>

      {error && (
        <p className="mt-1.5 text-xs text-red-600 font-semibold flex items-center gap-1.5">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-red-600 shrink-0"></span>
          <span>{error}</span>
        </p>
      )}

      {helperText && !error && (
        <p className="mt-1 text-xs text-slate-400">{helperText}</p>
      )}

      {/* Location Chips */}
      {locations.length > 0 && (
        <div className="flex items-center gap-1.5 flex-wrap mt-2.5">
          {locations.map((loc) => (
            <span
              key={loc}
              className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200/80 shadow-2xs"
            >
              <MapPin className="w-3 h-3 text-emerald-600" />
              <span>{loc}</span>
              <button
                type="button"
                onClick={() => handleRemoveLocation(loc)}
                className="text-emerald-500 hover:text-emerald-800 transition-colors"
                aria-label={`Remove ${loc}`}
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Autocomplete Suggestions */}
      {isOpen && filtered.length > 0 && (
        <div className="absolute z-50 left-0 right-0 mt-1 max-h-56 overflow-y-auto bg-white border border-slate-200 rounded-xl shadow-xl py-1 divide-y divide-slate-50">
          <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Suggested Tech Hubs
          </div>
          {filtered.map((loc) => (
            <button
              key={loc}
              type="button"
              onClick={() => handleAddLocation(loc)}
              className="w-full px-3.5 py-2 text-left text-xs font-medium flex items-center justify-between text-slate-700 hover:bg-indigo-50/80 hover:text-indigo-900 transition-colors"
            >
              <div className="flex items-center gap-2">
                <MapPin className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                <span>{loc}</span>
              </div>
              <Plus className="w-3.5 h-3.5 text-slate-400" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

