import React, { useState } from 'react'
import {
  Lightbulb,
  Thermometer,
  Bell,
  ArrowRight,
  Plus,
  Minus,
  Sparkles,
  CloudSun,
} from 'lucide-react'
import { mcpToolsCall, triggerRingWebhook } from '../api'

interface AmbientHomeWidgetsProps {
  currentTime?: string
  onRingEventTriggered: (res: any) => void
  onCommandTrigger: (prompt: string) => void
}

export const AmbientHomeWidgets: React.FC<AmbientHomeWidgetsProps> = ({
  currentTime = '03:24 PM',
  onRingEventTriggered,
  onCommandTrigger,
}) => {
  const [lightOn, setLightOn] = useState(true)
  const [temperature, setTemperature] = useState(72)
  const [, setIsUpdatingDevice] = useState(false)
  const [isTriggeringRing, setIsTriggeringRing] = useState(false)

  const handleToggleLight = async () => {
    const nextState = !lightOn
    setLightOn(nextState)
    setIsUpdatingDevice(true)
    try {
      await mcpToolsCall('update_smarthome_state', {
        device_id: 'living_room_light',
        device_type: 'light',
        state: { on: nextState, brightness: nextState ? 65 : 0, color: 'warm' },
      })
    } catch (e) { console.warn('MCP Light toggle sync:', e) }
    finally { setIsUpdatingDevice(false) }
  }

  const handleAdjustTemp = async (delta: number) => {
    const nextTemp = temperature + delta
    setTemperature(nextTemp)
    try {
      await mcpToolsCall('update_smarthome_state', {
        device_id: 'thermostat',
        device_type: 'thermostat',
        state: { temperature: nextTemp, mode: 'heat' },
      })
    } catch (e) { console.warn('MCP Temp sync:', e) }
  }

  const handleSimulateVisitor = async () => {
    setIsTriggeringRing(true)
    try {
      const res = await triggerRingWebhook('guest_arrival', 'Parents arrived at front door for visit')
      onRingEventTriggered(res)
    } catch (e) { console.error('Failed to trigger simulated visitor:', e) }
    finally { setIsTriggeringRing(false) }
  }

  return (
    <div className="w-full max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-4 my-auto items-center">

      {/* LEFT: Time + Family Note */}
      <div className="lg:col-span-5 flex flex-col gap-3">
        <div className="px-1">
          <div
            className="text-5xl sm:text-6xl font-light tracking-tight leading-none"
            style={{ color: 'var(--text-primary)' }}
          >
            {currentTime}
          </div>
          <div className="flex items-center gap-2 mt-1.5 text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
            <span>Friday, October 23</span>
            <span style={{ color: 'var(--text-dim)' }}>·</span>
            <span className="flex items-center gap-1" style={{ color: 'var(--warning)' }}>
              <CloudSun className="w-3.5 h-3.5" />
              72°F Sunny
            </span>
          </div>
        </div>

        {/* Family Note Card */}
        <div className="glass-surface rounded-2xl p-4 flex flex-col gap-2">
          <div className="flex items-center gap-1.5 text-xs font-semibold" style={{ color: 'var(--accent)' }}>
            <Sparkles className="w-3.5 h-3.5" />
            Visiting Family Priority
          </div>
          <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
            Parents arrive tomorrow. Dad's knee care &amp; low-sodium Ayurvedic menu are queued.
          </p>
          <div
            className="pt-2 mt-1 flex items-center justify-between"
            style={{ borderTop: '1px solid var(--glass-border)' }}
          >
            <span className="text-[11px] font-medium" style={{ color: 'var(--text-muted)' }}>
              Home Comfort Protocol
            </span>
            <button
              onClick={() => onCommandTrigger('Prep home for parents and find low-sodium items')}
              className="glass-chip px-2.5 py-1 rounded-full text-[11px] font-semibold flex items-center gap-1 cursor-pointer"
              style={{ color: 'var(--text-primary)' }}
            >
              Prepare Home
              <ArrowRight className="w-3 h-3" style={{ color: 'var(--accent)' }} />
            </button>
          </div>
        </div>
      </div>

      {/* CENTER: Ring Camera */}
      <div className="lg:col-span-4 rounded-2xl overflow-hidden relative h-[220px] flex flex-col justify-between p-3.5 group" style={{ border: '1px solid var(--glass-border)' }}>
        <img
          src="https://images.unsplash.com/photo-1513694203232-719a280e022f?w=900&auto=format&fit=crop&q=85"
          alt="Front Porch Camera"
          className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-black/30" />

        <div className="relative z-10 flex items-center justify-between">
          <div className="glass-chip px-2.5 py-1 rounded-full text-[11px] font-medium flex items-center gap-1.5" style={{ color: 'var(--text-primary)' }}>
            <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: 'var(--live-dot)' }} />
            Front Porch · Live
          </div>
          <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: 'rgba(0,0,0,0.5)', color: 'var(--text-muted)' }}>
            1080P
          </span>
        </div>

        <div className="relative z-10 flex items-end justify-between gap-2">
          <div>
            <div className="text-xs font-semibold drop-shadow" style={{ color: 'var(--text-primary)' }}>Armed &amp; Guarding</div>
            <div className="text-[10px] drop-shadow" style={{ color: 'var(--text-muted)' }}>Smart Doorbell Synced</div>
          </div>
          <button
            onClick={handleSimulateVisitor}
            disabled={isTriggeringRing}
            className="glass-chip px-2.5 py-1 rounded-full text-[11px] font-semibold flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
            style={{ color: 'var(--text-primary)' }}
          >
            <Bell className="w-3 h-3" style={{ color: 'var(--warning)' }} />
            {isTriggeringRing ? 'Ringing...' : 'Simulate Visitor'}
          </button>
        </div>
      </div>

      {/* RIGHT: Smart Home Tiles */}
      <div className="lg:col-span-3 flex flex-col gap-2.5 h-[220px]">
        {/* Light Tile */}
        <div
          onClick={handleToggleLight}
          className="glass-surface rounded-2xl p-3 flex flex-col justify-between flex-1 cursor-pointer"
          style={lightOn ? {
            background: 'var(--warning-muted)',
            borderColor: 'rgba(251, 191, 36, 0.3)',
          } : undefined}
        >
          <div className="flex items-center justify-between">
            <div
              className="p-1.5 rounded-xl transition-colors"
              style={lightOn ? { background: 'var(--warning)', color: 'var(--surface-base)' } : { background: 'var(--surface-elevated)', color: 'var(--text-muted)' }}
            >
              <Lightbulb className="w-4 h-4" />
            </div>
            <div
              className="w-10 h-5 rounded-full p-0.5 flex items-center transition-colors"
              style={lightOn ? { background: 'var(--warning)', justifyContent: 'flex-end' } : { background: 'var(--surface-elevated)', justifyContent: 'flex-start' }}
            >
              <div className="w-4 h-4 rounded-full bg-white shadow transition-transform" style={lightOn ? {} : { opacity: 0.7 }} />
            </div>
          </div>
          <div>
            <h4 className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>Living Room</h4>
            <div className="flex items-center justify-between text-[11px] font-medium" style={{ color: lightOn ? 'var(--warning)' : 'var(--text-muted)' }}>
              <span>{lightOn ? 'Warm Relax' : 'Off'}</span>
              <span>{lightOn ? '65% · 2700K' : 'Standby'}</span>
            </div>
          </div>
        </div>

        {/* Climate Tile */}
        <div className="glass-surface rounded-2xl p-3 flex flex-col justify-between flex-1">
          <div className="flex items-center justify-between">
            <div className="p-1.5 rounded-xl" style={{ background: 'var(--accent-muted)', color: 'var(--accent)' }}>
              <Thermometer className="w-4 h-4" />
            </div>
            <div className="flex items-center gap-0.5 p-0.5 rounded-full" style={{ background: 'var(--surface-elevated)' }}>
              <button
                onClick={(e) => { e.stopPropagation(); handleAdjustTemp(-1) }}
                className="w-5 h-5 rounded-full flex items-center justify-center transition-colors cursor-pointer"
                style={{ color: 'var(--text-primary)' }}
              >
                <Minus className="w-3 h-3" />
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); handleAdjustTemp(1) }}
                className="w-5 h-5 rounded-full flex items-center justify-center transition-colors cursor-pointer"
                style={{ color: 'var(--text-primary)' }}
              >
                <Plus className="w-3 h-3" />
              </button>
            </div>
          </div>
          <div className="flex items-end justify-between">
            <div>
              <h4 className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>Indoor Climate</h4>
              <p className="text-[11px] font-medium" style={{ color: 'var(--text-muted)' }}>Heat Active</p>
            </div>
            <div className="text-2xl font-light tracking-tight leading-none" style={{ color: 'var(--text-primary)' }}>
              {temperature}°<span className="text-xs font-normal" style={{ color: 'var(--text-muted)' }}>F</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
