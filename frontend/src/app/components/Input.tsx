import { InputHTMLAttributes, forwardRef } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = '', ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm text-[#111827] mb-2 font-medium">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={`w-full h-12 px-4 bg-[#F3F4F6] border border-[#E5E7EB] rounded-xl
            text-[#111827] transition-all duration-200
            focus:outline-none focus:ring-2 focus:ring-[#4F46E5] focus:ring-opacity-50 focus:border-[#4F46E5]
            ${error ? 'border-[#EF4444] focus:ring-[#EF4444]' : ''}
            ${className}`}
          {...props}
        />
        {error && (
          <p className="mt-1 text-sm text-[#EF4444]">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
