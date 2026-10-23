import React from 'react'
import { Sparkles, Volume2, Mic, X } from 'lucide-react'

interface ConversationalDialogueProps {
  lastUserSpeech?: string
  lastAssistantSpeech?: string
  isLoading?: boolean
  isListening?: boolean
  isSpeaking?: boolean
  onClearSpeech?: () => void
}

export const ConversationalDialogue: React.FC<ConversationalDialogueProps> = ({
  lastUserSpeech,
  lastAssistantSpeech,
  isLoading = false,
  isListening = false,
  isSpeaking = false,
  onClearSpeech,
}) => {
  if (!lastAssistantSpeech && !lastUserSpeech && !isLoading && !isListening) {
    return null
  }

  return (
    <div
      className="glass-surface w-full max-w-3xl mx-auto rounded-2xl p-3.5 transition-all duration-300"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className="p-1.5 rounded-lg"
            style={{ background: 'var(--accent-muted)', color: 'var(--accent)' }}
          >
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <span className="text-xs font-semibold" style={{ color: 'var(--accent)' }}>
            Alexa+ OmniPulse
          </span>
        </div>

        <div className="flex items-center gap-2">
          {isLoading && (
            <span
              className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium"
              style={{ background: 'var(--accent-muted)', color: 'var(--accent)' }}
            >
              <span className="w-1.5 h-1.5 rounded-full animate-ping" style={{ background: 'var(--accent)' }} />
              Processing...
            </span>
          )}
          {isSpeaking && !isLoading && (
            <span
              className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium"
              style={{ background: 'var(--success-muted)', color: 'var(--success)' }}
            >
              <Volume2 className="w-3 h-3 animate-pulse" />
              Speaking
            </span>
          )}
          {isListening && !isLoading && (
            <span
              className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium"
              style={{ background: 'var(--accent-muted)', color: 'var(--accent)' }}
            >
              <Mic className="w-3 h-3 animate-pulse" />
              Listening
            </span>
          )}
          {onClearSpeech && (
            <button
              onClick={onClearSpeech}
              className="p-1 rounded-full transition-colors cursor-pointer"
              style={{ color: 'var(--text-muted)' }}
              title="Dismiss"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* User turn */}
      {lastUserSpeech && (
        <div className="mt-2.5 pt-2 flex items-start gap-2 text-xs" style={{ borderTop: '1px solid var(--glass-border)' }}>
          <span
            className="shrink-0 px-1.5 py-0.5 rounded text-[10px] font-semibold"
            style={{ background: 'var(--surface-elevated)', color: 'var(--text-muted)' }}
          >
            You
          </span>
          <span className="italic" style={{ color: 'var(--text-secondary)' }}>
            "{lastUserSpeech}"
          </span>
        </div>
      )}

      {/* Assistant response */}
      <p className="mt-2 text-[13px] leading-relaxed select-text" style={{ color: 'var(--text-primary)' }}>
        {isLoading
          ? 'Synthesizing context across household memory, smart home devices, and wellness catalog...'
          : lastAssistantSpeech || 'Ready. Ask me anything or choose a scenario.'}
      </p>
    </div>
  )
}
