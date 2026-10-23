import React, { useState } from 'react'
import { Bell, UserCheck, Package, ChevronDown } from 'lucide-react'
import { triggerRingWebhook } from '../api'

interface RingTriggerButtonProps {
  onEventTriggered?: (res: any) => void
  disabled?: boolean
}

export const RingTriggerButton: React.FC<RingTriggerButtonProps> = ({
  onEventTriggered,
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [isTriggering, setIsTriggering] = useState(false)

  const handleTrigger = async (
    type: 'guest_arrival' | 'package_delivery',
    desc: string
  ) => {
    setIsTriggering(true)
    setIsOpen(false)
    try {
      const res = await triggerRingWebhook(type, desc)
      if (onEventTriggered) {
        onEventTriggered(res)
      }
    } catch (err) {
      console.error('Failed to trigger simulated Ring event', err)
    } finally {
      setIsTriggering(false)
    }
  }

  return (
    <div className="relative inline-block text-left">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || isTriggering}
        className="glass-card flex items-center gap-2 px-3.5 py-2 rounded-2xl border-amber-500/30 text-amber-300 hover:bg-amber-950/40 text-xs font-semibold shadow-md transition-all active:scale-95 disabled:opacity-50"
      >
        <Bell className="w-4 h-4 text-amber-400 animate-bounce" />
        <span>Simulate Ring Event</span>
        <ChevronDown className="w-3.5 h-3.5 opacity-70" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 rounded-2xl glass-panel p-2 shadow-2xl z-50 border border-white/10 animate-in fade-in zoom-in-95 duration-150">
          <div className="px-3 py-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Simulate Doorbell Event
          </div>
          <button
            onClick={() =>
              handleTrigger(
                'guest_arrival',
                'Parents arrived at front door for visit'
              )
            }
            className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl hover:bg-emerald-500/10 text-left text-xs text-slate-200 hover:text-emerald-300 transition-colors"
          >
            <UserCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <div>
              <div className="font-semibold">Guest Arrival (Parents)</div>
              <div className="text-[10px] text-slate-400">
                Cross-checks memory & unlocks door
              </div>
            </div>
          </button>

          <button
            onClick={() =>
              handleTrigger(
                'package_delivery',
                'Amazon package left at doorstep'
              )
            }
            className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl hover:bg-cyan-500/10 text-left text-xs text-slate-200 hover:text-cyan-300 transition-colors mt-1"
          >
            <Package className="w-4 h-4 text-cyan-400 shrink-0" />
            <div>
              <div className="font-semibold">Package Delivery</div>
              <div className="text-[10px] text-slate-400">
                Confirms package arrival & logs
              </div>
            </div>
          </button>
        </div>
      )}
    </div>
  )
}
