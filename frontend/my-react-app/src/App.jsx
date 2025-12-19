import React, { useState } from 'react';
import { fetchPrediction } from './api';

// Hooks
import { useMatches } from './hooks/useMatches';

// Components
import Header from './components/Header';
import LeagueFilter from './components/LeagueFilter';
import MatchGrid from './components/MatchGrid';
import LoadingSpinner from './components/LoadingSpinner';
import PredictionModal from './components/PredictionModal';

// Styles
import './styles/index.css';

function App() {
  // 1. Business Logic from Hook
  const { activeLeague, setActiveLeague, matches, loading, refreshMatches } = useMatches();

  // 2. UI State for Prediction Modal
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [loadingPred, setLoadingPred] = useState(false);

  const handleMatchClick = async (match) => {
    setSelectedMatch(match);
    setLoadingPred(true);
    setPrediction(null);
    
    // Fetch prediction data
    const predData = await fetchPrediction(match.fixture.id);
    
    setPrediction(predData);
    setLoadingPred(false);
  };

  const closePrediction = () => {
    setSelectedMatch(null);
    setPrediction(null);
  };

  return (
    <div className="app-layout">
      {/* --- Top Bar --- */}
      <div className="top-bar">
        <Header onRefresh={refreshMatches} />
        <LeagueFilter 
          activeLeague={activeLeague} 
          onLeagueSelect={setActiveLeague} 
        />
      </div>

      {/* --- Main Content --- */}
      <div className="content-area">
        <h2 className="section-title">
          Live & Upcoming <span className="highlight">{matches.length} Matches</span>
        </h2>
        
        {loading ? (
          <LoadingSpinner />
        ) : (
          <MatchGrid matches={matches} onMatchClick={handleMatchClick} />
        )}
      </div>

      {/* --- Modal --- */}
      <PredictionModal 
        match={selectedMatch}
        prediction={prediction}
        loading={loadingPred}
        onClose={closePrediction}
      />
    </div>
  );
}

export default App;