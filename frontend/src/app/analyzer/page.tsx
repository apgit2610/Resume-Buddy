"use client"

import { useState, useRef } from "react"
import AppNav from "@/components/AppNav"

type Results = {
  overall_score: number
  breakdown: {
    keyword_match: number
    sections: number
    content_quality: number
    ats_essentials: number
  }
  keywords: {
    matched: string[]
    missing: string[]
    skill_gaps: string[]
    total_jd: number
    total_matched: number
  }
  sections: {
    score: number
    found_sections: string[]
    missing_sections: string[]
  }
  content: {
    score: number
    word_count: number
    strengths: string[]
    issues: string[]
    metrics_count: number
    action_verbs_found: number
  }
  ats: {
    score: number
    checks: { label: string; pass: boolean }[]
  }
}

function ScoreRing({ score, size = 80 }: { score: number; size?: number }) {
  const color =
    score >= 75 ? "#22c55e" : score >= 50 ? "#f59e0b" : "#ef4444"
  const r = size / 2 - 6
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ

  return (
    <svg width={size} height={size} className="rotate-[-90deg]">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#e3e1da" strokeWidth={6} />
      <circle
        cx={size / 2} cy={size / 2} r={r} fill="none"
        stroke={color} strokeWidth={6}
        strokeDasharray={circ} strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: "stroke-dashoffset 0.6s ease" }}
      />
      <text
        x={size / 2} y={size / 2}
        textAnchor="middle" dominantBaseline="middle"
        className="rotate-90"
        style={{ rotate: "90deg", transformOrigin: `${size / 2}px ${size / 2}px` }}
        fill={color} fontSize={size * 0.22} fontWeight={700} fontFamily="inherit"
      >
        {score}
      </text>
    </svg>
  )
}

