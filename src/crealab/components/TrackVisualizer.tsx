import React from 'react';
import { GenerativeTrack } from '../types/CrealabTypes';
import './CreaLab.css';

interface Props {
  track: GenerativeTrack;
  pattern?: boolean[];
  activity?: number; // 0-1
}

export const TrackVisualizer: React.FC<Props> = ({ track, pattern = [], activity = 0 }) => {
  return (
    <div className="track-visualizer" style={{ ['--track-color' as any]: track.color }}>
      <div className="activity-indicator" style={{ opacity: activity }} />
      <div className="pattern-preview">
        {pattern.map((step, i) => (
          <div key={i} className={`pattern-step ${step ? 'active' : ''}`} />
        ))}
      </div>
    </div>
  );
};

export default TrackVisualizer;

