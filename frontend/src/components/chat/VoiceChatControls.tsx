import { useEffect } from "react";
import { useWebSpeech } from "../../hooks/useWebSpeech";

type Props = {
  onTranscript: (value: string) => void;
  promptToRead?: string | null;
  disabled?: boolean;
};

export default function VoiceChatControls({ onTranscript, promptToRead, disabled = false }: Props) {
  const speech = useWebSpeech();

  useEffect(() => {
    if (speech.transcript) onTranscript(speech.transcript);
  }, [speech.transcript, onTranscript]);

  useEffect(() => {
    if (promptToRead) speech.speakText(promptToRead);
  }, [promptToRead, speech.speakText]);

  if (!speech.speechSupported && !("speechSynthesis" in window)) return null;

  return (
    <div className="voice-controls" aria-label="Voice controls">
      {speech.speechSupported && (
        <button
          type="button"
          className="secondary"
          aria-pressed={speech.isListening}
          aria-label={speech.isListening ? "Stop voice input" : "Start voice input"}
          disabled={disabled}
          onClick={speech.isListening ? speech.stopListening : speech.startListening}
        >
          {speech.isListening ? "Stop mic" : "Mic"}
        </button>
      )}
      {"speechSynthesis" in window && (
        <button
          type="button"
          className="secondary"
          aria-pressed={speech.audioEnabled}
          aria-label={speech.audioEnabled ? "Turn spoken tutor prompts off" : "Turn spoken tutor prompts on"}
          onClick={speech.toggleAudio}
        >
          {speech.audioEnabled ? "Audio on" : "Audio off"}
        </button>
      )}
      {speech.error && <span className="muted small" role="status">{speech.error}</span>}
    </div>
  );
}
