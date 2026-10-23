import React from 'react'
import { Mic, Volume2, Sparkles } from 'lucide-react'

interface VoiceOrbProps {
  isListening: boolean
  isSpeaking: boolean
  onClick: () => void
  disabled?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export const VoiceOrb: React.FC<VoiceOrbProps> = ({
  isListening,
  isSpeaking,
  onClick,
  disabled = false,
  size = 'sm',
}) => {
  const dim = size === 'sm' ? 42 : 64

  return (
    <div className="relative flex items-center justify-center shrink-0">
      {/* Ripple ring when listening */}
      {isListening && (
        <div
          className="absolute rounded-full animate-ping -z-10"
          style={{
            inset: '-6px',
            border: '1px solid var(--accent)',
            opacity: 0.4,
            animationDuration: '2.2s',
          }}
        />
      )}

      <button
        onClick={onClick}
        disabled={disabled}
        title={isListening ? 'Listening — tap to stop' : 'Tap to speak'}
        className={`group transition-transform cursor-pointer ${isListening ? 'animate-orb-listening' : 'hover:scale-105'} active:scale-90`}
        style={{
          width: dim,
          height: dim,
          borderRadius: 'var(--radius-full)',
          background: isListening
            ? 'linear-gradient(135deg, var(--accent), #0891B2)'
            : isSpeaking
            ? 'linear-gradient(135deg, var(--success), #059669)'
            : 'linear-gradient(135deg, #0EA5E9, #0369A1)',
          boxShadow: isListening
            ? '0 0 24px var(--accent-glow)'
            : isSpeaking
            ? '0 0 20px rgba(52, 211, 153, 0.35)'
            : '0 0 12px rgba(14, 165, 233, 0.25)',
          border: '1px solid rgba(255,255,255,0.2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: disabled ? 'not-allowed' : 'pointer',
        }}
      >
        {isListening ? (
          <Mic className="w-5 h-5 animate-pulse" style={{ color: 'var(--surface-base)' }} />
        ) : isSpeaking ? (
          <Volume2 className="w-5 h-5" style={{ color: 'white' }} />
        ) : (
          <Sparkles className="w-5 h-5 group-hover:rotate-12 transition-transform" style={{ color: 'white' }} />
        )}
      </button>

      {/* Mini wave bars */}
      {(isListening || isSpeaking) && (
        <div className="absolute -bottom-1 flex items-center gap-px pointer-events-none">
          <span className="wave-bar" style={{ animationDelay: '0.1s', height: '8px' }} />
          <span className="wave-bar" style={{ animationDelay: '0.3s', height: '12px' }} />
          <span className="wave-bar" style={{ animationDelay: '0.2s', height: '8px' }} />
        </div>
      )}
    </div>
  )
}
