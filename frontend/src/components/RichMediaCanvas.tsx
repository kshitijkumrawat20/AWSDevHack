import React from 'react'
import {
  UICard,
  CarouselCard,
  SmartHomeCard,
  RingAlertCard,
  CheckoutCard,
  MemoryCard,
  ProductItem,
  DeviceStateItem,
} from '../types'
import {
  ShoppingBag,
  Lightbulb,
  Thermometer,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Package,
  Heart,
  Sliders,
  DollarSign,
  ArrowRight,
} from 'lucide-react'

interface RichMediaCanvasProps {
  cards: UICard[]
  onBuyProduct?: (productId: number, productName: string) => void
}

export const RichMediaCanvas: React.FC<RichMediaCanvasProps> = ({ cards, onBuyProduct }) => {
  if (!cards || cards.length === 0) {
    return (
      <div className="glass-panel w-full max-w-5xl mx-auto rounded-3xl p-10 text-center my-6 border-dashed border-white/10">
        <div className="w-16 h-16 rounded-2xl bg-cyan-950/40 border border-cyan-500/20 flex items-center justify-center mx-auto mb-4 text-cyan-400">
          <Sliders className="w-8 h-8 opacity-70" />
        </div>
        <h3 className="text-lg font-semibold text-slate-200">Echo Show 15 Ambient Canvas</h3>
        <p className="text-sm text-slate-400 max-w-md mx-auto mt-1 leading-relaxed">
          Say a voice command or click any demo chip below. Context-aware Smart Home controls, Shoppable
          Carousels, and Ring alerts will materialize here.
        </p>
      </div>
    )
  }

  return (
    <div className="w-full max-w-5xl mx-auto my-6 space-y-6">
      {cards.map((card, idx) => {
        switch (card.type) {
          case 'carousel':
            return (
              <CarouselCardRenderer
                key={idx}
                card={card as CarouselCard}
                onBuyProduct={onBuyProduct}
              />
            )
          case 'smarthome_card':
            return <SmartHomeCardRenderer key={idx} card={card as SmartHomeCard} />
          case 'ring_alert_card':
            return <RingAlertCardRenderer key={idx} card={card as RingAlertCard} />
          case 'checkout_card':
            return <CheckoutCardRenderer key={idx} card={card as CheckoutCard} />
          case 'memory_card':
            return <MemoryCardRenderer key={idx} card={card as MemoryCard} />
          default:
            return null
        }
      })}
    </div>
  )
}

