"use client";

import { useState, useEffect } from "react";
import SubmitPanel from "@/components/SubmitPanel";
import ComplaintResult from "@/components/ComplaintResult";
import ComplaintFeed from "@/components/ComplaintFeed";
import StatsPanel from "@/components/StatsPanel";
import MapPanel from "@/components/MapPanel";

const API_BASE = "http://127.0.0.1:8000/api";

export type Complaint = {
  id: string;
  original_text: string;
  normalized_text: string;
  classification: {
    department: string;
    sub_category: string;
    urgency: string;
    urgency_score: number;
    sentiment: string;
    keywords: string[];
  };
  location: {
    raw_text: string;
    resolved_name: string;
    latitude: number;
    longitude: number;
    confidence: number;
  } | null;
  cluster_id: string | null;
  cluster_size: number | null;
  suggested_response_urdu: string;
  source?: string;
  processed_at: string;
};

export default function Home() {
  const [activeView, setActiveView] = useState<"ai" | "feed" | "map" | "stats">("ai");
  const [lastResult, setLastResult] = useState<Complaint | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [complaints, setComplaints] = useState<Complaint[]>([]);

  // Auth state
  const [isAdmin, setIsAdmin] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginForm, setLoginForm] = useState({ username: "", password: "" });

  useEffect(() => {
    const storedAdmin = localStorage.getItem("naqskar_admin");
    if (storedAdmin === "true") {
      setIsAdmin(true);
    }
    refreshComplaints();
  }, []);

  const handleSubmit = async (text: string, source: string) => {
    setIsProcessing(true);
    setLastResult(null);
    try {
      const res = await fetch(`${API_BASE}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, source }),
      });
      const data: Complaint = await res.json();
      setLastResult(data);
      setComplaints((prev) => [data, ...prev]);
    } catch (err) {
      console.error("Submit error:", err);
    } finally {
      setIsProcessing(false);
    }
  };

  const refreshComplaints = async () => {
    try {
      const res = await fetch(`${API_BASE}/complaints?limit=50`);
      const data = await res.json();
      const normalized = (data.complaints || []).map((c: any) => ({
        ...c,
        classification: c.classification || {
          department: c.department || "general_complaint",
          sub_category: c.sub_category || "general",
          urgency: c.urgency || "medium",
          urgency_score: c.urgency_score || 0.5,
          sentiment: c.sentiment || "neutral",
          keywords: c.keywords || [],
        },
        processed_at: c.processed_at || new Date().toISOString(),
      }));
      setComplaints(normalized);
    } catch (err) {
      console.error("Fetch error:", err);
    }
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (loginForm.username === "admin" && loginForm.password === "pakistan") {
      setIsAdmin(true);
      localStorage.setItem("naqskar_admin", "true");
      setShowLoginModal(false);
      setLoginForm({ username: "", password: "" });
    } else {
      alert("Invalid credentials.");
    }
  };

  const handleLogout = () => {
    setIsAdmin(false);
    localStorage.removeItem("naqskar_admin");
  };

  return (
    <div className="min-h-screen flex flex-col relative">
      
      {/* ─── TOP NAVIGATION ────────────────────────────────────── */}
      <header className="fixed top-0 left-0 right-0 h-20 px-8 flex items-center justify-between z-40 bg-[var(--bg)]/80 backdrop-blur-md">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveView("ai")}>
          <div className="w-10 h-10 rounded-2xl bg-zinc-900 flex items-center justify-center text-white font-black text-xl shadow-lg">
            N
          </div>
          <span className="text-xl font-black tracking-tighter text-zinc-900">NaqsKAR</span>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={() => setActiveView("ai")}
            className={`px-5 py-2.5 rounded-full text-sm font-bold transition-all ${activeView === "ai" ? "bg-white shadow-sm border border-gray-200 text-zinc-900" : "text-gray-500 hover:text-zinc-900 hover:bg-gray-100"}`}
          >
            AI Triage
          </button>
          <button 
            onClick={() => { setActiveView("feed"); refreshComplaints(); }}
            className={`px-5 py-2.5 rounded-full text-sm font-bold transition-all ${activeView === "feed" ? "bg-white shadow-sm border border-gray-200 text-zinc-900" : "text-gray-500 hover:text-zinc-900 hover:bg-gray-100"}`}
          >
            Live Feed
          </button>
          <button 
            onClick={() => { setActiveView("map"); refreshComplaints(); }}
            className={`px-5 py-2.5 rounded-full text-sm font-bold transition-all ${activeView === "map" ? "bg-white shadow-sm border border-gray-200 text-zinc-900" : "text-gray-500 hover:text-zinc-900 hover:bg-gray-100"}`}
          >
            Map
          </button>
          
          {isAdmin ? (
            <>
              <button 
                onClick={() => { setActiveView("stats"); refreshComplaints(); }}
                className={`px-5 py-2.5 rounded-full text-sm font-bold transition-all ${activeView === "stats" ? "bg-white shadow-sm border border-gray-200 text-zinc-900" : "text-gray-500 hover:text-zinc-900 hover:bg-gray-100"}`}
              >
                Analytics
              </button>
              <button onClick={handleLogout} className="ml-2 btn-icon text-red-500 bg-red-50 border-red-100" title="Logout">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
              </button>
            </>
          ) : (
            <button onClick={() => setShowLoginModal(true)} className="ml-2 btn-icon" title="Admin Login">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            </button>
          )}
        </div>
      </header>

      {/* ─── MAIN CONTENT ─────────────────────────────────────── */}
      <main className="flex-1 pt-28 pb-20 px-8 max-w-[1200px] w-full mx-auto relative">
        {activeView === "ai" && (
          <div className="flex flex-col items-center justify-start min-h-[calc(100vh-160px)] w-full">
            
            {/* The Input changes size depending on if there is a result */}
            <div className={`w-full max-w-4xl transition-all duration-700 ease-in-out ${lastResult || isProcessing ? "mb-12" : "mt-[15vh]"}`}>
              {!lastResult && !isProcessing && (
                <h1 className="text-4xl md:text-5xl font-black text-center mb-10 tracking-tight text-zinc-800">
                  How can we help you today?
                </h1>
              )}
              <SubmitPanel onSubmit={handleSubmit} isProcessing={isProcessing} compact={!!lastResult} />
            </div>

            {/* Results Bento Grid */}
            {(lastResult || isProcessing) && (
              <div className="w-full animate-enter">
                <ComplaintResult result={lastResult} isProcessing={isProcessing} />
              </div>
            )}
          </div>
        )}

        {activeView === "feed" && <div className="animate-enter"><ComplaintFeed complaints={complaints} isAdmin={isAdmin} /></div>}
        {activeView === "map" && <div className="animate-enter h-[calc(100vh-160px)]"><MapPanel complaints={complaints} /></div>}
        {activeView === "stats" && <div className="animate-enter"><StatsPanel apiBase={API_BASE} /></div>}
      </main>

      {/* ─── LOGIN MODAL ────────────────────────────────────────── */}
      {showLoginModal && (
        <div className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-enter">
          <div className="bg-white rounded-[32px] shadow-2xl w-full max-w-sm overflow-hidden p-8">
            <div className="text-center mb-8">
              <div className="w-16 h-16 rounded-full bg-zinc-100 flex items-center justify-center mx-auto mb-4 text-2xl">
                🛡️
              </div>
              <h3 className="text-2xl font-black text-zinc-900">Admin Access</h3>
            </div>
            <form onSubmit={handleLogin} className="space-y-4">
              <input 
                type="text" 
                value={loginForm.username}
                onChange={e => setLoginForm({...loginForm, username: e.target.value})}
                className="w-full px-5 py-4 bg-zinc-50 border border-zinc-200 rounded-2xl text-base focus:outline-none focus:border-zinc-400 transition-all font-medium"
                placeholder="Username"
              />
              <input 
                type="password" 
                value={loginForm.password}
                onChange={e => setLoginForm({...loginForm, password: e.target.value})}
                className="w-full px-5 py-4 bg-zinc-50 border border-zinc-200 rounded-2xl text-base focus:outline-none focus:border-zinc-400 transition-all font-medium"
                placeholder="Password"
              />
              <div className="pt-4 flex gap-3">
                <button type="button" onClick={() => setShowLoginModal(false)} className="flex-1 py-4 rounded-full text-sm font-bold text-zinc-500 hover:bg-zinc-100 transition-all">
                  Cancel
                </button>
                <button type="submit" className="flex-1 py-4 rounded-full text-sm font-bold text-white bg-zinc-900 hover:bg-black transition-all">
                  Sign In
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
