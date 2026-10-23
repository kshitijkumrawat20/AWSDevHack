import React, { useState, useEffect, useCallback } from 'react'
import {
  Sparkles,
  Volume2,
  VolumeX,
  Clock,
  Terminal,
  Activity,
  Shield,
  Layers,
} from 'lucide-react'
import { VoiceOrb } from './components/VoiceOrb'
import { TranscriptBar } from './components/TranscriptBar'
import { RichMediaCanvas } from './components/RichMediaCanvas'
import { McpInspector } from './components/McpInspector'
import { DemoChips } from './components/DemoChips'
import { RingTriggerButton } from './components/RingTriggerButton'
import { useVoice } from './hooks/useVoice'
import { sendChat, subscribeToEvents } from './api'
import { UICard, MCPInspectorPayload } from './types'

export function App() {
  const [cards, setCards] = useState<UICard[]>([])
  const [lastUserSpeech, setLastUserSpeech] = useState<string>('')
  const [lastAssistantSpeech, setLastAssistantSpeech] = useState<string>(
    'Hello! I am Alexa+ OmniPulse. I can manage your smart home, prepare for visiting guests, and recommend personalized wellness products.'
  )
  const [isLoading, setIsLoading] = useState(false)
  const [inspectorOpen, setInspectorOpen] = useState(false)
  const [inspectorLogs, setInspectorLogs] = useState<MCPInspectorPayload[]>([])
  const [currentTime, setCurrentTime] = useState<string>('')

  // Live clock for Echo Show 15 interface
  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      setCurrentTime(
        now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      )
    }
    updateTime()
    const timer = setInterval(updateTime, 1000)
    return () => clearInterval(timer)
  }, [])

  // Execute chat orchestration
  const handleSendMessage = useCallback(
    async (messageText: string) => {
      if (!messageText || isLoading) return

      setIsLoading(true)
      setLastUserSpeech(messageText)

      try {
        const res = await sendChat(messageText, 'default')

        setLastAssistantSpeech(res.speech)
        if (res.cards && res.cards.length > 0) {
          // Prepend or replace cards for dynamic canvas experience
          setCards(res.cards)
        }

        // Voice output via TTS
        speak(res.speech)

        // Log tool calls to MCP Inspector
        if (res.tool_calls && res.tool_calls.length > 0) {
          const timestamp = new Date().toLocaleTimeString()
          const newLogs: MCPInspectorPayload[] = res.tool_calls.map((tc) => ({
            timestamp,
            direction: 'response',
            method: `tools/call: ${tc.name}`,
            payload: { tool: tc.name, arguments: tc.arguments, result: tc.result },
            latencyMs: 15,
          }))
          setInspectorLogs(newLogs)
        }
      } catch (err: any) {
        console.error('Chat orchestration error:', err)
        const errMsg = 'Sorry, I encountered an error connecting to the backend.'
        setLastAssistantSpeech(errMsg)
        speak(errMsg)
      } finally {
        setIsLoading(false)
      }
    },
    [isLoading]
  )

  // Voice Hook
  const {
    isListening,
    isSpeaking,
    ttsEnabled,
    setTtsEnabled,
    toggleListening,
    speak,
  } = useVoice({
    onFinalTranscript: (text) => {
      handleSendMessage(text)
    },
  })

  // Subscribe to proactive Ring doorbell alerts via Server-Sent Events (/events)
  useEffect(() => {
    const unsubscribe = subscribeToEvents((eventData) => {
      console.log('SSE proactive Ring alert received:', eventData)
      if (eventData.ring_alert_card) {
        setCards((prev) => [eventData.ring_alert_card, ...prev])
      }
      if (eventData.speech) {
        setLastAssistantSpeech(eventData.speech)
        speak(eventData.speech)
      }
    })

    return () => {
      unsubscribe()
    }
  }, [speak])

  // Handle 1-Click Buy button from product carousel
  const handleBuyProduct = (productId: number, productName: string) => {
    handleSendMessage(`checkout product ${productId}`)
  }

  return (
    <div className="min-h-screen flex flex-col justify-between p-4 sm:p-6 lg:p-8 max-w-[1600px] mx-auto relative select-none">
      {/* Top Navigation & Status Bar */}
      <header className="glass-panel w-full rounded-2xl px-6 py-3.5 flex items-center justify-between mb-4 shadow-lg border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center shadow-md shadow-cyan-900/40 border border-white/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-extrabold tracking-tight text-slate-100 flex items-center gap-1.5">
                <span>Alexa+</span>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-sky-400">
                  OmniPulse
                </span>
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                Echo Show 15 Simulator
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Autonomous Context-Aware Ambient Orchestrator | MCP 2025-11-25
            </p>
          </div>
        </div>

        {/* Right Status Controls */}
        <div className="flex items-center gap-3">
          {/* Live Clock */}
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900/60 border border-white/5 text-xs font-mono text-slate-300">
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            <span>{currentTime || '12:00 PM'}</span>
          </div>

          {/* Voice Output (TTS) Toggle */}
          <button
            onClick={() => setTtsEnabled(!ttsEnabled)}
            className={`p-2 rounded-xl border text-xs font-medium flex items-center gap-1.5 transition-all ${
              ttsEnabled
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/20'
                : 'bg-slate-800/50 border-white/10 text-slate-400 hover:text-slate-200'
            }`}
            title={ttsEnabled ? 'Voice output (TTS) ON' : 'Voice output (TTS) MUTED'}
          >
            {ttsEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
            <span className="hidden md:inline">{ttsEnabled ? 'TTS Audio' : 'Muted'}</span>
          </button>

          {/* Simulate Ring Doorbell Event */}
          <RingTriggerButton
            onEventTriggered={(res) => {
              if (res.ring_alert_card) {
                setCards((prev) => [res.ring_alert_card, ...prev])
              }
              if (res.speech) {
                setLastAssistantSpeech(res.speech)
                speak(res.speech)
              }
            }}
          />

          {/* MCP Inspector Toggle Button */}
          <button
            onClick={() => setInspectorOpen(!inspectorOpen)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md transition-all active:scale-95"
            title="Inspect Live MCP Protocol Streams"
          >
            <Terminal className="w-4 h-4" />
            <span className="hidden sm:inline">MCP Inspector</span>
          </button>
        </div>
      </header>

      {/* Main Interactive Stage */}
      <main className="flex-1 flex flex-col justify-start items-center relative z-10 w-full py-2">
        {/* Animated Alexa+ Voice Orb */}
        <VoiceOrb
          isListening={isListening}
          isSpeaking={isSpeaking}
          onClick={toggleListening}
        />

        {/* Live Conversational Transcript Bar */}
        <div className="w-full mt-3">
          <TranscriptBar
            lastUserSpeech={lastUserSpeech}
            lastAssistantSpeech={lastAssistantSpeech}
            onSubmitText={handleSendMessage}
            isLoading={isLoading}
          />
        </div>

        {/* Dynamic Rich Media Canvas (Carousels, Smart Home Cards, Ring Alerts) */}
        <div className="w-full">
          <RichMediaCanvas cards={cards} onBuyProduct={handleBuyProduct} />
        </div>
      </main>

      {/* Bottom Footer with Quick Demo Chips */}
      <footer className="w-full mt-auto pt-2 z-10">
        <DemoChips onSelectPrompt={handleSendMessage} disabled={isLoading} />
        <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono mt-3 px-2 border-t border-white/5 pt-2">
          <span>Backend: http://localhost:8000 | SQLite: omnipulse.db</span>
          <span>Amazon Developer Hackathon | Team OmniPulse</span>
        </div>
      </footer>

      {/* Collapsible MCP Protocol Inspector Drawer */}
      <McpInspector
        isOpen={inspectorOpen}
        onToggle={() => setInspectorOpen(!inspectorOpen)}
        externalLogs={inspectorLogs}
      />
    </div>
  )
}

export default App
