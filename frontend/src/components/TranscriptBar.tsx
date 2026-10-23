import React, { useState } from 'react'
import { Send, Sparkles, User } from 'lucide-react'

interface TranscriptBarProps {
  lastUserSpeech?: string
  lastAssistantSpeech?: string
  onSubmitText: (text: string) => void
  isLoading?: boolean
}

export const TranscriptBar: React.FC<TranscriptBarProps> = ({
  lastUserSpeech,
  lastAssistantSpeech,
  onSubmitText,
  isLoading = false,
}) => {
  const [inputText, setInputText] = useState('')

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputText.trim() || isLoading) return
    onSubmitText(inputText.trim())
    setInputText('')
  }

  return (
    <div className="w-full max-w-4xl mx-auto space-y-3">
      {/* Active Dialogue Bubbles */}
      <div className="space-y-2">
        {lastUserSpeech && (
          <div className="flex items-start gap-2.5 justify-end">
            <div className="glass-panel px-4 py-2.5 rounded-2xl rounded-tr-sm max-w-xl text-sm text-slate-100 bg-sky-950/40 border-sky-500/20 shadow-md">
              <span className="font-semibold text-xs text-cyan-400 block mb-0.5">You</span>
              {lastUserSpeech}
            </div>
            <div className="w-7 h-7 rounded-full bg-cyan-900/60 border border-cyan-400/30 flex items-center justify-center shrink-0">
              <User className="w-4 h-4 text-cyan-300" />
            </div>
          </div>
        )}

        {lastAssistantSpeech && (
          <div className="flex items-start gap-2.5 justify-start">
            <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-sky-600 to-cyan-400 border border-white/20 flex items-center justify-center shrink-0 shadow-md">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div className="glass-panel px-4 py-3 rounded-2xl rounded-tl-sm max-w-2xl text-sm text-slate-100 border-white/10 shadow-lg leading-relaxed">
              <span className="font-semibold text-xs text-sky-400 block mb-0.5 flex items-center gap-1">
                <span>Alexa+ OmniPulse</span>
                {isLoading && <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />}
              </span>
              {lastAssistantSpeech}
            </div>
          </div>
        )}
      </div>

      {/* Manual Input Bar */}
      <form onSubmit={handleFormSubmit} className="relative flex items-center">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Speak or type a command (e.g. 'Prep home for parents and find low-sodium items')..."
          disabled={isLoading}
          className="glass-input w-full px-5 py-3 pr-12 rounded-full text-sm placeholder:text-slate-500 shadow-inner"
        />
        <button
          type="submit"
          disabled={!inputText.trim() || isLoading}
          className="absolute right-2 p-2 rounded-full bg-cyan-500 hover:bg-cyan-400 text-slate-950 disabled:opacity-40 disabled:hover:bg-cyan-500 transition-colors shadow-md"
          title="Send command"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  )
}
