'use client'

import { useState, useEffect } from 'react'
import { Activity, Cpu, MemoryStick, Zap, Users, Brain } from 'lucide-react'

export default function Dashboard() {
  const [systemStatus, setSystemStatus] = useState({
    state: 'stopped',
    cpu: 0,
    memory: 0,
    gpu: 0,
    activeAgents: 0,
    uptime: 0
  })

  useEffect(() => {
    // Simulate real-time updates
    const interval = setInterval(() => {
      setSystemStatus(prev => ({
        ...prev,
        cpu: Math.random() * 30 + 10,
        memory: Math.random() * 20 + 40,
        gpu: Math.random() * 40 + 20,
        uptime: prev.uptime + 1
      }))
    }, 1000)

    return () => clearInterval(interval)
  }, [])

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
              </div>
              
              <div className="bg-slate-900/50 rounded-xl p-4 border border-cyan-500/20">
                <div className="text-sm text-cyan-400/60 mb-2">System Uptime</div>
                <div className="text-lg font-medium text-white">
                  {Math.floor(systemStatus.uptime / 60)}m {systemStatus.uptime % 60}s
                </div>
              </div>
              
              <div className="bg-slate-900/50 rounded-xl p-4 border border-cyan-500/20">
                <div className="text-sm text-cyan-400/60 mb-2">Thinking State</div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 rounded-full bg-cyan-400 animate-pulse" />
                  <span className="text-lg font-medium text-white">Ready</span>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="glass rounded-2xl p-6 cyber-border">
            <h2 className="text-xl font-semibold text-cyan-400 mb-6">Quick Actions</h2>
            
            <div className="space-y-3">
              <button className="w-full py-3 px-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 rounded-xl text-white font-medium transition-all neon-glow">
                Start ILLI
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
