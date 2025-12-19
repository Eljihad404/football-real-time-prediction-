import React from 'react';
import { LEAGUES } from '../api';

const LeagueFilter = ({ activeLeague, onLeagueSelect }) => {
  return (
    <div className="league-filter">
      {LEAGUES.map((league) => (
        <button
          key={league.id}
          className={`league-btn ${activeLeague.id === league.id ? 'active' : ''}`}
          onClick={() => onLeagueSelect(league)}
        >
          <span className="league-flag">{league.logo}</span>
          {league.name}
        </button>
      ))}
    </div>
  );
};

export default LeagueFilter;