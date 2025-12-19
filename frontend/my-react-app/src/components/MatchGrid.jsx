import React from 'react';
import MatchCard from './MatchCard';

const MatchGrid = ({ matches, onMatchClick }) => {
  return (
    <div className="match-grid">
      {matches.map((match) => (
        <MatchCard 
          key={match.fixture.id} 
          match={match} 
          onClick={onMatchClick} 
        />
      ))}
    </div>
  );
};

export default MatchGrid;