/**
 * TypeScript data models and interfaces for Alexa+ OmniPulse frontend simulator.
 *
 * Implements design.md §Data Model 7 (MCP UI Card Schemas) and MCP JSON-RPC 2.0 payloads.
 */

export interface ProductItem {
  id: number
  name: string
  price: number
  image_url: string
  description: string
  buyable: boolean
}

export interface DeviceStateItem {
  device_id: string
  device_type: string
  state: {
    on?: boolean
    brightness?: number
    color?: string
    temperature?: number
    mode?: string
    [key: string]: any
  }
  room?: string
}

export interface CarouselCard {
  type: 'carousel'
  title: string
  products: ProductItem[]
}

export interface SmartHomeCard {
  type: 'smarthome_card'
  title: string
  devices: DeviceStateItem[]
}

export interface RingAlertCard {
  type: 'ring_alert_card'
  title: string
  eventType: 'guest_arrival' | 'package_delivery' | string
  verified: boolean
  description: string
  action_taken?: string
}

export interface CheckoutCard {
  type: 'checkout_card'
  title: string
  orderId: string
  items: string[]
  total: number
}

export interface MemoryCard {
  type: 'memory_card'
  session_id: string
  context: string
  health_notes: string[]
  dietary_restrictions: string[]
  preferences: Record<string, any>
}

export type UICard =
  | CarouselCard
  | SmartHomeCard
  | RingAlertCard
  | CheckoutCard
  | MemoryCard

export interface ToolCallLog {
  name: string
  arguments: Record<string, any>
  result?: any
}

export interface ChatResponse {
  speech: string
  cards: UICard[]
  tool_calls: ToolCallLog[]
}

export interface MCPRequest {
  jsonrpc: '2.0'
  id: string | number
  method: 'initialize' | 'tools/list' | 'tools/call'
  params?: Record<string, any>
}

export interface MCPResponse {
  jsonrpc: '2.0'
  id: string | number
  result?: any
  error?: {
    code: number
    message: string
    data?: any
  }
}

export interface MCPInspectorPayload {
  timestamp: string
  direction: 'request' | 'response'
  method: string
  payload: any
  status?: number
  latencyMs?: number
}
