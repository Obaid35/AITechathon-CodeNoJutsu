"use client";

import dynamic from "next/dynamic";
import type { Complaint } from "@/app/page";

const MapComponent = dynamic(() => import("./MapContent"), { 
  ssr: false,
  loading: () => (
    <div className="glass-card h-[600px] flex items-center justify-center">
      <p className="text-[var(--nk-text-secondary)]">Loading map...</p>
    </div>
  )
});

type Props = {
  complaints: Complaint[];
};

export default function MapPanel({ complaints }: Props) {
  return <MapComponent complaints={complaints} />;
}
