import React, { useState, useEffect } from 'react'
import {
  Code,
  CheckCircle,
  Clock,
  Play,
  RotateCcw,
  ChevronRight,
  ChevronDown,
  Terminal,
  ShieldCheck,
  Send,
} from 'lucide-react'
import { mcpInitialize, mcpToolsList, mcpToolsCall } from '../api'
import { MCPInspectorPayload } from '../types'

interface McpInspectorProps {
  externalLogs?: MCPInspectorPayload[]
  isOpen: boolean
  onToggle: () => void
}

export const McpInspector: React.FC<McpInspectorProps> = ({
  externalLogs = [],
  isOpen,
  onToggle,
}) => {
  const [logs, setLogs] = useState<MCPInspectorPayload[]>([])
  const [activeTab, setActiveTab] = useState<'all' | 'initialize' | 'tools/list' | 'tools/call'>('all')
  const [isLoading, setIsLoading] = useState(false)
  const [verifiedVersion, setVerifiedVersion] = useState<string | null>(null)

  // Append external logs (ring buffer max 30)
  useEffect(() => {
    if (externalLogs.length > 0) {
      setLogs((prev) => [...externalLogs, ...prev].slice(0, 30))
    }
  }, [externalLogs])

  // Run initial compliance handshake on mount
  useEffect(() => {
    runInitialize()
  }, [])

  const addLog = (
    method: string,
    reqPayload: any,
    resPayload: any,
    latencyMs: number,
    status: number = 200
  ) => {
    const timestamp = new Date().toLocaleTimeString()
    const newItems: MCPInspectorPayload[] = [
      {
        timestamp,
        direction: 'response',
        method,
        payload: resPayload,
        status,
        latencyMs,
      },
      {
        timestamp,
        direction: 'request',
        method,
        payload: reqPayload,
      },
    ]
    setLogs((prev) => [...newItems, ...prev].slice(0, 30))
  }

  const runInitialize = async () => {
    setIsLoading(true)
    const start = performance.now()
    const req = { jsonrpc: '2.0' as const, id: Date.now(), method: 'initialize' as const }
    try {
      const res = await mcpInitialize(req.id)
      const latency = Math.round(performance.now() - start)
      if (res.result?.protocolVersion) {
        setVerifiedVersion(res.result.protocolVersion)
      }
      addLog('initialize', req, res, latency)
    } catch (err: any) {
      addLog('initialize', req, { error: err.message }, Math.round(performance.now() - start), 500)
    } finally {
      setIsLoading(false)
    }
  }

  const runToolsList = async () => {
    setIsLoading(true)
    const start = performance.now()
    const req = { jsonrpc: '2.0' as const, id: Date.now(), method: 'tools/list' as const }
    try {
      const res = await mcpToolsList(req.id)
      const latency = Math.round(performance.now() - start)
      addLog('tools/list', req, res, latency)
    } catch (err: any) {
      addLog('tools/list', req, { error: err.message }, Math.round(performance.now() - start), 500)
    } finally {
      setIsLoading(false)
    }
  }

  const runToolsCall = async () => {
    setIsLoading(true)
    const start = performance.now()
    const args = { query: 'tea', tags: ['ayurvedic', 'wellness'] }
    const req = {
      jsonrpc: '2.0' as const,
      id: Date.now(),
      method: 'tools/call' as const,
      params: { name: 'search_and_build_carousel', arguments: args },
    }
    try {
      const res = await mcpToolsCall('search_and_build_carousel', args, req.id)
      const latency = Math.round(performance.now() - start)
      addLog('tools/call', req, res, latency)
    } catch (err: any) {
      addLog('tools/call', req, { error: err.message }, Math.round(performance.now() - start), 500)
    } finally {
      setIsLoading(false)
    }
  }

  const filteredLogs = logs.filter((log) => {
    if (activeTab === 'all') return true
    return log.method === activeTab
  })

  return (
    <>
      {/* Floating Toggle Button when Drawer is Closed */}
      {!isOpen && (
        <button
          onClick={onToggle}
          className="fixed right-0 top-24 z-40 flex items-center gap-2 px-3 py-2.5 rounded-l-2xl bg-cyan-600 hover:bg-cyan-500 text-white shadow-xl transition-transform hover:-translate-x-1 font-mono text-xs font-semibold"
          title="Open MCP Protocol Inspector"
        >
          <Terminal className="w-4 h-4" />
          <span>MCP Inspector</span>
          {verifiedVersion && (
            <span className="px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] border border-emerald-400/30">
              {verifiedVersion}
            </span>
          )}
        </button>
      )}

      {/* Slide-out Drawer Panel */}
      <div
        className={`fixed inset-y-0 right-0 z-50 w-full sm:w-[480px] bg-slate-950/95 backdrop-blur-2xl border-l border-white/10 shadow-2xl flex flex-col transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Drawer Header */}
        <div className="p-4 border-b border-white/10 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-cyan-950 border border-cyan-500/30 text-cyan-400">
              <Terminal className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-slate-100 text-sm">MCP Protocol Inspector</h3>
                <span className="px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 font-mono text-[10px] border border-cyan-500/20">
                  Streamable HTTP
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                Target: http://localhost:8000/mcp
              </p>
            </div>
          </div>
          <button
            onClick={onToggle}
            className="p-1.5 rounded-xl hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>

        {/* Protocol Compliance Badge */}
        <div className="p-3 bg-gradient-to-r from-cyan-950/40 to-slate-900/40 border-b border-white/5 flex items-center justify-between px-4">
          <div className="flex items-center gap-2 text-xs">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span className="text-slate-300 font-medium">Compliance Spec:</span>
            <span className="font-mono font-bold text-emerald-400">
              {verifiedVersion || '2025-11-25'}
            </span>
          </div>
          <span className="text-[11px] text-slate-400">JSON-RPC 2.0</span>
        </div>

        {/* Quick Test Actions */}
        <div className="p-3 border-b border-white/10 bg-slate-900/30 flex items-center gap-2 overflow-x-auto">
          <button
            onClick={runInitialize}
            disabled={isLoading}
            className="px-2.5 py-1.5 rounded-xl bg-cyan-600/30 hover:bg-cyan-600/50 border border-cyan-500/30 text-cyan-300 text-xs font-mono font-semibold flex items-center gap-1.5 shrink-0 transition-all disabled:opacity-50"
          >
            <Play className="w-3 h-3" />
            <span>initialize</span>
          </button>
          <button
            onClick={runToolsList}
            disabled={isLoading}
            className="px-2.5 py-1.5 rounded-xl bg-purple-600/30 hover:bg-purple-600/50 border border-purple-500/30 text-purple-300 text-xs font-mono font-semibold flex items-center gap-1.5 shrink-0 transition-all disabled:opacity-50"
          >
            <Play className="w-3 h-3" />
            <span>tools/list</span>
          </button>
          <button
            onClick={runToolsCall}
            disabled={isLoading}
            className="px-2.5 py-1.5 rounded-xl bg-emerald-600/30 hover:bg-emerald-600/50 border border-emerald-500/30 text-emerald-300 text-xs font-mono font-semibold flex items-center gap-1.5 shrink-0 transition-all disabled:opacity-50"
          >
            <Play className="w-3 h-3" />
            <span>tools/call</span>
          </button>
          <button
            onClick={() => setLogs([])}
            className="p-1.5 rounded-xl hover:bg-white/10 text-slate-500 hover:text-slate-300 ml-auto transition-colors"
            title="Clear logs"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Filter Tabs */}
        <div className="flex border-b border-white/10 text-xs font-mono px-2 bg-slate-950">
          {(['all', 'initialize', 'tools/list', 'tools/call'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-2 border-b-2 font-medium transition-colors ${
                activeTab === tab
                  ? 'border-cyan-400 text-cyan-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Live Payload Log Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 font-mono text-xs">
          {filteredLogs.length === 0 ? (
            <div className="text-center text-slate-500 py-12">
              <Code className="w-8 h-8 mx-auto mb-2 opacity-40" />
              <p>No JSON-RPC payloads logged yet.</p>
              <p className="text-[11px] mt-1 text-slate-600">
                Click any action above or trigger a voice command.
              </p>
            </div>
          ) : (
            filteredLogs.map((item, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-2xl border ${
                  item.direction === 'request'
                    ? 'bg-slate-900/60 border-sky-500/20'
                    : 'bg-slate-900/90 border-emerald-500/20 shadow-md'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                        item.direction === 'request'
                          ? 'bg-sky-500/20 text-sky-300'
                          : 'bg-emerald-500/20 text-emerald-300'
                      }`}
                    >
                      {item.direction.toUpperCase()}
                    </span>
                    <span className="text-slate-300 font-semibold">{item.method}</span>
                  </div>
                  <div className="flex items-center gap-2 text-[10px] text-slate-400">
                    {item.latencyMs !== undefined && (
                      <span className="flex items-center gap-0.5 text-cyan-400">
                        <Clock className="w-3 h-3" />
                        {item.latencyMs}ms
                      </span>
                    )}
                    <span>{item.timestamp}</span>
                  </div>
                </div>

                <pre className="p-2.5 rounded-xl bg-slate-950/90 text-slate-200 overflow-x-auto text-[11px] leading-relaxed border border-white/5">
                  {JSON.stringify(item.payload, null, 2)}
                </pre>
              </div>
            ))
          )}
        </div>
      </div>
    </>
  )
}
