import { ButtonHTMLAttributes, forwardRef } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  fullWidth?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', fullWidth = false, className = '', children, ...props }, ref) => {
    const baseStyles = 'h-12 px-6 rounded-xl font-medium transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed';

    const variantStyles = {
      primary: 'bg-[#4F46E5] text-white hover:bg-[#3730A3] active:scale-[0.98]',
      secondary: 'bg-white text-[#111827] border border-[#E5E7EB] hover:bg-[#F3F4F6]',
      ghost: 'bg-transparent text-[#4F46E5] hover:bg-[#F3F4F6]',
      danger: 'bg-[#EF4444] text-white hover:bg-[#DC2626] active:scale-[0.98]'
    };

    const widthClass = fullWidth ? 'w-full' : '';

    return (
      <button
        ref={ref}
        className={`${baseStyles} ${variantStyles[variant]} ${widthClass} ${className}`}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
