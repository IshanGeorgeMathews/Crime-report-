import React from 'react';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'blue' | 'amber' | 'green' | 'red' | 'gray' | 'orange' | 'purple';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'gray',
  className = '',
}) => {
  const baseStyle = 'inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider select-none';

  const variants = {
    blue: 'bg-sky-100 text-sky-800 border border-sky-200/50',
    amber: 'bg-amber-100 text-amber-800 border border-amber-200/50',
    green: 'bg-emerald-100 text-emerald-800 border border-emerald-200/50',
    red: 'bg-rose-100 text-rose-800 border border-rose-200/50',
    gray: 'bg-slate-100 text-slate-700 border border-slate-200/50',
    orange: 'bg-orange-100 text-orange-800 border border-orange-200/50',
    purple: 'bg-purple-100 text-purple-800 border border-purple-200/50',
  };

  return <span className={`${baseStyle} ${variants[variant]} ${className}`}>{children}</span>;
};
export default Badge;
