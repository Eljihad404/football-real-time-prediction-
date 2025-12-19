import React from 'react';
import { XCircle } from 'lucide-react';

const PredictionModal = ({ match, prediction, loading, onClose }) => {
  if (!match) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="close-btn" onClick={onClose}><XCircle size={24}/></button>
        
        <div className="modal-header">
          <h3>AI Prediction Analysis</h3>
          <p>{match.teams.home.name} vs {match.teams.away.name}</p>
        </div>

        {loading ? (
          <div className="loading-pred">Analyzing stats...</div>
        ) : prediction ? (
          <div className="prediction-body">
            <div className="advice-card">
              <div className="advice-label">ALGORITHM SAYS:</div>
              <div className="advice-text">{prediction.predictions.advice}</div>
            </div>

            <div className="stat-bars">
              {['home', 'draw', 'away'].map((type) => (
                <div key={type} className="stat-row">
                  <div className="stat-label">
                    <span>{type === 'home' ? match.teams.home.name : type === 'away' ? match.teams.away.name : 'Draw'}</span>
                    <strong>{prediction.predictions.percent[type]}</strong>
                  </div>
                  <div className="bar-track">
                    <div 
                      className={`bar-fill ${type}`} 
                      style={{width: prediction.predictions.percent[type]}}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="no-data">Data unavailable for this match.</p>
        )}
      </div>
    </div>
  );
};

export default PredictionModal;