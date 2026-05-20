"use client";

import type { Complaint } from "@/app/page";

const URGENCY_BAR: Record<string, string> = {
  critical: "border-l-red-500",
  high: "border-l-orange-400",
  medium: "border-l-amber-400",
  low: "border-l-emerald-400",
};

const DEPT_ICONS: Record<string, string> = {
  water_supply: "💧", electricity: "⚡", gas_supply: "🔥",
  roads_infrastructure: "🛣️", sanitation_sewerage: "🚮", health: "🏥",
  education: "📚", police_security: "🚔", fire_emergency: "🧯",
  public_transport: "🚌", telecom: "📡", revenue_land: "📋",
  environment: "🌿", general_complaint: "📌",
};

type Props = { complaints: Complaint[]; isAdmin?: boolean };

export default function ComplaintFeed({ complaints, isAdmin }: Props) {
  if (complaints.length === 0) {
    return (
      <div className="bento-panel flex flex-col items-center justify-center min-h-[400px] text-center bg-zinc-50 border-dashed">
        <div className="w-16 h-16 rounded-3xl bg-white border border-zinc-200 flex items-center justify-center mx-auto mb-4 shadow-sm">
          <span className="text-2xl opacity-40">📋</span>
        </div>
        <p className="text-lg font-black text-zinc-900 tracking-tight">No complaints yet</p>
        <p className="text-[13px] font-medium text-zinc-500 mt-2">Submit a complaint to see the live feed</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-black text-gray-900 tracking-tight">Live Complaint Feed</h2>
          <p className="text-[13px] font-medium text-gray-500 mt-1">Sorted by urgency score (highest first)</p>
        </div>
        <span className="px-4 py-2 rounded-xl bg-gray-100 text-[12px] font-bold text-gray-600 border border-gray-200">
          {complaints.length} total
        </span>
      </div>

      <div className="space-y-3">
        {complaints.map((c) => (
          <div
            key={c.id}
            className={`bento-panel border-l-[3px] ${URGENCY_BAR[c.classification.urgency] || "border-l-gray-300"} ${c.classification.urgency === "critical" ? "pulse-ring" : ""
              }`}
            style={{ padding: "16px 20px" }}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-3 flex-wrap">
                  <span className="text-lg">{DEPT_ICONS[c.classification.department] || "📌"}</span>
                  <span className="dept-chip">{c.classification.department.replace(/_/g, " ")}</span>
                  {c.source === 'whatsapp' && <span className="px-2 py-1 rounded bg-green-100 text-green-700 text-[10px] font-bold border border-green-200">💬 WhatsApp</span>}
                  {c.source === 'ivr' && <span className="px-2 py-1 rounded bg-purple-100 text-purple-700 text-[10px] font-bold border border-purple-200">📞 IVR</span>}
                  {(!c.source || c.source === 'web') && <span className="px-2 py-1 rounded bg-blue-50 text-blue-600 text-[10px] font-bold border border-blue-200">💻 Web</span>}
                  <span className={`px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider ${
                    c.classification.urgency === "critical" ? "pill-critical" :
                    c.classification.urgency === "high" ? "pill-high" :
                    c.classification.urgency === "medium" ? "pill-medium" : "pill-low"
                  }`}>
                    {c.classification.urgency}
                  </span>
                  {c.cluster_id && (
                    <span className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                      🔗 ×{c.cluster_size}
                    </span>
                  )}
                </div>

                <p className="text-[15px] font-bold text-gray-900 mb-1 leading-snug">{c.original_text}</p>
                <p className="text-[13px] font-medium text-gray-500 leading-snug">{c.normalized_text}</p>

                <div className="flex items-center gap-3 mt-4 text-[11px] font-medium text-gray-400">
                  {c.location && (
                    <span className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-sky-50 text-sky-700 font-bold border border-sky-100">📍 {c.location.resolved_name}</span>
                  )}
                  <span>{new Date(c.processed_at).toLocaleTimeString()}</span>
                  <span className="font-mono bg-gray-100 px-1.5 py-0.5 rounded text-gray-500">{c.id}</span>
                </div>
              </div>

              <div className="flex flex-col items-end gap-2 shrink-0">
                <div className={`score-ring ${c.classification.urgency_score >= 0.9 ? "score-critical" :
                    c.classification.urgency_score >= 0.7 ? "score-high" :
                      c.classification.urgency_score >= 0.4 ? "score-medium" : "score-low"
                  }`}>
                  {(c.classification.urgency_score * 100).toFixed(0)}
                </div>
                {isAdmin && (
                  <button 
                    onClick={() => alert(`Marked complaint ${c.id} as resolved (Demo)`)}
                    className="px-3 py-1.5 mt-1 text-[11px] font-bold text-indigo-700 bg-indigo-50 border border-indigo-200 hover:bg-indigo-100 hover:text-indigo-800 rounded-lg transition shadow-sm w-full"
                  >
                    Resolve
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
