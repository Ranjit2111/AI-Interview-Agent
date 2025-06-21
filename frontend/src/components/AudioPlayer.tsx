import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';

interface AudioPlayerProps {
  onVoiceSelect: (voiceId: string | null) => void;
}

const AudioPlayer: React.FC<AudioPlayerProps> = ({ onVoiceSelect }) => {
  const [isEnabled, setIsEnabled] = useState(false);

  const handleToggleChange = (checked: boolean) => {
    setIsEnabled(checked);
    
    if (checked) {
      // Voice selection is handled by backend environment variables
      onVoiceSelect("enabled");
    } else {
      onVoiceSelect(null);
    }
  };

  return (
    <div className="flex items-center gap-4">
      <div className="flex items-center space-x-2">
        <Switch 
          id="tts-toggle" 
          checked={isEnabled} 
          onCheckedChange={handleToggleChange}
        />
        <Label htmlFor="tts-toggle">Voice Responses</Label>
      </div>
    </div>
  );
};

export default AudioPlayer;
