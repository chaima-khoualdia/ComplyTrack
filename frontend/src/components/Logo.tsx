import React from 'react';

interface LogoProps {
  variant?: 'full' | 'noslogan' | 'icon';
  theme?: 'light' | 'dark';
  className?: string;
  alt?: string;
}

export function Logo({ variant = 'noslogan', theme = 'dark', className = 'h-8', alt = 'ComplyTrack' }: LogoProps) {
  let src = '';
  if (variant === 'icon') {
    src = theme === 'dark' ? '/src/assets/Logo_Icon_Dark.svg' : '/src/assets/Logo_Icon_Light.svg';
  } else if (variant === 'full') {
    src = theme === 'dark' ? '/src/assets/Logo_Full_Dark_Large.svg' : '/src/assets/Logo_Full_Light_Large.svg';
  } else {
    src = theme === 'dark' ? '/src/assets/Logo_NoSlogan_Dark.svg' : '/src/assets/Logo_NoSlogan_Light.svg';
  }
  return <img src={src} alt={alt} className={className} />;
}
