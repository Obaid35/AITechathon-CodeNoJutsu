"use client";

import type { Complaint } from "@/app/page";

const DEPT_LABELS: Record<string, { icon: string; label: string; color: string }> = {
  water_supply: { icon: "💧", label: "Water Supply", color: "text-sky-600 bg-sky-50 border-sky-100" },
  electricity: { icon: "⚡", label: "Electricity", color: "text-amber-600 bg-amber-50 border-amber-100" },
  gas_supply: { icon: "🔥", label: "Gas Supply", color: "text-orange-600 bg-orange-50 border-orange-100" },
  roads_infrastructure: { icon: "🛣️", label: "Roads", color: "text-slate-600 bg-slate-100 border-slate-200" },
  sanitation_sewerage: { icon: "🚮", label: "Sanitation", color: "text-lime-600 bg-lime-50 border-lime-100" },
  health: { icon: "🏥", label: "Health", color: "text-rose-600 bg-rose-50 border-rose-100" },
  education: { icon: "📚", label: "Education", color: "text-blue-600 bg-blue-50 border-blue-100" },
  police_security: { icon: "🚔", label: "Security", color: "text-red-600 bg-red-50 border-red-100" },
  fire_emergency: { icon: "🧯", label: "Fire", color: "text-red-700 bg-red-100 border-red-200" },
  public_transport: { icon: "🚌", label: "Transport", color: "text-teal-600 bg-teal-50 border-teal-100" },
  telecom: { icon: "📡", label: "Telecom", color: "text-violet-600 bg-violet-50 border-violet-100" },
  revenue_land: { icon: "📋", label: "Revenue", color: "text-yellow-600 bg-yellow-50 border-yellow-100" },
  environment: { icon: "🌿", label: "Environment", color: "text-emerald-600 bg-emerald-50 border-emerald-100" },
  general_complaint: { icon: "📌", label: "General", color: "text-gray-600 bg-gray-50 border-gray-200" },
};

type Props = {
  result: Complaint | null;
  isProcessing: boolean;
};

export default function ComplaintResult({ result, isProcessing }: Props) {
  if (isProcessing) {
    return (
      <div className="w-full flex flex-col items-center justify-center py-20 animate-enter">
        <div className="w-16 h-16 rounded-full border-4 border-zinc-100 border-t-zinc-900 animate-spin mb-6" />
        <h3 className="text-2xl font-black text-zinc-900 mb-2 tracking-tight">AI is Triageing...</h3>
        <p className="text-sm font-medium text-zinc-500 uppercase tracking-widest">Running zero-shot classification & NER</p>
      </div>
    );
  }

  if (!result) return null;

  const c = result.classification;
  const dept = DEPT_LABELS[c.department] || DEPT_LABELS.general_complaint;

  return (
    <div className="w-full max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-4 md:gap-6 mt-8">

      {/* ─── BENTO 1: PRIMARY CLASSIFICATION (Span 12) ─── */}
      <div className="bento-panel md:col-span-12 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <p className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-2">Primary Classification</p>
          <div className="flex items-center gap-3">
            <span className={`tag border ${dept.color} text-sm px-4 py-1.5`}>
              {dept.icon} {dept.label}
            </span>
            <span className="text-lg font-black text-zinc-300">/</span>
            <span className="text-lg font-bold text-zinc-800">{c.sub_category}</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-1">Urgency</p>
            <p className={`text-xl font-black uppercase ${c.urgency === 'critical' ? 'text-red-600' :
                c.urgency === 'high' ? 'text-orange-600' :
                  c.urgency === 'medium' ? 'text-amber-500' : 'text-emerald-500'
              }`}>
              {c.urgency}
            </p>
          </div>
          <div className="w-16 h-16 rounded-full bg-zinc-50 border-4 border-zinc-100 flex items-center justify-center">
            <span className="text-xl font-black text-zinc-900">{(c.urgency_score * 100).toFixed(0)}</span>
          </div>
        </div>
      </div>

      {/* ─── BENTO 2: LOCATION (Span 7) ─── */}
      <div className="bento-panel md:col-span-7 bg-blue-50/50 border-blue-100 relative overflow-hidden">
        <div className="absolute -right-10 -bottom-10 text-[120px] opacity-[0.03]">📍</div>
        <p className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-3">Geospatial Entity Extracted</p>

        {result.location ? (
          <>
            <h3 className="text-3xl font-black text-blue-950 tracking-tight leading-none mb-3">{result.location.resolved_name}</h3>
            <div className="flex gap-3 text-sm font-semibold text-blue-700">
              <span className="bg-white px-3 py-1 rounded-full border border-blue-100 shadow-sm">{result.location.latitude.toFixed(4)}, {result.location.longitude.toFixed(4)}</span>
              <span className="bg-white px-3 py-1 rounded-full border border-blue-100 shadow-sm">{(result.location.confidence * 100).toFixed(0)}% Confidence</span>
            </div>
          </>
        ) : (
          <div className="flex items-center gap-3 text-zinc-500">
            <span className="text-2xl">🌍</span>
            <span className="font-medium text-sm">No specific location entities detected in the text.</span>
          </div>
        )}
      </div>

      {/* ─── BENTO 3: CLUSTER & SENTIMENT (Span 5) ─── */}
      <div className="bento-panel md:col-span-5 flex flex-col gap-4">
        <div className="flex-1 bg-zinc-50 rounded-2xl p-4 border border-zinc-200">
          <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-1">Deduplication Cluster</p>
          {result.cluster_id ? (
            <p className="text-sm font-bold text-zinc-800">
              🔗 Linked to <span className="text-blue-600 bg-blue-50 px-2 py-0.5 rounded font-mono">{result.cluster_id}</span> ({result.cluster_size} similar)
            </p>
          ) : (
            <p className="text-sm font-medium text-zinc-500">Unique issue (New Cluster Created)</p>
          )}
        </div>

        <div className="flex-1 bg-zinc-50 rounded-2xl p-4 border border-zinc-200 flex justify-between items-center">
          <div>
            <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-1">Sentiment</p>
            <p className="text-sm font-bold text-zinc-800 capitalize">{c.sentiment}</p>
          </div>
          <div className="text-2xl">
            {c.sentiment === 'angry' ? '😡' : c.sentiment === 'urgent' ? '🚨' : c.sentiment === 'sad' ? '😢' : '😐'}
          </div>
        </div>
      </div>

      {/* ─── BENTO 4: TRANSLATION / RESPONSE (Span 12) ─── */}
      <div className="bento-panel md:col-span-12 relative overflow-hidden" style={{ backgroundColor: "#ffffff", color: "#1c1917" }}>
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 blur-[50px] rounded-full pointer-events-none" />
        <div className="flex items-center justify-between mb-4 relative z-10">
          <p className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Generated Auto-Response (Urdu)</p>
          <span className="px-3 py-1.5 rounded-full bg-zinc-100 border border-zinc-200 text-zinc-600 text-[10px] font-black tracking-widest uppercase">Llama 3.1</span>
        </div>
        <p className="text-2xl font-bold leading-relaxed relative z-10 text-zinc-900" dir="rtl">
          {result.suggested_response_urdu}
        </p>
      </div>

    </div>
  );
}
