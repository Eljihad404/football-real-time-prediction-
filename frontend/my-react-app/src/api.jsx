import axios from 'axios';

const API_KEY = 'YOUR_RAPIDAPI_KEY_HERE'; // Replace with your key later
const BASE_URL = 'https://api-football-v1.p.rapidapi.com/v3';

// League IDs for Top 5 Europe (2023/2024 season IDs vary, these are generic)
export const LEAGUES = [
  { id: 39, name: "Premier League", country: "England", logo: "🇬🇧" },
  { id: 140, name: "La Liga", country: "Spain", logo: "🇪🇸" },
  { id: 135, name: "Serie A", country: "Italy", logo: "🇮🇹" },
  { id: 78, name: "Bundesliga", country: "Germany", logo: "🇩🇪" },
  { id: 61, name: "Ligue 1", country: "France", logo: "🇫🇷" }
];

// Switch this to FALSE to use real API data
const USE_MOCK_DATA = true; 

export const fetchMatches = async (leagueId) => {
  if (USE_MOCK_DATA) return getMockMatches(leagueId);

  const options = {
    method: 'GET',
    url: `${BASE_URL}/fixtures`,
    params: { league: leagueId, season: '2024', next: '10' }, // Get next 10 matches
    headers: {
      'X-RapidAPI-Key': API_KEY,
      'X-RapidAPI-Host': 'api-football-v1.p.rapidapi.com'
    }
  };

  try {
    const response = await axios.request(options);
    return response.data.response;
  } catch (error) {
    console.error(error);
    return [];
  }
};

export const fetchPrediction = async (fixtureId) => {
  if (USE_MOCK_DATA) return getMockPrediction();

  const options = {
    method: 'GET',
    url: `${BASE_URL}/predictions`,
    params: { fixture: fixtureId },
    headers: {
      'X-RapidAPI-Key': API_KEY,
      'X-RapidAPI-Host': 'api-football-v1.p.rapidapi.com'
    }
  };

  try {
    const response = await axios.request(options);
    return response.data.response[0]; // The API returns an array
  } catch (error) {
    console.error(error);
    return null;
  }
};

// --- MOCK DATA GENERATORS (So you can test UI immediately) ---
const getMockMatches = (leagueId) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve([
        {
          fixture: { id: 111, status: { short: "FT" }, date: "2024-05-12T14:00:00" },
          teams: {
            home: { name: "Manchester City", logo: "https://media.api-sports.io/football/teams/50.png", winner: true },
            away: { name: "Arsenal", logo: "https://media.api-sports.io/football/teams/42.png", winner: false }
          },
          goals: { home: 3, away: 1 }
        },
        {
          fixture: { id: 222, status: { short: "NS" }, date: "2024-05-12T16:30:00" },
          teams: {
            home: { name: "Liverpool", logo: "https://media.api-sports.io/football/teams/40.png", winner: null },
            away: { name: "Chelsea", logo: "https://media.api-sports.io/football/teams/49.png", winner: null }
          },
          goals: { home: null, away: null }
        },
      ]);
    }, 500);
  });
};

const getMockPrediction = () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        predictions: {
          winner: { name: "Liverpool", comment: "Liverpool has a strong home advantage." },
          percent: { home: "65%", draw: "20%", away: "15%" },
          advice: "Winner: Liverpool"
        }
      });
    }, 500);
  });
};