"use client";

import { useEffect, useState } from "react";

type Stats = {
  total_complaints: number;
  by_department: Record<string, number>;
  by_urgency: Record<string, number>;
  avg_urgency_score: number;
  top_locations: { name: string; count: number }[];
  clusters_active: number;
};

const DEPT_LABELS: Record<string, { icon: string; label: string }> = {
  water_supply: { icon: "💧", label: "Water Supply" },
  electricity: { icon: "⚡", label: "Electricity" },
  gas_supply: { icon: "🔥", label: "Gas" },
  roads_infrastructure: { icon: "🛣️", label: "Roads" },
  sanitation_sewerage: { icon: "🚮", label: "Sanitation" },
  health: { icon: "🏥", label: "Health" },
  education: { icon: "📚", label: "Education" },
  police_security: { icon: "🚔", label: "Police" },
  fire_emergency: { icon: "🧯", label: "Fire" },
  public_transport: { icon: "🚌", label: "Transport" },
  telecom: { icon: "📡", label: "Telecom" },
  revenue_land: { icon: "📋", label: "Revenue" },
  environment: { icon: "🌿", label: "Environment" },
  general_complaint: { icon: "📌", label: "General" },
};

type Props = { apiBase: string };

export default function StatsPanel({ apiBase }: Props) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${apiBase}/stats`)
      .then((r) => r.json())
      .then((d) => { setStats(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [apiBase]);

  if (loading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => <div key={i} className="shimmer h-28" />)}
      </div>
    );
  }

  if (!stats || stats.total_complaints === 0) {
    return (
      <div className="bento-panel flex flex-col items-center justify-center min-h-[400px] text-center bg-zinc-50 border-dashed">
        <div className="w-16 h-16 rounded-3xl bg-white border border-zinc-200 flex items-center justify-center mx-auto mb-4 shadow-sm">
          <span className="text-2xl opacity-40">📊</span>
        </div>
        <p className="text-lg font-black text-zinc-900 tracking-tight">No analytics yet</p>
        <p className="text-[13px] font-medium text-zinc-500 mt-2">Submit complaints to see the dashboard</p>
      </div>
    );
  }

  const maxDept = Math.max(...Object.values(stats.by_department), 1);

  return (
    <div className="space-y-6">
      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bento-panel text-center">
          <p className="text-4xl font-black text-blue-600">{stats.total_complaints}</p>
          <p className="text-[12px] text-zinc-500 font-bold mt-2 uppercase tracking-widest">Total Complaints</p>
        </div>
        <div className="bento-panel text-center">
          <p className="text-4xl font-black text-orange-500">{stats.clusters_active}</p>
          <p className="text-[12px] text-zinc-500 font-bold mt-2 uppercase tracking-widest">Active Clusters</p>
        </div>
        <div className="bento-panel text-center">
          <p className="text-4xl font-black text-amber-500">{(stats.avg_urgency_score * 100).toFixed(0)}%</p>
          <p className="text-[12px] text-zinc-500 font-bold mt-2 uppercase tracking-widest">Avg Urgency</p>
        </div>
        <div className="bento-panel text-center">
          <p className="text-4xl font-black text-emerald-500">{Object.keys(stats.by_department).length}</p>
          <p className="text-[12px] text-zinc-500 font-bold mt-2 uppercase tracking-widest">Departments</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-3 bento-panel">
          <h3 className="text-[15px] font-black text-zinc-900 tracking-tight mb-6">Complaints by Department</h3>
          <div className="space-y-5">
            {Object.entries(stats.by_department)
              .sort(([, a], [, b]) => b - a)
              .map(([dept, count]) => {
                const d = DEPT_LABELS[dept] || { icon: "📌", label: dept };
                return (
                  <div key={dept}>
                    <div className="flex justify-between items-center text-[13px] mb-2">
                      <span className="font-bold text-zinc-700">{d.icon} {d.label}</span>
                      <span className="font-black text-blue-600">{count}</span>
                    </div>
                    <div className="h-3 bg-zinc-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-500 to-sky-400 rounded-full transition-all duration-700"
                        style={{ width: `${(count / maxDept) * 100}%` }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
        </div>

        {/* Right column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Urgency */}
          <div className="bento-panel">
            <h3 className="text-[15px] font-black text-zinc-900 tracking-tight mb-6">Urgency Distribution</h3>
            <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
              {(["critical", "high", "medium", "low"] as const).map((level) => {
                const count = stats.by_urgency[level] || 0;
                const colors = {
                  critical: { bg: "bg-red-50", text: "text-red-700", dot: "bg-red-500" },
                  high: { bg: "bg-orange-50", text: "text-orange-700", dot: "bg-orange-500" },
                  medium: { bg: "bg-amber-50", text: "text-amber-700", dot: "bg-amber-500" },
                  low: { bg: "bg-emerald-50", text: "text-emerald-700", dot: "bg-emerald-500" },
                };
                const c = colors[level];
                return (
                  <div key={level} className={`${c.bg} rounded-2xl p-4 text-center transition-all hover:scale-105`}>
                    <div className={`w-2.5 h-2.5 rounded-full ${c.dot} mx-auto mb-3 shadow-sm`} />
                    <p className={`text-2xl font-black ${c.text}`}>{count}</p>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 mt-1">{level}</p>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="bento-panel">
            <h3 className="text-[15px] font-black text-zinc-900 tracking-tight mb-6">Top Complaint Areas</h3>
            {stats.top_locations.length === 0 ? (
              <p className="text-[13px] font-medium text-zinc-500">No location data</p>
            ) : (
              <div className="space-y-3">
                {stats.top_locations.map((loc, i) => (
                  <div key={i} className="flex items-center justify-between p-3.5 rounded-xl bg-zinc-50 hover:bg-zinc-100 border border-zinc-100 transition-colors">
                    <div className="flex items-center gap-3">
                      <span className="w-6 h-6 rounded-lg bg-white border border-zinc-200 flex items-center justify-center text-[10px] font-black text-blue-600 shadow-sm">
                        {i + 1}
                      </span>
                      <span className="text-[13px] font-bold text-zinc-700">{loc.name}</span>
                    </div>
                    <span className="text-[14px] font-black text-blue-600">{loc.count}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
