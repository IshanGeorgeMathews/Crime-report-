import React from 'react';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger';
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  isLoading = false,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyle =
    'inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold rounded-lg transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 select-none';

  const variants = {
    primary:
      'bg-police-slate hover:bg-police-hover text-white focus:ring-police-slate border border-transparent active:scale-[0.98]',
    secondary:
      'bg-slate-200 hover:bg-slate-300 text-police-dark focus:ring-slate-300 border border-transparent active:scale-[0.98]',
    outline:
      'bg-transparent hover:bg-slate-100 text-police-slate border border-slate-300 focus:ring-slate-300 active:scale-[0.98]',
    danger:
      'bg-police-accent hover:bg-red-700 text-white focus:ring-police-accent border border-transparent active:scale-[0.98]',
  };

  const disabledStyle = 'opacity-50 cursor-not-allowed pointer-events-none';

  return (
    <button
      className={`${baseStyle} ${variants[variant]} ${disabled || isLoading ? disabledStyle : ''} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && <Loader2 size={16} className="animate-spin" />}
      {children}
    </button>
  );
};