/** 1. Product Carousel Renderer with 1-Click Buy */
const CarouselCardRenderer: React.FC<{
  card: CarouselCard
  onBuyProduct?: (id: number, name: string) => void
}> = ({ card, onBuyProduct }) => {
  return (
    <div className="glass-panel p-6 rounded-3xl relative overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-emerald-950/50 border border-emerald-500/30 text-emerald-400">
            <ShoppingBag className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-base">{card.title || 'Shoppable Recommendations'}</h3>
            <span className="text-xs text-slate-400">Customized using household Ayurvedic memory</span>
          </div>
        </div>
        <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
          {card.products.length} Items Available
        </span>
      </div>

      {/* Horizontal Scrollable Product Track */}
      <div className="flex gap-4 overflow-x-auto pb-3 pt-1 scroll-smooth">
        {card.products.map((product: ProductItem) => (
          <div
            key={product.id}
            className="glass-card w-64 shrink-0 rounded-2xl p-4 flex flex-col justify-between group hover:border-emerald-500/40"
          >
            <div>
              {/* Product Image with Fallback */}
              <div className="w-full h-36 rounded-xl overflow-hidden bg-slate-900 border border-white/5 relative mb-3">
                <img
                  src={product.image_url}
                  alt={product.name}
                  loading="lazy"
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  onError={(e) => {
                    // Fallback to placeholder if external URL is blocked
                    ;(e.target as HTMLElement).style.display = 'none'
                  }}
                />
                <div className="absolute top-2 right-2 px-2 py-0.5 rounded-full bg-slate-900/80 backdrop-blur-md text-xs font-mono font-bold text-emerald-400 border border-emerald-500/30">
                  ${product.price.toFixed(2)}
                </div>
              </div>

              <h4 className="font-semibold text-slate-100 text-sm line-clamp-1 group-hover:text-cyan-300 transition-colors">
                {product.name}
              </h4>
              <p className="text-xs text-slate-400 line-clamp-2 mt-1 leading-relaxed">
                {product.description}
              </p>
            </div>

            {/* 1-Click Buy Button */}
            <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
              <span className="text-[11px] font-medium text-emerald-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                In Stock
              </span>
              <button
                onClick={() => onBuyProduct && onBuyProduct(product.id, product.name)}
                className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-950 transition-all active:scale-95"
              >
                <span>Buy Now</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/** 2. Smart Home State Card Renderer */
const SmartHomeCardRenderer: React.FC<{ card: SmartHomeCard }> = ({ card }) => {
  return (
    <div className="glass-panel p-6 rounded-3xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-amber-950/50 border border-amber-500/30 text-amber-400">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-base">{card.title || 'Smart Home Controls'}</h3>
            <span className="text-xs text-slate-400">Living Room & Climate Sync</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {card.devices.map((device: DeviceStateItem, idx: number) => {
          const isLight = device.device_type === 'light' || device.device_id.includes('light')
          return (
            <div
              key={idx}
              className="glass-card p-4 rounded-2xl flex items-center justify-between border-white/10"
            >
              <div className="flex items-center gap-3">
                <div
                  className={`p-3 rounded-xl border ${
                    isLight
                      ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                      : 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400'
                  }`}
                >
                  {isLight ? <Lightbulb className="w-6 h-6" /> : <Thermometer className="w-6 h-6" />}
                </div>
                <div>
                  <h4 className="font-semibold text-slate-200 text-sm capitalize">
                    {device.device_id.replace(/_/g, ' ')}
                  </h4>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    <span className="text-xs text-slate-400 font-mono">
                      {isLight
                        ? `Color: ${device.state.color || 'warm'} | Brightness: ${device.state.brightness ?? 60}%`
                        : `Target: ${device.state.temperature ?? 72}°F | Mode: ${device.state.mode || 'heat'}`}
                    </span>
                  </div>
                </div>
              </div>

              <div className="text-right">
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  {device.state.on !== false ? 'ACTIVE' : 'OFF'}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/** 3. Ring Alert Security Card Renderer */
const RingAlertCardRenderer: React.FC<{ card: RingAlertCard }> = ({ card }) => {
  const isVerified = card.verified
  return (
    <div
      className={`glass-panel p-6 rounded-3xl border-l-4 ${
        isVerified ? 'border-l-emerald-500' : 'border-l-amber-500'
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div
            className={`p-3 rounded-2xl border ${
              isVerified
                ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-400'
                : 'bg-amber-950/60 border-amber-500/40 text-amber-400'
            }`}
          >
            {isVerified ? <ShieldCheck className="w-7 h-7" /> : <AlertTriangle className="w-7 h-7" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-slate-100 text-base">{card.title || 'Ring Doorbell Security'}</h3>
              <span
                className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
                  isVerified
                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                    : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                }`}
              >
                {isVerified ? 'VERIFIED VISITOR' : 'UNVERIFIED ALERT'}
              </span>
            </div>
            <p className="text-sm text-slate-300 mt-1 leading-relaxed">{card.description}</p>
            {card.action_taken && (
              <p className="text-xs font-mono text-cyan-400 mt-2">
                Automated Action: {card.action_taken.replace(/_/g, ' ')}
              </p>
            )}
          </div>
        </div>

        <div className="text-xs font-mono text-slate-400 px-3 py-1 rounded-xl bg-slate-900/60 border border-white/5">
          Live Ring Feed
        </div>
      </div>
    </div>
  )
}

/** 4. Checkout Confirmation Card Renderer */
const CheckoutCardRenderer: React.FC<{ card: CheckoutCard }> = ({ card }) => {
  return (
    <div className="glass-panel p-6 rounded-3xl border-l-4 border-l-purple-500 bg-gradient-to-r from-purple-950/20 to-slate-900/40">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2.5 rounded-2xl bg-purple-950/60 border border-purple-500/40 text-purple-300">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-base">{card.title || '1-Click Instant Checkout'}</h3>
            <span className="text-xs text-purple-300 font-mono">Order ID: {card.orderId}</span>
          </div>
        </div>
        <div className="text-right">
          <span className="text-xs text-slate-400 block">Total Charged</span>
          <span className="text-xl font-bold font-mono text-emerald-400">${card.total.toFixed(2)}</span>
        </div>
      </div>

      <div className="glass-card p-4 rounded-2xl">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
          Items Ordered ({card.items.length})
        </span>
        <ul className="space-y-1.5">
          {card.items.map((item, idx) => (
            <li key={idx} className="text-sm text-slate-200 flex items-center gap-2">
              <Package className="w-4 h-4 text-purple-400 shrink-0" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

/** 5. Cross-Session Memory Card Renderer */
const MemoryCardRenderer: React.FC<{ card: MemoryCard }> = ({ card }) => {
  return (
    <div className="glass-panel p-6 rounded-3xl border-l-4 border-l-cyan-500">
      <div className="flex items-center gap-2.5 mb-3">
        <div className="p-2 rounded-xl bg-cyan-950/50 border border-cyan-500/30 text-cyan-400">
          <Heart className="w-5 h-5" />
        </div>
        <div>
          <h3 className="font-bold text-slate-100 text-base">Persistent Household Context</h3>
          <span className="text-xs text-slate-400 font-mono">Session ID: {card.session_id}</span>
        </div>
      </div>
      <p className="text-sm text-slate-200 leading-relaxed mb-3">{card.context}</p>
      <div className="flex flex-wrap gap-2 text-xs">
        {card.health_notes.map((hn, idx) => (
          <span
            key={idx}
            className="px-2.5 py-1 rounded-full bg-red-500/10 text-red-300 border border-red-500/20"
          >
            Health: {hn}
          </span>
        ))}
        {card.dietary_restrictions.map((diet, idx) => (
          <span
            key={idx}
            className="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
          >
            Diet: {diet}
          </span>
        ))}
      </div>
    </div>
  )
}
