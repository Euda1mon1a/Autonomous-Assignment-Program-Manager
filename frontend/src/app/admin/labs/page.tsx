'use client';

/**
 * Research Labs - Category-Based Visualization Hub
 *
 * Consolidates experimental visualizations under functional categories:
 * - Wellness / Fatigue: Intuitive monitoring for Tier 0-1 users
 * - Schedule Optimization: Solver landscapes and topology for Tier 1-2
 * - Fairness / Equity: Workload distribution analysis for Tier 1
 * - Resilience / Risk: Cascading failure analysis for Tier 1-2
 * - Command Center: Unified dashboard for system monitoring
 *
 * @route /admin/labs
 */

import Link from 'next/link';
import {
  Beaker,
  Heart,
  Cpu,
  Scale,
  Shield,
  ArrowRight,
  Activity,
  TrendingUp,
  AlertTriangle,
  Zap,
  Command,
} from 'lucide-react';

interface LabCategory {
  id: string;
  title: string;
  description: string;
  href: string;
  icon: React.ElementType;
  iconBg: string;
  iconColor: string;
  targetTier: string;
  readiness: 'high' | 'medium' | 'low';
  features: string[];
}

const LAB_CATEGORIES: LabCategory[] = [
  {
    id: 'wellness',
    title: 'Wellness & Fatigue',
    description: 'Monitor burnout risk, fatigue levels, and team wellbeing through intuitive neural interface visualization.',
    href: '/admin/labs/wellness',
    icon: Heart,
    iconBg: 'from-rose-500 to-pink-600',
    iconColor: 'text-rose-500',
    targetTier: 'Tier 0-1',
    readiness: 'high',
    features: ['Synapse Monitor', 'Burnout Rt', 'Fatigue Scoring'],
  },
  {
    id: 'optimization',
    title: 'Schedule Optimization',
    description: 'Explore solver landscapes and constraint topology through 3D visualizations of the optimization space.',
    href: '/admin/labs/optimization',
    icon: Cpu,
    iconBg: 'from-cyan-500 to-blue-600',
    iconColor: 'text-cyan-500',
    targetTier: 'Tier 1-2',
    readiness: 'medium',
    features: ['CP-SAT Simulator', 'Brane Topology', 'Foam Topology'],
  },
  {
    id: 'fairness',
    title: 'Fairness & Equity',
    description: 'Analyze workload distribution using Lorenz curves, Gini coefficients, and Shapley value decomposition.',
    href: '/admin/labs/fairness',
    icon: Scale,
    iconBg: 'from-emerald-500 to-teal-600',
    iconColor: 'text-emerald-500',
    targetTier: 'Tier 1',
    readiness: 'high',
    features: ['Lorenz Curve', 'Shapley Values', 'Jain Index'],
  },
  {
    id: 'resilience',
    title: 'Resilience & Risk',
    description: 'Identify cascading failure risks and simulate black swan events in the scheduling system.',
    href: '/admin/labs/resilience',
    icon: Shield,
    iconBg: 'from-amber-500 to-orange-600',
    iconColor: 'text-amber-500',
    targetTier: 'Tier 1-2',
    readiness: 'medium',
    features: ['Fragility Triage', 'N-1/N-2 Resilience', 'Cascade Simulation'],
  },
  {
    id: 'command',
    title: 'Command Center',
    description: 'Unified command dashboard for monitoring all scheduling subsystems from a single view.',
    href: '/admin/labs/command',
    icon: Command,
    iconBg: 'from-purple-500 to-indigo-600',
    iconColor: 'text-purple-500',
    targetTier: 'Tier 1',
    readiness: 'medium',
    features: ['Sovereign Portal', '4-Panel View', 'System Alerts'],
  },
];

