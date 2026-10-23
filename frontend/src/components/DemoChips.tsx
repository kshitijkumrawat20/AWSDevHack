import React from 'react'

interface DemoChipsProps {
  onSelectPrompt: (prompt: string) => void
  disabled?: boolean
}

export const DemoChips: React.FC<DemoChipsProps> = ({ onSelectPrompt, disabled = false }) => {
  const scenarios = [
    { label: 'Prep for Parents', prompt: 'Prep home for parents and find low-sodium items' },
    { label: 'Ring: Guest Arrival', prompt: 'Check front door ring camera for visitors' },
    { label: 'Knee Pain Relief', prompt: 'Search ayurvedic wellness products for knee care' },
    { label: 'Warm 2700K Lights', prompt: 'Set living room lights to warm ambient' },
    { label: '1-Click Checkout', prompt: 'checkout product 1 and product 5' },
  ]

  return (
    <div className="flex flex-wrap items-center justify-center gap-1.5 py-0.5 max-w-3xl mx-auto">
      {scenarios.map((s, i) => (
        <button
          key={i}
          onClick={() => onSelectPrompt(s.prompt)}
          disabled={disabled}
          className="glass-chip px-3 py-1 rounded-full text-xs font-medium disabled:opacity-40"
          style={{ color: 'var(--text-secondary)' }}
        >
          {s.label}
        </button>
      ))}
    </div>
  )
}
