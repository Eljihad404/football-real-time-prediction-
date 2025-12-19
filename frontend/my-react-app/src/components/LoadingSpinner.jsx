import React from 'react';

const LoadingSpinner = () => {
  return (
    <div className="loading-state">
      <div className="spinner"></div>
      <p>Scanning League Data...</p>
    </div>
  );
};

export default LoadingSpinner;