function ReadinessIndicator({ readiness }: { readiness: 'high' | 'medium' | 'low' }) {
  const config = {
    high: { label: 'Ready', color: 'bg-emerald-500', glow: 'shadow-emerald-500/50' },
    medium: { label: 'Beta', color: 'bg-amber-500', glow: 'shadow-amber-500/50' },
    low: { label: 'Alpha', color: 'bg-red-500', glow: 'shadow-red-500/50' },
  };

  const { label, color, glow } = config[readiness];

  return (
    <div className="flex items-center gap-1.5">
      <div className={`w-2 h-2 rounded-full ${color} ${glow} shadow-sm`} />
      <span className="text-xs text-slate-400">{label}</span>
    </div>
  );
}

function CategoryCard({ category }: { category: LabCategory }) {
  const Icon = category.icon;

  return (
    <Link
      href={category.href}
      className="group relative bg-slate-800/50 border border-slate-700/50 rounded-xl p-6 hover:border-slate-600 hover:bg-slate-800/80 transition-all duration-300"
    >
      {/* Icon */}
      <div className={`inline-flex p-3 rounded-lg bg-gradient-to-br ${category.iconBg} mb-4`}>
        <Icon className="w-6 h-6 text-white" />
      </div>

      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-lg font-semibold text-white group-hover:text-cyan-400 transition-colors">
          {category.title}
        </h3>
        <ArrowRight className="w-5 h-5 text-slate-500 group-hover:text-cyan-400 group-hover:translate-x-1 transition-all" />
      </div>

      {/* Description */}
      <p className="text-sm text-slate-400 mb-4 line-clamp-2">
        {category.description}
      </p>

      {/* Features */}
      <div className="flex flex-wrap gap-2 mb-4">
        {category.features.map((feature) => (
          <span
            key={feature}
            className="text-xs px-2 py-1 bg-slate-700/50 text-slate-300 rounded-md"
          >
            {feature}
          </span>
        ))}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-700/50">
        <span className="text-xs text-slate-500">{category.targetTier}</span>
        <ReadinessIndicator readiness={category.readiness} />
      </div>
    </Link>
  );
}

function QuickStats() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      <div className="bg-slate-800/30 border border-slate-700/30 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <Activity className="w-4 h-4 text-cyan-500" />
          <span className="text-xs text-slate-400 uppercase tracking-wide">Visualizations</span>
        </div>
        <span className="text-2xl font-bold text-white">12</span>
      </div>
      <div className="bg-slate-800/30 border border-slate-700/30 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <TrendingUp className="w-4 h-4 text-emerald-500" />
          <span className="text-xs text-slate-400 uppercase tracking-wide">Ready</span>
        </div>
        <span className="text-2xl font-bold text-white">5</span>
      </div>
      <div className="bg-slate-800/30 border border-slate-700/30 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle className="w-4 h-4 text-amber-500" />
          <span className="text-xs text-slate-400 uppercase tracking-wide">Beta</span>
        </div>
        <span className="text-2xl font-bold text-white">7</span>
      </div>
      <div className="bg-slate-800/30 border border-slate-700/30 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <Zap className="w-4 h-4 text-violet-500" />
          <span className="text-xs text-slate-400 uppercase tracking-wide">3D/WebGL</span>
        </div>
        <span className="text-2xl font-bold text-white">8</span>
      </div>
    </div>
  );
}

export default function LabsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-violet-500 to-purple-600 rounded-lg">
              <Beaker className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Research Labs</h1>
              <p className="text-sm text-slate-400">
                Experimental visualizations for scheduling intelligence
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Quick Stats */}
        <QuickStats />

        {/* Category Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {LAB_CATEGORIES.map((category) => (
            <CategoryCard key={category.id} category={category} />
          ))}
        </div>

        {/* Footer Note */}
        <div className="mt-8 p-4 bg-slate-800/30 border border-slate-700/30 rounded-lg">
          <p className="text-sm text-slate-400 text-center">
            <span className="text-cyan-400">Graduation Path:</span> Visualizations marked as
            &quot;Ready&quot; are candidates for promotion to user-facing tiers. Beta tools
            require additional refinement before general availability.
          </p>
        </div>
      </main>
    </div>
  );
}
