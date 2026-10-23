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
  Sparkles,
  Lock,
  Unlock,
  Star,
  Copy,
} from 'lucide-react'
import { ArrowLeft } from 'lucide-react'

export const PRODUCT_IMAGES: Record<number, string> = {
  1: 'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=600&auto=format&fit=crop&q=80',
  2: 'https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=600&auto=format&fit=crop&q=80',
  3: 'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=600&auto=format&fit=crop&q=80',
  4: 'https://images.unsplash.com/photo-1518110925495-5fe2fda0442c?w=600&auto=format&fit=crop&q=80',
  5: 'https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&auto=format&fit=crop&q=80',
  6: 'https://images.unsplash.com/photo-1526947425960-945c6e72858f?w=600&auto=format&fit=crop&q=80',
}

interface RichMediaCanvasProps {
  cards: UICard[]
  onBuyProduct?: (productId: number, productName: string) => void
  onBackToHome?: () => void
  lastAssistantSpeech?: string
  lastUserSpeech?: string
}

export const RichMediaCanvas: React.FC<RichMediaCanvasProps> = ({
  cards,
  onBuyProduct,
  onBackToHome,
  lastAssistantSpeech,
  lastUserSpeech,
}) => {
  if (!cards || cards.length === 0) {
    return null
  }

  return (
    <div className="w-full max-w-5xl mx-auto flex flex-col justify-center my-auto animate-in fade-in duration-300 max-h-[calc(100vh-210px)] overflow-y-auto pr-1">
      {/* Top Navigation Row: Back Button */}
      <div className="flex items-center justify-between mb-2.5 px-1 shrink-0">
        {onBackToHome && (
          <button
            onClick={onBackToHome}
            className="glass-pill px-3.5 py-1.5 rounded-full text-xs font-semibold text-cyan-300 hover:text-white flex items-center gap-1.5 transition-all shadow-md active:scale-95"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>← Back to Ambient Home</span>
          </button>
        )}
        <span className="text-[11px] font-mono text-slate-400">
          {cards.length} {cards.length === 1 ? 'Action Result' : 'Action Results'}
        </span>
      </div>

      {/* Conversational Speech Context Banner */}
      {(lastUserSpeech || lastAssistantSpeech) && (
        <div className="glass-surface px-4 py-2.5 rounded-2xl mb-3 border border-white/10 flex flex-col gap-1.5 shadow-lg shrink-0">
          {lastUserSpeech && (
            <div className="flex items-center gap-2 text-xs text-slate-300">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 bg-white/10 px-2 py-0.5 rounded-md">
                You
              </span>
              <span className="italic text-slate-200">"{lastUserSpeech}"</span>
            </div>
          )}
          {lastAssistantSpeech && (
            <div className="flex items-start gap-2 text-xs text-slate-100 font-medium">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
              <span>{lastAssistantSpeech}</span>
            </div>
          )}
        </div>
      )}

      <div className="space-y-4">
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
    </div>
  )
}

