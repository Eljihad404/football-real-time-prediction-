import React from 'react';
import { Trophy, RefreshCw } from 'lucide-react';

const Header = ({ onRefresh }) => {
  return (
    <header className="header">
      <h1><Trophy color="#FFD700" size={24} /> Euro Predictor</h1>
      <button className="refresh-btn" onClick={onRefresh} aria-label="Refresh">
        <RefreshCw size={18} />
      </button>
    </header>
  );
};

export default Header;