function MiniBar({ score, label }: { score: number; label: string }) {
  const color =
    score >= 75 ? "bg-green-500" : score >= 50 ? "bg-amber-400" : "bg-red-400"
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-[#6e7682]">{label}</span>
        <span className="font-mono font-medium text-[#16191d]">{score}%</span>
      </div>
      <div className="h-1.5 bg-[#e3e1da] rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all duration-500`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  )
}

export default function AnalyzerPage() {
  const [jobDescription, setJobDescription] = useState("")
  const [resumeText, setResumeText] = useState("")
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<Results | null>(null)
  const [inputMode, setInputMode] = useState<"paste" | "upload">("paste")
  const [fileName, setFileName] = useState("")
  const [error, setError] = useState("")

  const fileRef = useRef<HTMLInputElement>(null)

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setFileName(file.name)
    const bytes = await file.arrayBuffer()
    const formData = new FormData()
    formData.append("file", file)
    formData.append("job_description", jobDescription || " ")
    // We just extract text for now, full analyze happens on button click
    // Store file for later
    ;(window as any).__resumeFile = file
  }

  const analyze = async () => {
    setError("")
    if (!jobDescription.trim()) { setError("Please enter a job description"); return }

    setLoading(true)
    setResults(null)

    try {
      let res: Response

      if (inputMode === "upload" && (window as any).__resumeFile) {
        const formData = new FormData()
        formData.append("file", (window as any).__resumeFile)
        formData.append("job_description", jobDescription)
        res = await fetch("http://localhost:8000/analyzer/analyze-file", {
          method: "POST",
          body: formData,
        })
      } else {
        if (!resumeText.trim()) { setError("Please paste your resume text"); setLoading(false); return }
        res = await fetch("http://localhost:8000/analyzer/analyze-text", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ resume_text: resumeText, job_description: jobDescription }),
        })
      }

      const data = await res.json()
      if (data.detail) { setError(data.detail); setLoading(false); return }
      setResults(data)
    } catch {
      setError("Failed to connect to the analyzer. Make sure the backend is running.")
    }
    setLoading(false)
  }

  const scoreColor = (s: number) =>
    s >= 75 ? "text-green-600" : s >= 50 ? "text-amber-500" : "text-red-500"

  return (
    <div className="min-h-screen bg-[#fafaf7]">
      <AppNav />

      <main className="max-w-6xl mx-auto px-6 py-10">
        <div className="mb-8">
          <p className="text-xs font-mono uppercase tracking-widest text-[#6e7682] mb-2">Resume Analyzer</p>
          <h2 className="text-3xl font-bold text-[#16191d]" style={{ fontFamily: "var(--font-display)" }}>
            ATS Score & Analysis
          </h2>
        </div>

        {/* Input area */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Resume */}
          <div className="bg-white border border-[#e3e1da] rounded-2xl p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-semibold text-[#16191d]">Your Resume</span>
              <div className="flex gap-1 bg-[#f1f0eb] rounded-lg p-1">
                {(["paste", "upload"] as const).map((m) => (
                  <button
                    key={m}
                    onClick={() => { setInputMode(m); setError("") }}
                    className={`px-3 py-1 text-xs rounded-md transition-colors capitalize ${
                      inputMode === m ? "bg-white text-[#16191d] shadow-sm" : "text-[#6e7682]"
                    }`}
                  >
                    {m === "paste" ? "Paste Text" : "Upload File"}
                  </button>
                ))}
              </div>
            </div>

            {inputMode === "paste" ? (
              <textarea
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                placeholder="Paste your resume text here..."
                rows={12}
                className="w-full px-3 py-2 border border-[#e3e1da] rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#16191d] resize-none bg-[#fafaf7]"
              />
            ) : (
              <label className="flex flex-col items-center justify-center border-2 border-dashed border-[#e3e1da] rounded-xl py-12 cursor-pointer hover:border-[#6e7682] transition-colors">
                <input
                  type="file" accept=".pdf,.docx"
                  ref={fileRef} onChange={handleFile}
                  className="hidden"
                />
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#6e7682" strokeWidth="1.5" className="mb-3">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="12" y1="18" x2="12" y2="12"/>
                  <line x1="9" y1="15" x2="15" y2="15"/>
                </svg>
                <span className="text-sm text-[#6e7682] font-medium">
                  {fileName || "Click to upload PDF or DOCX"}
                </span>
                <span className="text-xs text-[#6e7682] mt-1 opacity-60">Drag and drop supported</span>
              </label>
            )}
          </div>

          {/* Job description */}
          <div className="bg-white border border-[#e3e1da] rounded-2xl p-5">
            <span className="text-sm font-semibold text-[#16191d] block mb-3">Job Description</span>
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the job description here..."
              rows={12}
              className="w-full px-3 py-2 border border-[#e3e1da] rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#16191d] resize-none bg-[#fafaf7]"
            />
          </div>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <button
          onClick={analyze}
          disabled={loading}
          className="w-full bg-[#16191d] text-white py-3 rounded-xl font-semibold hover:bg-[#2a2d32] transition-colors disabled:opacity-50 mb-10"
        >
          {loading ? "Analyzing…" : "Analyze Resume"}
        </button>

        {/* Results */}
        {results && (
          <div className="space-y-6 animate-in fade-in duration-500">

            {/* Overall + breakdown */}
            <div className="bg-white border border-[#e3e1da] rounded-2xl p-6">
              <div className="flex flex-col md:flex-row items-start md:items-center gap-8">
                <div className="flex items-center gap-5">
                  <ScoreRing score={results.overall_score} size={96} />
                  <div>
                    <p className="text-xs font-mono uppercase tracking-widest text-[#6e7682] mb-1">Overall ATS Score</p>
                    <p className={`text-4xl font-bold ${scoreColor(results.overall_score)}`} style={{ fontFamily: "var(--font-display)" }}>
                      {results.overall_score}<span className="text-xl">/100</span>
                    </p>
                    <p className="text-sm text-[#6e7682] mt-1">
                      {results.overall_score >= 75 ? "Strong match — great shape!" : results.overall_score >= 50 ? "Good start — a few improvements will help" : "Needs work — follow the suggestions below"}
                    </p>
                  </div>
                </div>

                <div className="flex-1 w-full space-y-3">
                  <MiniBar score={results.breakdown.keyword_match} label="Keyword Match (40%)" />
                  <MiniBar score={results.breakdown.content_quality} label="Content Quality (25%)" />
                  <MiniBar score={results.breakdown.sections} label="Section Coverage (20%)" />
                  <MiniBar score={results.breakdown.ats_essentials} label="ATS Essentials (15%)" />
                </div>
              </div>
            </div>

            {/* Grid: keywords + sections */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

              {/* Keywords */}
              <div className="bg-white border border-[#e3e1da] rounded-2xl p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-[#16191d]" style={{ fontFamily: "var(--font-display)" }}>
                    Keyword Match
                  </h3>
                  <span className="text-xs font-mono bg-[#f1f0eb] text-[#6e7682] px-2 py-1 rounded-lg">
                    {results.keywords.total_matched}/{results.keywords.total_jd}
                  </span>
                </div>

                {results.keywords.skill_gaps.length > 0 && (
                  <div>
                    <p className="text-xs font-mono uppercase tracking-widest text-[#ff6b47] mb-2">⚠ Skill Gaps</p>
                    <div className="flex flex-wrap gap-2">
                      {results.keywords.skill_gaps.map((k, i) => (
                        <span key={i} className="bg-red-50 text-red-700 border border-red-200 px-2.5 py-1 rounded-lg text-xs font-medium">
                          {k}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <p className="text-xs font-mono uppercase tracking-widest text-[#6e7682] mb-2">✓ Matched</p>
                  <div className="flex flex-wrap gap-2">
                    {results.keywords.matched.slice(0, 15).map((k, i) => (
                      <span key={i} className="bg-green-50 text-green-700 border border-green-200 px-2.5 py-1 rounded-lg text-xs font-medium">
                        {k}
                      </span>
                    ))}
                  </div>
                </div>

                {results.keywords.missing.length > 0 && (
                  <div>
                    <p className="text-xs font-mono uppercase tracking-widest text-[#6e7682] mb-2">✗ Missing Keywords</p>
                    <div className="flex flex-wrap gap-2">
                      {results.keywords.missing.slice(0, 12).map((k, i) => (
                        <span key={i} className="bg-[#f1f0eb] text-[#6e7682] px-2.5 py-1 rounded-lg text-xs">
                          {k}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Sections */}
              <div className="bg-white border border-[#e3e1da] rounded-2xl p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-[#16191d]" style={{ fontFamily: "var(--font-display)" }}>
                    Section Coverage
                  </h3>
                  <span className={`text-sm font-bold ${scoreColor(results.sections.score)}`}>
                    {results.sections.score}%
                  </span>
                </div>

                <div className="space-y-2">
                  {results.sections.found_sections.map((s, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm">
                      <span className="text-green-500 font-bold">✓</span>
                      <span className="capitalize text-[#16191d]">{s}</span>
                    </div>
                  ))}
                  {results.sections.missing_sections.map((s, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm">
                      <span className="text-red-400 font-bold">✗</span>
                      <span className="capitalize text-[#6e7682]">{s} — not detected</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Content quality */}
            <div className="bg-white border border-[#e3e1da] rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-[#16191d]" style={{ fontFamily: "var(--font-display)" }}>
                  Content Quality
                </h3>
                <div className="flex gap-3 text-xs text-[#6e7682]">
                  <span>{results.content.word_count} words</span>
                  <span>•</span>
                  <span>{results.content.metrics_count} metrics</span>
                  <span>•</span>
                  <span>{results.content.action_verbs_found} action verbs</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {results.content.strengths.length > 0 && (
                  <div>
                    <p className="text-xs font-mono uppercase tracking-widest text-green-600 mb-2">Strengths</p>
                    <ul className="space-y-1.5">
                      {results.content.strengths.map((s, i) => (
                        <li key={i} className="text-sm text-[#16191d] flex gap-2">
                          <span className="text-green-500 shrink-0">✓</span> {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {results.content.issues.length > 0 && (
                  <div>
                    <p className="text-xs font-mono uppercase tracking-widest text-[#ff6b47] mb-2">To Improve</p>
                    <ul className="space-y-1.5">
                      {results.content.issues.map((s, i) => (
                        <li key={i} className="text-sm text-[#16191d] flex gap-2">
                          <span className="text-amber-500 shrink-0">→</span> {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            {/* ATS Essentials */}
            <div className="bg-white border border-[#e3e1da] rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-[#16191d]" style={{ fontFamily: "var(--font-display)" }}>
                  ATS Essentials
                </h3>
                <span className={`text-sm font-bold ${scoreColor(results.ats.score)}`}>
                  {results.ats.score}%
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {results.ats.checks.map((c, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm py-1.5 border-b border-[#f1f0eb] last:border-0">
                    <span className={c.pass ? "text-green-500" : "text-red-400"}>
                      {c.pass ? "✓" : "✗"}
                    </span>
                    <span className={c.pass ? "text-[#16191d]" : "text-[#6e7682]"}>{c.label}</span>
                  </div>
                ))}
              </div>
            </div>

          </div>
        )}
      </main>
    </div>
  )
}