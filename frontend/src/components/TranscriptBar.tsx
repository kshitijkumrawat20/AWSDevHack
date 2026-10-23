import React, { useState } from 'react'
import { Send } from 'lucide-react'
import { VoiceOrb } from './VoiceOrb'

interface TranscriptBarProps {
  lastUserSpeech?: string
  lastAssistantSpeech?: string
  onSubmitText: (text: string) => void
  isLoading?: boolean
  isListening: boolean
  isSpeaking: boolean
  onToggleListening: () => void
}

export const TranscriptBar: React.FC<TranscriptBarProps> = ({
  onSubmitText,
  isLoading = false,
  isListening,
  isSpeaking,
  onToggleListening,
}) => {
  const [inputText, setInputText] = useState('')

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputText.trim() || isLoading) return
    onSubmitText(inputText.trim())
    setInputText('')
  }

  return (
    <div className="glass-surface w-full max-w-3xl mx-auto rounded-full p-1.5 flex items-center gap-2.5">
      <div className="shrink-0 pl-0.5">
        <VoiceOrb
          size="sm"
          isListening={isListening}
          isSpeaking={isSpeaking}
          onClick={onToggleListening}
          disabled={isLoading}
        />
      </div>

      <form onSubmit={handleFormSubmit} className="flex-1 flex items-center gap-2 min-w-0">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder={
            isListening
              ? 'Listening...'
              : isLoading
              ? 'Processing...'
              : "Ask Alexa+ anything..."
          }
          disabled={isLoading || isListening}
          className="glass-input w-full rounded-full px-4 py-2 text-sm"
          style={{ color: 'var(--text-primary)' }}
        />
        <button
          type="submit"
          disabled={!inputText.trim() || isLoading}
          className="p-2.5 rounded-full font-semibold transition-all active:scale-95 shrink-0 cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
          style={{ background: 'var(--accent)', color: 'var(--surface-base)' }}
          title="Send"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  )
}
