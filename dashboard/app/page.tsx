'use client'

import { useState, useEffect } from 'react'
import { Activity, Cpu, MemoryStick, Zap, Users, Brain, Play, Square } from 'lucide-react'

const API_BASE = 'http://localhost:8000'

export default function Dashboard() {
  const [systemStatus, setSystemStatus] = useState({
    state: 'stopped',
    cpu: 0,
    memory: 0,
    gpu: 0,
    activeAgents: 0,
    uptime: 0,
    model_loaded: false,
    tasks_completed: 0,
    tasks_failed: 0
  })
  const [isConnected, setIsConnected] = useState(false)
  const [query, setQuery] = useState('')
  const [response, setResponse] = useState('')

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 2000)
    return () => clearInterval(interval)
  }, [])

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/status`)
      if (res.ok) {
        const data = await res.json()
        setSystemStatus({
          state: data.state,
          cpu: data.cpu_usage_percent,
          memory: data.memory_usage_mb / 1024,
          gpu: data.gpu_usage_percent,
          activeAgents: data.active_agents,
          uptime: data.uptime_seconds,
          model_loaded: data.model_loaded,
          tasks_completed: data.tasks_completed,
          tasks_failed: data.tasks_failed
        })
        setIsConnected(true)
      } else {
        setIsConnected(false)
      }
    } catch (error) {
      setIsConnected(false)
    }
  }

  const handleQuery = async () => {
    console.log('Query button clicked, query:', query)
    if (!query.trim()) return
    
    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      })
      console.log('Query response:', res.status)
      const data = await res.json()
      setResponse(data.response)
    } catch (error) {
      console.error('Query error:', error)
      setResponse('Error: Could not connect to ILLI backend')
    }
  }

  const handleStart = async () => {
    console.log('Start button clicked')
    try {
      const res = await fetch(`${API_BASE}/command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'start' })
      })
      console.log('Start response:', res.status)
      if (res.ok) {
        await fetchStatus()
      }
    } catch (error) {
      console.error('Start error:', error)
    }
  }

  const handleStop = async () => {
    console.log('Stop button clicked')
    try {
      const res = await fetch(`${API_BASE}/command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'stop' })
      })
      console.log('Stop response:', res.status)
      if (res.ok) {
        await fetchStatus()
      }
    } catch (error) {
      console.error('Stop error:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900">
      {/* Header */}
      <header className="border-b border-cyan-500/20 bg-slate-950/50 backdrop-blur-xl">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 animate-pulse-slow neon-glow" />
              <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                ILLI
              </h1>
              <span className="text-xs text-cyan-400/60 px-2 py-1 rounded-full border border-cyan-500/30">
                v0.1.0
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${
                isConnected 
                  ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                  : 'bg-red-500/20 text-red-400 border border-red-500/30'
              }`}>
                <div className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'
                }`} />
                <span className="text-sm font-medium">{isConnected ? 'Connected' : 'Disconnected'}</span>
              </div>
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${
                systemStatus.state === 'running' 
                  ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                  : 'bg-red-500/20 text-red-400 border border-red-500/30'
              }`}>
                <div className={`w-2 h-2 rounded-full ${
                  systemStatus.state === 'running' ? 'bg-green-400 animate-pulse' : 'bg-red-400'
                }`} />
                <span className="text-sm font-medium capitalize">{systemStatus.state}</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={<Cpu className="w-5 h-5" />}
            label="CPU Usage"
            value={`${systemStatus.cpu.toFixed(1)}%`}
            color="cyan"
          />
          <StatCard
            icon={<MemoryStick className="w-5 h-5" />}
            label="Memory"
            value={`${systemStatus.memory.toFixed(1)}%`}
            color="blue"
          />
          <StatCard
            icon={<Zap className="w-5 h-5" />}
            label="GPU Usage"
            value={`${systemStatus.gpu.toFixed(1)}%`}
            color="purple"
          />
          <StatCard
            icon={<Users className="w-5 h-5" />}
            label="Active Agents"
            value={systemStatus.activeAgents.toString()}
            color="green"
          />
        </div>

        {/* Main Panels */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* AI Status Panel */}
          <div className="lg:col-span-2 glass rounded-2xl p-6 cyber-border">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-cyan-400 flex items-center space-x-2">
                <Brain className="w-5 h-5" />
                <span>AI Command Center</span>
              </h2>
              <Activity className="w-5 h-5 text-cyan-400/60 animate-pulse" />
            </div>
            
            <div className="space-y-4">
              <div className="bg-slate-900/50 rounded-xl p-4 border border-cyan-500/20">
                <div className="text-sm text-cyan-400/60 mb-2">Current Model</div>
                <div className="text-lg font-medium text-white">Llama 2 7B (Q4_K_M)</div>
                <div className="text-sm text-cyan-400/60 mt-1">
                  {systemStatus.model_loaded ? '✓ Loaded' : '○ Not Loaded'}
                </div>
              </div>
              
              <div className="bg-slate-900/50 rounded-xl p-4 border border-cyan-500/20">
                <div className="text-sm text-cyan-400/60 mb-2">System Uptime</div>
                <div className="text-lg font-medium text-white">
                  {Math.floor(systemStatus.uptime / 60)}m {systemStatus.uptime % 60}s
                </div>
              </div>
              
              <div className="bg-slate-900/50 rounded-xl p-4 border border-cyan-500/20">
                <div className="text-sm text-cyan-400/60 mb-2">Tasks</div>
                <div className="flex items-center space-x-4">
                  <div>
                    <span className="text-lg font-medium text-white">{systemStatus.tasks_completed}</span>
                    <span className="text-sm text-cyan-400/60 ml-1">Completed</span>
                  </div>
                  <div>
                    <span className="text-lg font-medium text-white">{systemStatus.tasks_failed}</span>
                    <span className="text-sm text-cyan-400/60 ml-1">Failed</span>
                  </div>
                </div>
              </div>

              {/* Query Input */}
              <div className="bg-slate-900/50 rounded-xl p-4 border border-cyan-500/20">
                <div className="text-sm text-cyan-400/60 mb-2">Query ILLI</div>
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask ILLI something..."
                  className="w-full bg-slate-800 border border-cyan-500/30 rounded-lg p-3 text-white placeholder-cyan-400/40 focus:outline-none focus:border-cyan-500 resize-none"
                  rows={3}
                />
                <button
                  onClick={handleQuery}
                  disabled={!query.trim() || systemStatus.state !== 'running'}
                  className="mt-2 w-full py-2 px-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 rounded-lg text-white font-medium transition-all neon-glow disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Send Query
                </button>
              </div>

              {/* Response */}
              {response && (
                <div className="bg-slate-900/50 rounded-xl p-4 border border-cyan-500/20">
                  <div className="text-sm text-cyan-400/60 mb-2">Response</div>
                  <div className="text-white whitespace-pre-wrap">{response}</div>
                </div>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="glass rounded-2xl p-6 cyber-border">
            <h2 className="text-xl font-semibold text-cyan-400 mb-6">Quick Actions</h2>
            
            <div className="space-y-3">
              <button 
                onClick={handleStart}
                disabled={systemStatus.state === 'running'}
                className="w-full py-3 px-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 rounded-xl text-white font-medium transition-all neon-glow disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
              >
                <Play className="w-4 h-4" />
                <span>Start ILLI</span>
              </button>
              <button 
                onClick={handleStop}
                disabled={systemStatus.state !== 'running'}
                className="w-full py-3 px-4 bg-slate-800 hover:bg-slate-700 rounded-xl text-white font-medium transition-all border border-cyan-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
              >
                <Square className="w-4 h-4" />
                <span>Stop ILLI</span>
              </button>
              <button className="w-full py-3 px-4 bg-slate-800 hover:bg-slate-700 rounded-xl text-white font-medium transition-all border border-cyan-500/30">
                View Logs
              </button>
              <button className="w-full py-3 px-4 bg-slate-800 hover:bg-slate-700 rounded-xl text-white font-medium transition-all border border-cyan-500/30">
                Memory Explorer
              </button>
              <button className="w-full py-3 px-4 bg-slate-800 hover:bg-slate-700 rounded-xl text-white font-medium transition-all border border-cyan-500/30">
                Agent Monitor
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

function StatCard({ icon, label, value, color }: { icon: React.ReactNode, label: string, value: string, color: string }) {
  const colorClasses = {
    cyan: 'from-cyan-500/20 to-cyan-600/10 border-cyan-500/30 text-cyan-400',
    blue: 'from-blue-500/20 to-blue-600/10 border-blue-500/30 text-blue-400',
    purple: 'from-purple-500/20 to-purple-600/10 border-purple-500/30 text-purple-400',
    green: 'from-green-500/20 to-green-600/10 border-green-500/30 text-green-400',
  }

  return (
    <div className={`glass rounded-2xl p-6 border ${colorClasses[color as keyof typeof colorClasses]}`}>
      <div className="flex items-center justify-between mb-4">
        {icon}
        <span className="text-sm opacity-60">{label}</span>
      </div>
      <div className="text-3xl font-bold">{value}</div>
    </div>
  )
}
