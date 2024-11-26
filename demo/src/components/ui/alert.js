import React from 'react';

export const Alert = ({ variant, children, className }) => {
  const variantClasses = {
    destructive: 'bg-red-100 text-red-700 border-red-400',
    // Add other variants if needed
  };

  return (
    <div className={`border-l-4 p-4 ${variantClasses[variant]} ${className}`}>
      {children}
    </div>
  );
};

export const AlertDescription = ({ children }) => {
  return <div>{children}</div>;
};