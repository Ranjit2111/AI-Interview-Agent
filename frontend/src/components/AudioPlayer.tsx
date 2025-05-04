import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { api } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface AudioPlayerProps {
  onVoiceSelect: (voiceId: string | null) => void;
}

const AudioPlayer: React.FC<AudioPlayerProps> = ({ onVoiceSelect }) => {
  const [voices, setVoices] = useState<{ id: string; name: string }[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<string | null>(null);
  const [isEnabled, setIsEnabled] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    // Fetch available voices when the component mounts
    if (isEnabled && voices.length === 0) {
      fetchVoices();
    }
  }, [isEnabled]);

  const fetchVoices = async () => {
    try {
      const response = await api.getVoices();
      if (response.voices && response.voices.length > 0) {
        setVoices(response.voices);
        // Select the first voice by default
        setSelectedVoice(response.voices[0].id);
        onVoiceSelect(response.voices[0].id);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load text-to-speech voices',
        variant: 'destructive',
      });
      console.error('Failed to load voices:', error);
    }
  };

  const handleToggleChange = (checked: boolean) => {
    setIsEnabled(checked);
    
    if (checked) {
      if (voices.length === 0) {
        fetchVoices();
      } else if (selectedVoice) {
        onVoiceSelect(selectedVoice);
      }
    } else {
      onVoiceSelect(null);
    }
  };

  const handleVoiceChange = (voiceId: string) => {
    setSelectedVoice(voiceId);
    if (isEnabled) {
      onVoiceSelect(voiceId);
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
      
      {isEnabled && voices.length > 0 && (
        <Select value={selectedVoice || ''} onValueChange={handleVoiceChange}>
          <SelectTrigger className="w-[180px] h-8 bg-gray-900/70 border-gray-700/70 text-gray-100">
            <SelectValue placeholder="Select voice" />
          </SelectTrigger>
          <SelectContent className="bg-gray-900/90 border-gray-700 text-gray-100">
            {voices.map((voice) => (
              <SelectItem key={voice.id} value={voice.id} className="hover:bg-gray-800">
                {voice.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
    </div>
  );
};

export default AudioPlayer;