/** 1. Product Carousel Renderer with 1-Click Buy */
const CarouselCardRenderer: React.FC<{
  card: CarouselCard
  onBuyProduct?: (id: number, name: string) => void
}> = ({ card, onBuyProduct }) => {
  return (
    <div className="glass-surface p-6 rounded-3xl relative overflow-hidden border-emerald-500/30 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-emerald-950/60 border border-emerald-500/30 text-emerald-400">
            <ShoppingBag className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-base">{card.title || 'Shoppable Recommendations'}</h3>
            <span className="text-xs text-slate-400">Context-aware Ayurvedic selections</span>
          </div>
        </div>
        <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
          {card.products.length} Items In Stock
        </span>
      </div>

      {/* Horizontal Scrollable Product Track */}
      <div className="flex gap-4 overflow-x-auto pb-3 pt-1 scroll-smooth">
        {card.products.map((product: ProductItem) => {
          const imgUrl = PRODUCT_IMAGES[product.id] || product.image_url
          return (
            <div
              key={product.id}
              className="glass-card w-64 shrink-0 rounded-2xl p-4 flex flex-col justify-between group hover:border-emerald-500/50 hover:shadow-emerald-950/50 hover:shadow-xl transition-all"
            >
              <div>
                <div className="w-full h-36 rounded-xl overflow-hidden bg-slate-900 border border-white/5 relative mb-3">
                  <img
                    src={imgUrl}
                    alt={product.name}
                    loading="lazy"
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                  <div className="absolute top-2 right-2 px-2.5 py-0.5 rounded-full bg-slate-900/90 backdrop-blur-md text-xs font-mono font-bold text-emerald-400 border border-emerald-500/30">
                    ${product.price.toFixed(2)}
                  </div>
                  <div className="absolute bottom-2 left-2 px-2 py-0.5 rounded-md bg-slate-950/80 backdrop-blur-md text-[10px] text-cyan-300 border border-cyan-500/30 font-semibold">
                    Prime
                  </div>
                </div>

                <div className="flex items-center gap-1 text-[11px] text-amber-400 mb-1">
                  <Star className="w-3 h-3 fill-amber-400" />
                  <span className="font-semibold">4.9</span>
                  <span className="text-slate-400 text-[10px]">(890 reviews)</span>
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
                  className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-950 transition-all active:scale-95"
                >
                  <span>1-Click Buy</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/** 2. Smart Home State Card Renderer */
const SmartHomeCardRenderer: React.FC<{ card: SmartHomeCard }> = ({ card }) => {
  return (
    <div className="glass-surface p-6 rounded-3xl border border-white/10 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-amber-950/60 border border-amber-500/30 text-amber-400">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-base">{card.title || 'Smart Home Controls'}</h3>
            <span className="text-xs text-slate-400">Living Room & Climate Sync</span>
          </div>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30">
          MCP Controlled
        </span>
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
                      ? 'bg-amber-500/15 border-amber-500/30 text-amber-400'
                      : 'bg-cyan-500/15 border-cyan-500/30 text-cyan-400'
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
                <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {isLight ? (device.state.on ? 'Active' : 'Off') : 'Set'}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/** 3. Ring Alert Card Renderer */
const RingAlertCardRenderer: React.FC<{ card: RingAlertCard }> = ({ card }) => {
  const isGuest = card.eventType === 'guest_arrival'
  return (
    <div
      className={`glass-surface p-6 rounded-3xl border ${
        isGuest ? 'border-emerald-500/40 bg-emerald-950/20' : 'border-cyan-500/40 bg-sky-950/20'
      } shadow-xl relative overflow-hidden`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div
            className={`p-2.5 rounded-2xl border ${
              isGuest
                ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                : 'bg-cyan-500/20 border-cyan-500/40 text-cyan-300'
            }`}
          >
            {isGuest ? <ShieldCheck className="w-6 h-6" /> : <Package className="w-6 h-6" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-slate-100 text-base">{card.title || 'Ring Doorbell Event'}</h3>
              {card.verified && (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  VERIFIED VISITOR
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-0.5 font-mono">
              Front Porch Ring Cam • Cross-Checked with Household Memory
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900/80 border border-white/10 text-xs font-semibold text-emerald-400">
          <Unlock className="w-4 h-4 text-emerald-400" />
          <span>Door Unlocked</span>
        </div>
      </div>

      <div className="p-4 rounded-2xl bg-slate-950/70 border border-white/5 space-y-2">
        <p className="text-sm text-slate-200">{card.description}</p>
        {card.action_taken && (
          <div className="flex items-center gap-2 text-xs text-emerald-300 pt-1 border-t border-white/5">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>Action Taken: {card.action_taken}</span>
          </div>
        )}
      </div>
    </div>
  )
}

/** 4. Checkout Card Renderer */
const CheckoutCardRenderer: React.FC<{ card: CheckoutCard }> = ({ card }) => {
  return (
    <div className="glass-surface p-6 rounded-3xl border-emerald-500/30 shadow-2xl relative overflow-hidden">
      <div className="absolute top-0 right-0 w-48 h-48 bg-emerald-500/10 rounded-full blur-3xl -z-10" />

      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-300">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-base">{card.title || '1-Click Instant Checkout'}</h3>
            <span className="text-xs text-emerald-400 font-mono">
              Amazon Order Placed • Next-Day Delivery
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-slate-400 font-mono">Order ID</div>
          <div className="text-xs font-mono font-bold text-slate-200 flex items-center gap-1">
            <span>{card.orderId}</span>
          </div>
        </div>
      </div>

      <div className="p-4 rounded-2xl bg-slate-950/80 border border-white/5 space-y-3">
        <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Items Purchased:
        </div>
        <ul className="space-y-1.5">
          {card.items.map((item: string, idx: number) => (
            <li key={idx} className="text-xs text-slate-200 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>{item}</span>
            </li>
          ))}
        </ul>

        <div className="pt-3 border-t border-white/10 flex items-center justify-between">
          <span className="text-xs text-slate-400">Total Charged (One-Click Payment):</span>
          <span className="text-base font-bold font-mono text-emerald-400">
            ${card.total.toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  )
}

/** 5. Memory Card Renderer */
const MemoryCardRenderer: React.FC<{ card: MemoryCard }> = ({ card }) => {
  return (
    <div className="glass-surface p-6 rounded-3xl border border-white/10 shadow-xl">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 rounded-xl bg-cyan-950/60 border border-cyan-500/30 text-cyan-400">
          <Heart className="w-5 h-5" />
        </div>
        <div>
          <h3 className="font-bold text-slate-100 text-base">Household Memory Context</h3>
          <span className="text-xs text-slate-400 font-mono">Session ID: {card.session_id}</span>
        </div>
      </div>

      <p className="text-sm text-slate-200 mb-3">{card.context}</p>

      <div className="flex flex-wrap gap-2 pt-2 border-t border-white/5">
        {card.dietary_restrictions?.map((d, i) => (
          <span
            key={i}
            className="text-[11px] px-2.5 py-1 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 font-medium"
          >
            Diet: {d}
          </span>
        ))}
        {card.health_notes?.map((h, i) => (
          <span
            key={i}
            className="text-[11px] px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20 font-medium"
          >
            Health: {h}
          </span>
        ))}
      </div>
    </div>
  )
}
