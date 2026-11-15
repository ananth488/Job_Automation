import React from 'react';
import { cn } from '@/lib/utils';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, helperText, type = 'text', id, ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          type={type}
          className={cn(
            'w-full px-3.5 py-2 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all duration-150',
            error && 'border-red-500 focus:border-red-600 focus:ring-red-500/20 bg-red-50/30 text-red-950',
            className
          )}
          {...props}
        />
        {error && error.trim() && (
          <p className="mt-1.5 text-xs text-red-600 font-semibold flex items-center gap-1.5 animate-fadeIn">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-red-600 shrink-0"></span>
            <span>{error}</span>
          </p>
        )}
        {helperText && (!error || !error.trim()) && <p className="mt-1 text-xs text-slate-400">{helperText}</p>}
      </div>
    );
  }
);
Input.displayName = 'Input';

