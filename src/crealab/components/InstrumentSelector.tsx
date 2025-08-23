import React, { useEffect, useState } from 'react';
import { GenerativeTrack, InstrumentProfile } from '../types/CrealabTypes';
import { InstrumentProfileManager } from '../core/InstrumentProfileManager';
import './InstrumentSelector.css';

interface InstrumentSelectorProps {
  track: GenerativeTrack;
  onTrackUpdate: (updates: Partial<GenerativeTrack>) => void;
  genre?: string; // kept for compatibility
  allTracks?: GenerativeTrack[]; // kept for compatibility
}

/**
 * Native select based instrument selector used directly inside the track strip.
 * Previous modal based selector was removed to keep everything inline.
 */
export const InstrumentSelector: React.FC<InstrumentSelectorProps> = ({
  track,
  onTrackUpdate
}) => {
  const profileManager = InstrumentProfileManager.getInstance();
  const [profiles, setProfiles] = useState<InstrumentProfile[]>([]);

  useEffect(() => {
    setProfiles(profileManager.getAllProfiles());
  }, [profileManager]);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const profileId = e.target.value;
    if (!profileId) return;
    const updates = profileManager.applyProfileToTrack(track, profileId);
    onTrackUpdate(updates);
  };

  return (
    <select
      className="instrument-native-selector"
      value={track.instrumentProfile || ''}
      onChange={handleChange}
    >
      <option value="">Instrument</option>
      {profiles.map(p => (
        <option key={p.id} value={p.id}>{p.name}</option>
      ))}
    </select>
  );
};

export default InstrumentSelector;
