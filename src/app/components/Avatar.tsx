interface AvatarProps {
  name: string;
  size?: 'small' | 'medium' | 'large';
}

export function Avatar({ name, size = 'medium' }: AvatarProps) {
  const sizes = {
    small: 'w-8 h-8 text-sm',
    medium: 'w-11 h-11 text-base',
    large: 'w-[72px] h-[72px] text-2xl'
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const getGradient = (name: string) => {
    const hue = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % 360;
    return `linear-gradient(135deg, hsl(${hue}, 70%, 55%), hsl(${(hue + 30) % 360}, 70%, 65%))`;
  };

  return (
    <div
      className={`${sizes[size]} rounded-full flex items-center justify-center font-medium text-white ring-2 ring-white shadow-lg`}
      style={{ background: getGradient(name) }}
    >
      {getInitials(name)}
    </div>
  );
}
