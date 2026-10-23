import React, { useState, useEffect, useCallback } from 'react'
import {
  Clock,
  CloudSun,
  Terminal,
  Volume2,
  VolumeX,
} from 'lucide-react'
import { AmbientHomeWidgets } from './components/AmbientHomeWidgets'
import { RichMediaCanvas } from './components/RichMediaCanvas'
import { DemoChips } from './components/DemoChips'
import { TranscriptBar } from './components/TranscriptBar'
import { ConversationalDialogue } from './components/ConversationalDialogue'
import { RingTriggerButton } from './components/RingTriggerButton'
import { McpInspector } from './components/McpInspector'
import { useVoice } from './hooks/useVoice'
import { sendChat, subscribeToEvents } from './api'
import { UICard, MCPInspectorPayload } from './types'

export function App() {
  const [cards, setCards] = useState<UICard[]>([])
  const [lastUserSpeech, setLastUserSpeech] = useState<string>('')
  const [lastAssistantSpeech, setLastAssistantSpeech] = useState<string>(
    'Hello! I\'m Alexa+ OmniPulse. Parents visiting tomorrow — context is active.'
  )
  const [isLoading, setIsLoading] = useState(false)
  const [inspectorOpen, setInspectorOpen] = useState(false)
  const [inspectorLogs, setInspectorLogs] = useState<MCPInspectorPayload[]>([])
  const [currentTime, setCurrentTime] = useState<string>('03:24 PM')

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

  const handleSendMessage = useCallback(
    async (messageText: string) => {
      if (!messageText || isLoading) return
      setIsLoading(true)
      setLastUserSpeech(messageText)
      try {
        const res = await sendChat(messageText, 'default')
        setLastAssistantSpeech(res.speech)
        if (res.cards && res.cards.length > 0) setCards(res.cards)
        speak(res.speech)
        if (res.tool_calls && res.tool_calls.length > 0) {
          const timestamp = new Date().toLocaleTimeString()
          const newLogs: MCPInspectorPayload[] = res.tool_calls.map((tc) => ({
            timestamp,
            direction: 'response',
            method: `tools/call: ${tc.name}`,
            payload: { tool: tc.name, arguments: tc.arguments, result: tc.result },
            latencyMs: 16,
          }))
          setInspectorLogs((prev) => [...newLogs, ...prev].slice(0, 30))
        }
      } catch (err: any) {
        console.error('Chat orchestration error:', err)
        const errMsg = 'Connection error with the backend agent.'
        setLastAssistantSpeech(errMsg)
        speak(errMsg)
      } finally {
        setIsLoading(false)
      }
    },
    [isLoading]
  )

  const { isListening, isSpeaking, ttsEnabled, setTtsEnabled, toggleListening, speak } = useVoice({
    onFinalTranscript: (text) => handleSendMessage(text),
  })

  useEffect(() => {
    const unsubscribe = subscribeToEvents((eventData) => {
      if (eventData.ring_alert_card) setCards((prev) => [eventData.ring_alert_card, ...prev])
      if (eventData.speech) {
        setLastAssistantSpeech(eventData.speech)
        speak(eventData.speech)
      }
    })
    return () => unsubscribe()
  }, [speak])

  const handleBuyProduct = (productId: number, _productName: string) => {
    handleSendMessage(`checkout product ${productId}`)
  }

  const handleRingEventTriggered = (res: any) => {
    if (res.ring_alert_card) setCards((prev) => [res.ring_alert_card, ...prev])
    if (res.speech) {
      setLastAssistantSpeech(res.speech)
      speak(res.speech)
    }
  }

  return (
    <div className="h-screen w-screen overflow-hidden bg-[var(--surface-base)] flex items-center justify-center select-none">
      {/* Inner display frame */}
      <div
        className="w-full h-full relative flex flex-col bg-cover bg-center"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=2000&q=85')`,
        }}
      >
        {/* Frosted overlay — single layer, consistent */}
        <div className="absolute inset-0 bg-[var(--surface-base)]/80 backdrop-blur-2xl" />

        {/* TOP STATUS BAR */}
        <header className="relative z-20 flex items-center justify-between h-12 px-5 shrink-0">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5 text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
              <Clock className="w-4 h-4" style={{ color: 'var(--accent)' }} />
              {currentTime}
            </div>
            <div className="w-px h-4 bg-[var(--glass-border)]" />
            <div className="flex items-center gap-1.5 text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
              <CloudSun className="w-3.5 h-3.5" style={{ color: 'var(--warning)' }} />
              72°F Seattle
            </div>
          </div>

          {/* Protocol badge */}
          <div className="hidden sm:flex glass-chip items-center gap-2 px-3 py-1 rounded-full text-xs" style={{ color: 'var(--text-secondary)' }}>
            <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: 'var(--success)' }} />
            MCP 2025-11-25 · Live
          </div>

          {/* Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setTtsEnabled(!ttsEnabled)}
              className="glass-chip p-2 rounded-full cursor-pointer"
              title={ttsEnabled ? 'Mute voice' : 'Unmute voice'}
              style={{ color: ttsEnabled ? 'var(--success)' : 'var(--text-muted)' }}
            >
              {ttsEnabled ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
            </button>
            <RingTriggerButton onEventTriggered={handleRingEventTriggered} />
            <button
              onClick={() => setInspectorOpen(true)}
              className="glass-chip flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium cursor-pointer"
              style={{ color: 'var(--text-secondary)' }}
              title="MCP Inspector"
            >
              <Terminal className="w-3.5 h-3.5" style={{ color: 'var(--accent)' }} />
              <span className="hidden sm:inline">Inspector</span>
              {inspectorLogs.length > 0 && (
                <span
                  className="w-4 h-4 rounded-full text-[10px] flex items-center justify-center font-bold"
                  style={{ background: 'var(--accent-muted)', color: 'var(--accent)' }}
                >
                  {inspectorLogs.length}
                </span>
              )}
            </button>
          </div>
        </header>

        {/* CENTER STAGE */}
        <main className="relative z-10 flex-1 min-h-0 flex flex-col justify-center items-center px-4 py-1 overflow-hidden">
          {cards.length === 0 ? (
            <AmbientHomeWidgets
              currentTime={currentTime}
              onRingEventTriggered={handleRingEventTriggered}
              onCommandTrigger={handleSendMessage}
            />
          ) : (
            <RichMediaCanvas
              cards={cards}
              onBuyProduct={handleBuyProduct}
              onBackToHome={() => setCards([])}
              lastAssistantSpeech={lastAssistantSpeech}
              lastUserSpeech={lastUserSpeech}
            />
          )}
        </main>

        {/* BOTTOM DOCK */}
        <footer className="relative z-20 w-full shrink-0 px-4 pb-4 pt-1 space-y-2">
          {cards.length === 0 && (
            <ConversationalDialogue
              lastUserSpeech={lastUserSpeech}
              lastAssistantSpeech={lastAssistantSpeech}
              isLoading={isLoading}
              isListening={isListening}
              isSpeaking={isSpeaking}
              onClearSpeech={() => { setLastAssistantSpeech(''); setLastUserSpeech('') }}
            />
          )}
          <DemoChips onSelectPrompt={handleSendMessage} disabled={isLoading} />
          <TranscriptBar
            onSubmitText={handleSendMessage}
            isLoading={isLoading}
            isListening={isListening}
            isSpeaking={isSpeaking}
            onToggleListening={toggleListening}
          />
        </footer>

        <McpInspector
          isOpen={inspectorOpen}
          onToggle={() => setInspectorOpen(!inspectorOpen)}
          externalLogs={inspectorLogs}
        />
      </div>
    </div>
  )
}

export default App
