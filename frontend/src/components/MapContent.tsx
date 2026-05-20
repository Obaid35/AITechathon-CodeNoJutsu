"use client";

import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { Complaint } from "@/app/page";

const URGENCY_COLORS: Record<string, string> = {
  critical: "#ef4444",
  high: "#f97316",
  medium: "#eab308",
  low: "#22c55e",
};

type Props = { complaints: Complaint[] };

export default function MapContent({ complaints }: Props) {
  const withLoc = complaints.filter((c) => c.location);

  return (
    <div>
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-lg font-bold text-[var(--nk-text)]">Complaint Heatmap</h2>
          <p className="text-[11px] text-[var(--nk-text-muted)]">Geographic distribution of citizen complaints</p>
        </div>
        <div className="flex gap-3">
          {Object.entries(URGENCY_COLORS).map(([level, color]) => (
            <div key={level} className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-[10px] text-[var(--nk-text-muted)] capitalize font-medium">{level}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="nk-card p-0 overflow-hidden" style={{ height: "560px" }}>
        {withLoc.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 rounded-2xl bg-[var(--nk-surface-2)] flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl opacity-40">🗺️</span>
              </div>
              <p className="text-sm font-semibold text-[var(--nk-text-secondary)]">No location data</p>
              <p className="text-[11px] text-[var(--nk-text-muted)] mt-1">Submit complaints with locations to see the map</p>
            </div>
          </div>
        ) : (
          <MapContainer
            center={[33.6844, 73.0479]}
            zoom={11}
            style={{ height: "100%", width: "100%", borderRadius: "14px" }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
              url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
            />
            {withLoc.map((c) => (
              <CircleMarker
                key={c.id}
                center={[c.location!.latitude, c.location!.longitude]}
                radius={c.cluster_size ? Math.min(c.cluster_size * 6, 28) : 9}
                fillColor={URGENCY_COLORS[c.classification.urgency] || "#6366f1"}
                color={URGENCY_COLORS[c.classification.urgency] || "#6366f1"}
                weight={2}
                opacity={0.9}
                fillOpacity={0.3}
              >
                <Popup>
                  <div style={{ maxWidth: 260, fontFamily: "Inter, sans-serif" }}>
                    <p style={{ fontWeight: 800, fontSize: 12, color: "#0f172a", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.04em" }}>
                      {c.classification.department.replace(/_/g, " ")}
                    </p>
                    <p style={{ fontSize: 12, color: "#334155", marginBottom: 6, lineHeight: 1.4 }}>{c.original_text}</p>
                    <div style={{ display: "flex", gap: 8, fontSize: 10, color: "#64748b" }}>
                      <span>📍 {c.location!.resolved_name}</span>
                      <span style={{ fontWeight: 700, color: URGENCY_COLORS[c.classification.urgency] }}>
                        {c.classification.urgency.toUpperCase()} ({(c.classification.urgency_score * 100).toFixed(0)}%)
                      </span>
                    </div>
                    {c.cluster_size && (
                      <p style={{ fontSize: 10, color: "#f59e0b", fontWeight: 700, marginTop: 4 }}>
                        🔗 Cluster of {c.cluster_size} reports
                      </p>
                    )}
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        )}
      </div>
    </div>
  );
}
