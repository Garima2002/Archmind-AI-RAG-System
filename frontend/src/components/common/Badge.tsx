import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'brand' | 'cyan' | 'emerald' | 'amber' | 'rose' | 'slate';
  size?: 'sm' | 'md';
  dot?: boolean;
  className?: string;
  onClick?: () => void;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  dot = false,
  className = '',
  onClick,
}) => {
  const variantStyles = {
    default: 'bg-slate-800/80 text-slate-300 border-slate-700/60',
    brand: 'bg-indigo-950/70 text-indigo-300 border-indigo-800/60',
    cyan: 'bg-cyan-950/70 text-cyan-300 border-cyan-800/60',
    emerald: 'bg-emerald-950/70 text-emerald-300 border-emerald-800/60',
    amber: 'bg-amber-950/70 text-amber-300 border-amber-800/60',
    rose: 'bg-rose-950/70 text-rose-300 border-rose-800/60',
    slate: 'bg-slate-900/90 text-slate-400 border-slate-800',
  }[variant];

  const dotColors = {
    default: 'bg-slate-400',
    brand: 'bg-indigo-400',
    cyan: 'bg-cyan-400',
    emerald: 'bg-emerald-400',
    amber: 'bg-amber-400',
    rose: 'bg-rose-400',
    slate: 'bg-slate-500',
  }[variant];

  const sizeStyles = {
    sm: 'text-xs px-2 py-0.5 font-medium',
    md: 'text-xs px-2.5 py-1 font-medium',
  }[size];

  const interactive = onClick ? 'cursor-pointer hover:brightness-110 active:scale-95 transition-all' : '';

  return (
    <span
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 rounded-full border ${variantStyles} ${sizeStyles} ${interactive} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${dotColors} animate-pulse-subtle`} />}
      {children}
    </span>
  );
};
