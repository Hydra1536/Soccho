import { useRef, useState, KeyboardEvent, ClipboardEvent } from 'react';

interface OTPInputProps {
  length?: number;
  onComplete?: (otp: string) => void;
}

export function OTPInput({ length = 6, onComplete }: OTPInputProps) {
  const [otp, setOtp] = useState<string[]>(Array(length).fill(''));
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const handleChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value.slice(-1);
    setOtp(newOtp);

    if (value && index < length - 1) {
      inputRefs.current[index + 1]?.focus();
    }

    if (newOtp.every(digit => digit !== '') && onComplete) {
      onComplete(newOtp.join(''));
    }
  };

  const handleKeyDown = (index: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').slice(0, length);
    if (!/^\d+$/.test(pastedData)) return;

    const newOtp = [...otp];
    pastedData.split('').forEach((char, idx) => {
      if (idx < length) newOtp[idx] = char;
    });
    setOtp(newOtp);

    const lastFilledIndex = Math.min(pastedData.length - 1, length - 1);
    inputRefs.current[lastFilledIndex]?.focus();

    if (newOtp.every(digit => digit !== '') && onComplete) {
      onComplete(newOtp.join(''));
    }
  };

  return (
    <div className="flex gap-3 justify-center">
      {otp.map((digit, index) => (
        <input
          key={index}
          ref={(el) => (inputRefs.current[index] = el)}
          type="text"
          inputMode="numeric"
          maxLength={1}
          value={digit}
          onChange={(e) => handleChange(index, e.target.value)}
          onKeyDown={(e) => handleKeyDown(index, e)}
          onPaste={handlePaste}
          className="w-12 h-14 text-center text-xl font-mono font-medium bg-[#F3F4F6] border-2 border-[#E5E7EB] rounded-xl
            focus:outline-none focus:ring-2 focus:ring-[#4F46E5] focus:border-[#4F46E5] transition-all duration-200"
        />
      ))}
    </div>
  );
}
