import React from 'react'
import { Sparkles, Home, ShoppingBag, CheckCircle, Bell, Flame } from 'lucide-react'

interface DemoChipsProps {
  onSelectPrompt: (prompt: string) => void
  disabled?: boolean
}

export const DemoChips: React.FC<DemoChipsProps> = ({ onSelectPrompt, disabled = false }) => {
  const chips = [
    {
      label: 'Prep home for parents & low-sodium items',
      prompt: 'Prep home for parents and find low-sodium items',
      icon: Flame,
      color: 'border-cyan-500/30 text-cyan-300 hover:bg-cyan-950/40',
      badge: 'Multi-Domain',
    },
    {
      label: 'Set warm ambient lighting',
      prompt: 'Set living room lights to warm ambient',
      icon: Home,
      color: 'border-amber-500/30 text-amber-300 hover:bg-amber-950/40',
      badge: 'Smart Home',
    },
    {
      label: 'Search ayurvedic wellness catalog',
      prompt: 'Search ayurvedic wellness products for knee care',
      icon: ShoppingBag,
      color: 'border-emerald-500/30 text-emerald-300 hover:bg-emerald-950/40',
      badge: 'Commerce',
    },
    {
      label: '1-Click Checkout products',
      prompt: 'checkout product 1 and product 2',
      icon: CheckCircle,
      color: 'border-purple-500/30 text-purple-300 hover:bg-purple-950/40',
      badge: 'Instant Buy',
    },
    {
      label: 'Simulate doorbell guest',
      prompt: 'Check front door ring camera for visitors',
      icon: Bell,
      color: 'border-sky-500/30 text-sky-300 hover:bg-sky-950/40',
      badge: 'Ring Security',
    },
  ]

  return (
    <div className="w-full max-w-5xl mx-auto mt-4">
      <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-slate-400 uppercase tracking-wider px-1">
        <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
        <span>Hackathon Quick-Demo Chips</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {chips.map((chip, idx) => {
          const IconComponent = chip.icon
          return (
            <button
              key={idx}
              onClick={() => onSelectPrompt(chip.prompt)}
              disabled={disabled}
              className={`glass-card flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium transition-all ${chip.color} disabled:opacity-40 disabled:pointer-events-none hover:scale-[1.02] active:scale-[0.98] shadow-sm`}
            >
              <IconComponent className="w-3.5 h-3.5 shrink-0" />
              <span>{chip.label}</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-white/10 text-slate-300 font-mono">
                {chip.badge}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
