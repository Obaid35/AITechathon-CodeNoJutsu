"use client";

import { useState } from "react";

const SAMPLES = [
  { tag: "Water", text: "Lahore mein Line 5 me pichle 4 din se pani nahi aa raha, bohot masla hai" },
  { tag: "Power", text: "There has been a power outage in G-9 Islamabad for 12 hours" },
  { tag: "Roads", text: "Rawalpindi main road pe bohot bada khadda hai jiski wajah se accident ho sakta hai" },
  { tag: "Waste", text: "Kachra uthane wala pichle hafte se G-11 Islamabad me nahi aya" },
];

export default function SubmitPanel({ onSubmit, isProcessing, compact = false }: { onSubmit: (t: string, s: string) => void, isProcessing: boolean, compact?: boolean }) {
  const [text, setText] = useState("");
  const [source, setSource] = useState("web");

  return (
    <div className={`w-full ${compact ? '' : 'max-w-4xl mx-auto'}`}>
      
      <div className="ai-input-container">
        {/* Source Selector (hidden in compact mode to save space) */}
        {!compact && (
          <div className="flex px-6 pt-6 gap-3">
            {[
              { id: "web", label: "Web Portal", icon: "💻" },
              { id: "whatsapp", label: "WhatsApp", icon: "💬" },
              { id: "ivr", label: "Voice / IVR", icon: "📞" },
            ].map(s => (
              <button
                key={s.id}
                onClick={() => setSource(s.id)}
                className={`px-4 py-2 rounded-full text-[13px] font-bold transition-all ${
                  source === s.id 
                    ? "bg-zinc-100 text-zinc-900 border border-zinc-200" 
                    : "text-zinc-400 hover:text-zinc-600 border border-transparent"
                }`}
              >
                {s.icon} <span className="ml-1">{s.label}</span>
              </button>
            ))}
          </div>
        )}

        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Describe the issue... (Roman Urdu, Urdu, English)"
          className={`ai-textarea ${compact ? 'h-[140px] px-6 py-6' : 'h-[200px] px-8 py-6'}`}
          dir="auto"
          disabled={isProcessing}
        />
        
        <div className="absolute bottom-6 right-6 flex items-center gap-4">
          <div className="text-[11px] font-medium text-zinc-400 uppercase tracking-widest hidden sm:block">
            Press Enter to submit
          </div>
          <button
            onClick={() => onSubmit(text, source)}
            disabled={!text.trim() || isProcessing}
            className="btn-ai"
          >
            {isProcessing ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                Processing
              </>
            ) : (
              <>
                Analyze <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Samples */}
      {!compact && (
        <div className="mt-8 flex flex-wrap justify-center gap-3 animate-enter" style={{animationDelay: '0.2s'}}>
          {SAMPLES.map((s, i) => (
            <button
              key={i}
              onClick={() => setText(s.text)}
              className="px-4 py-2 rounded-full bg-white border border-zinc-200 text-[13px] font-medium text-zinc-600 hover:border-zinc-400 hover:text-zinc-900 transition-all shadow-sm flex items-center gap-2"
            >
              <span className="w-2 h-2 rounded-full bg-blue-500"></span>
              {s.tag}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
