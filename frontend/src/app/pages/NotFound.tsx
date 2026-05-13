import { useNavigate } from 'react-router';
import { Button } from '../components/Button';

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#111827] flex items-center justify-center p-4">
      <div className="text-center max-w-md">
        {/* Animated Broken Taka Coin */}
        <div className="mb-8 flex justify-center">
          <svg
            width="200"
            height="200"
            viewBox="0 0 200 200"
            className="animate-bounce"
            style={{ animationDuration: '2s' }}
          >
            {/* Left half of coin */}
            <g>
              <path
                d="M 100 30 A 70 70 0 0 1 100 170 L 95 170 A 65 65 0 0 0 95 30 Z"
                fill="#4F46E5"
                opacity="0.9"
              />
              <text
                x="70"
                y="110"
                fontSize="48"
                fontWeight="bold"
                fill="white"
                fontFamily="var(--font-display)"
              >
                ৳
              </text>
            </g>

            {/* Right half of coin */}
            <g>
              <path
                d="M 100 30 A 70 70 0 0 0 100 170 L 105 170 A 65 65 0 0 1 105 30 Z"
                fill="#7C3AED"
                opacity="0.9"
              />
            </g>

            {/* Crack with glow effect */}
            <g>
              <defs>
                <filter id="glow">
                  <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                  <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                  </feMerge>
                </filter>
              </defs>
              <path
                d="M 100 25 L 95 50 L 105 75 L 95 100 L 105 125 L 95 150 L 100 175"
                stroke="#EF4444"
                strokeWidth="3"
                fill="none"
                filter="url(#glow)"
                className="animate-pulse"
              />
            </g>

            {/* Sparkles around the crack */}
            <circle cx="95" cy="50" r="2" fill="#EF4444" opacity="0.8" className="animate-ping" />
            <circle cx="105" cy="75" r="2" fill="#EF4444" opacity="0.6" className="animate-ping" style={{ animationDelay: '0.3s' }} />
            <circle cx="95" cy="100" r="2" fill="#EF4444" opacity="0.9" className="animate-ping" style={{ animationDelay: '0.6s' }} />
            <circle cx="105" cy="125" r="2" fill="#EF4444" opacity="0.7" className="animate-ping" style={{ animationDelay: '0.9s' }} />
          </svg>
        </div>

        {/* Text Content */}
        <h1
          className="text-white text-4xl mb-4"
          style={{ fontFamily: 'var(--font-display)', fontWeight: 700 }}
        >
          Lost your taka?
        </h1>

        <p className="text-[#9CA3AF] text-lg mb-8">
          This page doesn't exist.
        </p>

        {/* CTA Button */}
        <Button
          onClick={() => navigate('/home')}
          className="bg-[#4F46E5] hover:bg-[#3730A3]"
        >
          Go Home
        </Button>

        {/* Additional helpful text */}
        <p className="text-[#6B7280] text-sm mt-6">
          Error 404 - Page not found
        </p>
      </div>
    </div>
  );
}
