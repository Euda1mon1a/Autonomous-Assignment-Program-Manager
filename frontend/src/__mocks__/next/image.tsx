/**
 * Mock for next/image
 */

import React from 'react';

interface NextImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  [key: string]: unknown;
}

const NextImage: React.FC<NextImageProps> = ({ src, alt, ...props }) => {
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={src} alt={alt} {...props} />;
};

export default NextImage;
