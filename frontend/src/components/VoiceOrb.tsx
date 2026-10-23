import React from 'react'
import { Mic, MicOff, Volume2, Sparkles } from 'lucide-react'

interface VoiceOrbProps {
  isListening: boolean
  isSpeaking: boolean
  onClick: () => void
  disabled?: boolean
}

export const VoiceOrb: React.FC<VoiceOrbProps> = ({
  isListening,
  isSpeaking,
  onClick,
  disabled = false,
}) => {
  return (
    <div className="flex flex-col items-center justify-center relative my-2">
      {/* Expanding Ripple Rings when Listening */}
      {isListening && (
        <>
          <div className="orb-ripple w-36 h-36 -z-10" />
          <div
            className="orb-ripple w-48 h-48 -z-10"
            style={{ animationDelay: '0.8s' }}
          />
          <div
            className="orb-ripple w-60 h-60 -z-10"
            style={{ animationDelay: '1.6s' }}
          />
        </>
      )}

      {/* Main Interactive Orb Button */}
      <button
        onClick={onClick}
        disabled={disabled}
        title={isListening ? 'Listening... click to stop' : 'Click to talk to Alexa+'}
        style={{
          width: '84px',
          height: '84px',
          borderRadius: '9999px',
          background: isListening
            ? 'radial-gradient(circle at 35% 35%, #67e8f9 0%, #00d2ff 45%, #0284c7 85%, #0369a1 100%)'
            : isSpeaking
            ? 'radial-gradient(circle at 35% 35%, #a7f3d0 0%, #10b981 50%, #047857 100%)'
            : 'radial-gradient(circle at 35% 35%, #38bdf8 0%, #0284c7 50%, #0f172a 100%)',
          boxShadow: isListening
            ? '0 0 35px rgba(0, 210, 255, 0.9), 0 0 70px rgba(14, 165, 233, 0.5), inset 0 0 15px rgba(255, 255, 255, 0.8)'
            : isSpeaking
            ? '0 0 30px rgba(16, 185, 129, 0.7), inset 0 0 15px rgba(255, 255, 255, 0.6)'
            : '0 0 20px rgba(2, 132, 199, 0.4), inset 0 0 10px rgba(255, 255, 255, 0.3)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          cursor: disabled ? 'not-allowed' : 'pointer',
          border: '2px solid rgba(255, 255, 255, 0.25)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
        }}
        className={`group ${isListening ? 'animate-orb-listening' : 'hover:scale-105'}`}
      >
        {isListening ? (
          <Mic className="w-8 h-8 text-white drop-shadow-md animate-pulse" />
        ) : isSpeaking ? (
          <Volume2 className="w-8 h-8 text-white drop-shadow-md animate-bounce" />
        ) : (
          <Sparkles className="w-8 h-8 text-white/90 group-hover:rotate-12 transition-transform duration-300" />
        )}
      </button>

      {/* State Badge */}
      <div className="mt-3 flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium tracking-wide bg-slate-900/80 border border-white/10 shadow-sm">
        <span
          className={`w-2 h-2 rounded-full ${
            isListening
              ? 'bg-cyan-400 animate-ping'
              : isSpeaking
              ? 'bg-emerald-400 animate-pulse'
              : 'bg-sky-500'
          }`}
        />
        <span className="text-slate-300">
          {isListening
            ? 'Listening to you...'
            : isSpeaking
            ? 'Alexa+ Speaking'
            : 'Alexa+ Ready'}
        </span>
      </div>
    </div>
  )
}
