/**
 * API client for Alexa+ OmniPulse backend.
 *
 * Implements real HTTP requests to /chat, /mcp, and /webhook/ring,
 * fulfilling Property 9 (real HTTP runtime requests, no mock data).
 */

import { ChatResponse, MCPRequest, MCPResponse } from './types'

// Use relative URL by default (proxied by Vite) or fallback to localhost:8000
const API_BASE = window.location.origin.includes(':5173') ? '' : 'http://localhost:8000'

export async function sendChat(message: string, sessionId: string = 'default'): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message, session_id: sessionId }),
  })

  if (!res.ok) {
    const errorText = await res.text()
    throw new Error(`Chat error (${res.status}): ${errorText}`)
  }

  return res.json()
}

export async function sendMCP(req: MCPRequest): Promise<MCPResponse> {
  const res = await fetch(`${API_BASE}/mcp`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(req),
  })

  if (!res.ok) {
    const errorText = await res.text()
    throw new Error(`MCP error (${res.status}): ${errorText}`)
  }

  return res.json()
}

export async function mcpInitialize(id: number | string = 1): Promise<MCPResponse> {
  return sendMCP({
    jsonrpc: '2.0',
    id,
    method: 'initialize',
  })
}

export async function mcpToolsList(id: number | string = 2): Promise<MCPResponse> {
  return sendMCP({
    jsonrpc: '2.0',
    id,
    method: 'tools/list',
  })
}

export async function mcpToolsCall(
  name: string,
  args: Record<string, any> = {},
  id: number | string = 3
): Promise<MCPResponse> {
  return sendMCP({
    jsonrpc: '2.0',
    id,
    method: 'tools/call',
    params: {
      name,
      arguments: args,
    },
  })
}

export async function triggerRingWebhook(
  eventType: 'guest_arrival' | 'package_delivery',
  description: string = 'Front door activity'
): Promise<{ speech: string; ring_alert_card: any }> {
  const res = await fetch(`${API_BASE}/webhook/ring`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ event_type: eventType, description }),
  })

  if (!res.ok) {
    const errorText = await res.text()
    throw new Error(`Ring webhook error (${res.status}): ${errorText}`)
  }

  return res.json()
}

export function subscribeToEvents(
  onEvent: (data: any) => void,
  onError?: (err: any) => void
): () => void {
  const eventSource = new EventSource(`${API_BASE}/events`)

  eventSource.addEventListener('ring_alert', (e) => {
    try {
      const data = JSON.parse(e.data)
      onEvent(data)
    } catch (err) {
      console.error('Failed to parse SSE event data', err)
    }
  })

  eventSource.addEventListener('error', (e) => {
    if (onError) onError(e)
  })

  return () => {
    eventSource.close()
  }
}
