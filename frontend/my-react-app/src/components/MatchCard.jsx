import React from 'react';
import { Activity } from 'lucide-react';

const MatchCard = ({ match, onClick }) => {
  const isFinished = match.fixture.status.short === 'FT';

  return (
    <div className="match-card" onClick={() => onClick(match)}>
      <div className="team home">
        <img src={match.teams.home.logo} alt="home" className="team-logo" />
        <span className="team-name">{match.teams.home.name}</span>
      </div>
      
      <div className="match-center">
        <div className="score-badge">
          {match.goals.home ?? 0} - {match.goals.away ?? 0}
        </div>
        <span className={`status-pill ${isFinished ? 'finished' : 'live'}`}>
          {match.fixture.status.short}
        </span>
      </div>

      <div className="team away">
        <img src={match.teams.away.logo} alt="away" className="team-logo" />
        <span className="team-name">{match.teams.away.name}</span>
      </div>
      
      <div className="predict-overlay">
        <span>Tap for AI Prediction <Activity size={12} /></span>
      </div>
    </div>
  );
};

export default MatchCard;