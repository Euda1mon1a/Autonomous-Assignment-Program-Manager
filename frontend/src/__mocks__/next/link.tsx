/**
 * Mock for next/link
 */

import React from 'react';

interface NextLinkProps {
  children: React.ReactNode;
  href: string;
  [key: string]: unknown;
}

const NextLink: React.FC<NextLinkProps> = ({ children, href, ...props }) => {
  return (
    <a href={href} {...props}>
      {children}
    </a>
  );
};

export default NextLink;
