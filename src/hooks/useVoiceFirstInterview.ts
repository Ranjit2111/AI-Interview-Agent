import React, { useCallback } from 'react';

// TTS state management
const handleTTSStart = useCallback((isInitial: boolean = false) => {
  console.log('🎙️ TTS Start - Setting audioPlaying=true, turnState=ai', { isInitial });
  
  if (isInitial) {
    // For initial message, only set synthesis state, not visual AI state yet
    setIsInitialTTSSynthesizing(true);
    setIsInitialMessage(true);
    setVoiceState(prev => ({
      ...prev,
      microphoneState: 'disabled' as const // Block mic during synthesis
    }));
    console.log('🎙️ Initial TTS Start - Setting synthesis state, mic disabled');
  } else {
    // For regular interview messages, DON'T show AI state during synthesis - wait for audio to play
    setVoiceState(prev => {
      const newState: VoiceState = {
        ...prev,
        audioState: 'buffering' as const,
        microphoneState: 'disabled' as const
        // turnState stays 'idle' until audio actually plays
      };
      console.log('🎙️ Regular TTS Start - Synthesis started, mic disabled, waiting for audio to play:', newState);
      return newState;
    });
  }
}, []); 