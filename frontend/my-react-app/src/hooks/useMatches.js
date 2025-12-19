import { useState, useEffect } from 'react';
import { LEAGUES, fetchMatches } from '../api';

export const useMatches = () => {
  const [activeLeague, setActiveLeague] = useState(LEAGUES[0]);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadMatches = async (leagueId) => {
    setLoading(true);
    const data = await fetchMatches(leagueId);
    setMatches(data);
    setLoading(false);
  };

  useEffect(() => {
    loadMatches(activeLeague.id);
  }, [activeLeague]);

  const refreshMatches = () => loadMatches(activeLeague.id);

  return { 
    activeLeague, 
    setActiveLeague, 
    matches, 
    loading, 
    refreshMatches 
  };
};