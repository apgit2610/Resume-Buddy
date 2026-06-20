"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import AppNav from "@/components/AppNav"
import { API_URL } from "@/lib/api"

export default function AnalyzerPage() {
    const [jobDescription, setJobDescription] = useState("")
    const [resumeText, setResumeText] = useState("")
    const [file, setFile] = useState<File | null>(null)
    const [mode, setMode] = useState<"paste" | "upload">("upload")
    const [loading, setLoading] = useState(false)
    const [results, setResults] = useState<any>(null)

    const analyze = async () => {
        if (!jobDescription.trim()) {
            alert("Please enter a job description")
            return
        }

        setLoading(true)
        try {
            let data

            if (mode === "upload" && file) {
                const formData = new FormData()
                formData.append("file", file)
                formData.append("job_description", jobDescription)
                const res = await fetch(`${API_URL}/analyzer/analyze-file`, {
                    method: "POST",
                    body: formData,
                })
                data = await res.json()
            } else {
                if (!resumeText.trim()) {
                    alert("Please paste your resume text")
                    setLoading(false)
                    return
                }
                const res = await fetch(`${API_URL}/analyzer/analyze-text`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ resume_text: resumeText, job_description: jobDescription }),
                })
                data = await res.json()
            }

            setResults(data)
        } catch (e) {
            alert("Something went wrong. Please try again.")
        }
        setLoading(false)
    }

    const scoreColor = (score: number) => {
        if (score >= 75) return "text-green-600"
        if (score >= 50) return "text-yellow-600"
        return "text-red-500"
    }

    const scoreBarColor = (score: number) => {
        if (score >= 75) return "bg-green-500"
        if (score >= 50) return "bg-yellow-400"
        return "bg-red-400"
    }

    const scoreLabel = (score: number) => {
        if (score >= 80) return "Excellent"
        if (score >= 65) return "Good — a few improvements will help"
        if (score >= 50) return "Fair — needs work"
        return "Poor — significant gaps found"
    }

    return (
        <div className="min-h-screen bg-[#fafaf7]">
            <AppNav />

            <main className="max-w-5xl mx-auto px-6 py-10">
                <div className="mb-8">
                    <h2 className="text-2xl font-bold text-gray-900 mb-1">Resume Analyzer</h2>
                    <p className="text-gray-500 text-sm">Upload your resume and paste a job description to get a detailed ATS analysis.</p>
                </div>

                {/* Input Section */}
                {!results && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                        {/* Resume Input */}
                        <div>
                            <div className="flex gap-2 mb-3">
                                <button
                                    onClick={() => setMode("upload")}
                                    className={`px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors ${mode === "upload" ? "bg-black text-white border-black" : "bg-white text-gray-600 border-gray-300"}`}
                                >
                                    Upload File
                                </button>
                                <button
                                    onClick={() => setMode("paste")}
                                    className={`px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors ${mode === "paste" ? "bg-black text-white border-black" : "bg-white text-gray-600 border-gray-300"}`}
                                >
                                    Paste Text
                                </button>
                            </div>

                            {mode === "upload" ? (
                                <div
                                    className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-gray-400 transition-colors"
                                    onClick={() => document.getElementById("resume-file")?.click()}
                                    onDragOver={(e) => e.preventDefault()}
                                    onDrop={(e) => {
                                        e.preventDefault()
                                        const f = e.dataTransfer.files[0]
                                        if (f) setFile(f)
                                    }}
                                >
                                    <input
                                        id="resume-file"
                                        type="file"
                                        accept=".pdf,.docx"
                                        className="hidden"
                                        onChange={(e) => setFile(e.target.files?.[0] || null)}
                                    />
                                    {file ? (
                                        <div>
                                            <p className="text-green-600 font-medium">✓ {file.name}</p>
                                            <p className="text-gray-400 text-xs mt-1">Click to change file</p>
                                        </div>
                                    ) : (
                                        <div>
                                            <p className="text-2xl mb-2">📄</p>
                                            <p className="text-gray-500 text-sm mb-1">Drop your resume here</p>
                                            <p className="text-gray-400 text-xs">PDF or DOCX supported</p>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div>
                                    <label className="text-sm font-medium text-gray-700 mb-2 block">Your Resume</label>
                                    <textarea
                                        value={resumeText}
                                        onChange={(e) => setResumeText(e.target.value)}
                                        placeholder="Paste your resume text here..."
                                        rows={12}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-black resize-none"
                                    />
                                </div>
                            )}
                        </div>

                        {/* JD Input */}
                        <div>
                            <label className="text-sm font-medium text-gray-700 mb-2 block">Job Description</label>
                            <textarea
                                value={jobDescription}
                                onChange={(e) => setJobDescription(e.target.value)}
                                placeholder="Paste the job description here..."
                                rows={14}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-black resize-none"
                            />
                        </div>
                    </div>
                )}

                {!results && (
                    <Button onClick={analyze} disabled={loading} className="w-full mb-8">
                        {loading ? "Analyzing..." : "Analyze Resume"}
                    </Button>
                )}

                {/* Results */}
                {results && (
                    <div className="space-y-6">

                        {/* Re-analyze button */}
                        <div className="flex justify-end">
                            <Button variant="outline" size="sm" onClick={() => setResults(null)}>
                                ← Analyze Another
                            </Button>
                        </div>

                        {/* Overall Score */}
                        <div className="bg-white border rounded-2xl p-8 flex flex-col md:flex-row items-center gap-8">
                            {/* Circle */}
                            <div className="relative w-32 h-32 flex-shrink-0">
                                <svg className="w-32 h-32 -rotate-90" viewBox="0 0 120 120">
                                    <circle cx="60" cy="60" r="50" fill="none" stroke="#f3f4f6" strokeWidth="10" />
                                    <circle
                                        cx="60" cy="60" r="50" fill="none"
                                        stroke={results.overall_score >= 75 ? "#22c55e" : results.overall_score >= 50 ? "#eab308" : "#ef4444"}
                                        strokeWidth="10"
                                        strokeDasharray={`${(results.overall_score / 100) * 314} 314`}
                                        strokeLinecap="round"
                                    />
                                </svg>
                                <div className="absolute inset-0 flex flex-col items-center justify-center">
                                    <span className={`text-3xl font-bold ${scoreColor(results.overall_score)}`}>
                                        {results.overall_score}
                                    </span>
                                    <span className="text-xs text-gray-400">/100</span>
                                </div>
                            </div>

                            {/* Breakdown */}
                            <div className="flex-1 w-full">
                                <p className="text-lg font-semibold text-gray-900 mb-1">Overall ATS Score</p>
                                <p className="text-gray-500 text-sm mb-4">{scoreLabel(results.overall_score)}</p>
                                <div className="space-y-3">
                                    {[
                                        { label: "Tech Skills Match (45%)", score: results.breakdown.tech_skills_match },
                                        { label: "Role Keywords (25%)", score: results.breakdown.role_keywords },
                                        { label: "Resume Quality (20%)", score: results.breakdown.resume_quality },
                                        { label: "ATS Essentials (10%)", score: results.breakdown.ats_essentials },
                                    ].map(({ label, score }) => (
                                        <div key={label}>
                                            <div className="flex justify-between text-xs text-gray-600 mb-1">
                                                <span>{label}</span>
                                                <span className={`font-semibold ${scoreColor(score)}`}>{score}%</span>
                                            </div>
                                            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full rounded-full transition-all ${scoreBarColor(score)}`}
                                                    style={{ width: `${score}%` }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Tech Skills */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="bg-white border rounded-2xl p-6">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="font-semibold text-gray-900">✅ Matched Tech Skills</h3>
                                    <span className="text-xs bg-green-50 text-green-700 border border-green-200 px-2 py-1 rounded-full">
                                        {results.tech_skills.matched_total}/{results.tech_skills.jd_total} required
                                    </span>
                                </div>
                                {results.tech_skills.matched.length > 0 ? (
                                    <div className="flex flex-wrap gap-2">
                                        {results.tech_skills.matched.map((skill: string) => (
                                            <span key={skill} className="bg-green-50 text-green-700 border border-green-200 px-3 py-1 rounded-full text-sm">
                                                {skill}
                                            </span>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-gray-400 text-sm">No matching tech skills found</p>
                                )}
                            </div>

                            <div className="bg-white border rounded-2xl p-6">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="font-semibold text-gray-900">❌ Missing Tech Skills</h3>
                                    <span className="text-xs bg-red-50 text-red-600 border border-red-200 px-2 py-1 rounded-full">
                                        {results.tech_skills.missing.length} gaps
                                    </span>
                                </div>
                                {results.tech_skills.missing.length > 0 ? (
                                    <div className="flex flex-wrap gap-2">
                                        {results.tech_skills.missing.map((skill: string) => (
                                            <span key={skill} className="bg-red-50 text-red-600 border border-red-200 px-3 py-1 rounded-full text-sm">
                                                {skill}
                                            </span>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-green-600 text-sm">All required tech skills found 🎉</p>
                                )}
                            </div>
                        </div>

                        {/* Role Keywords */}
                        {(results.role_keywords.matched.length > 0 || results.role_keywords.missing.length > 0) && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="bg-white border rounded-2xl p-6">
                                    <h3 className="font-semibold text-gray-900 mb-4">✅ Matched Role Keywords</h3>
                                    {results.role_keywords.matched.length > 0 ? (
                                        <div className="flex flex-wrap gap-2">
                                            {results.role_keywords.matched.map((kw: string) => (
                                                <span key={kw} className="bg-green-50 text-green-700 border border-green-200 px-3 py-1 rounded-full text-sm capitalize">
                                                    {kw}
                                                </span>
                                            ))}
                                        </div>
                                    ) : (
                                        <p className="text-gray-400 text-sm">No matching role keywords found</p>
                                    )}
                                </div>

                                <div className="bg-white border rounded-2xl p-6">
                                    <h3 className="font-semibold text-gray-900 mb-4">❌ Missing Role Keywords</h3>
                                    {results.role_keywords.missing.length > 0 ? (
                                        <div className="flex flex-wrap gap-2">
                                            {results.role_keywords.missing.map((kw: string) => (
                                                <span key={kw} className="bg-red-50 text-red-600 border border-red-200 px-3 py-1 rounded-full text-sm capitalize">
                                                    {kw}
                                                </span>
                                            ))}
                                        </div>
                                    ) : (
                                        <p className="text-green-600 text-sm">Great keyword coverage 🎉</p>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Resume Quality */}
                        <div className="bg-white border rounded-2xl p-6">
                            <h3 className="font-semibold text-gray-900 mb-4">📝 Resume Quality</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {results.quality.strengths.length > 0 && (
                                    <div>
                                        <p className="text-xs font-semibold text-green-700 uppercase tracking-wider mb-2">Strengths</p>
                                        <ul className="space-y-1.5">
                                            {results.quality.strengths.map((s: string, i: number) => (
                                                <li key={i} className="text-sm text-gray-700 flex gap-2">
                                                    <span className="text-green-500 mt-0.5">✓</span>
                                                    <span>{s}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                                {results.quality.issues.length > 0 && (
                                    <div>
                                        <p className="text-xs font-semibold text-red-600 uppercase tracking-wider mb-2">Issues</p>
                                        <ul className="space-y-1.5">
                                            {results.quality.issues.map((s: string, i: number) => (
                                                <li key={i} className="text-sm text-gray-700 flex gap-2">
                                                    <span className="text-red-400 mt-0.5">✗</span>
                                                    <span>{s}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                            <div className="flex gap-6 mt-4 pt-4 border-t text-sm text-gray-500">
                                <span>Words: <strong className="text-gray-900">{results.quality.word_count}</strong></span>
                                <span>Metrics: <strong className="text-gray-900">{results.quality.metrics_count}</strong></span>
                                <span>Action verbs: <strong className="text-gray-900">{results.quality.action_verbs_count}</strong></span>
                            </div>
                        </div>

                        {/* ATS Essentials */}
                        <div className="bg-white border rounded-2xl p-6">
                            <h3 className="font-semibold text-gray-900 mb-4">🤖 ATS Essentials</h3>
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                {results.ats.checks.map((check: any, i: number) => (
                                    <div key={i} className={`flex items-center gap-2 text-sm px-3 py-2 rounded-lg border ${check.pass ? "bg-green-50 border-green-200 text-green-700" : "bg-red-50 border-red-200 text-red-600"}`}>
                                        <span>{check.pass ? "✓" : "✗"}</span>
                                        <span>{check.label}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Sections */}
                        <div className="bg-white border rounded-2xl p-6">
                            <h3 className="font-semibold text-gray-900 mb-4">📋 Resume Sections</h3>
                            <div className="flex flex-wrap gap-2">
                                {results.sections.found.map((s: string) => (
                                    <span key={s} className="bg-green-50 text-green-700 border border-green-200 px-3 py-1 rounded-full text-sm capitalize">✓ {s}</span>
                                ))}
                                {results.sections.missing.map((s: string) => (
                                    <span key={s} className="bg-gray-50 text-gray-400 border border-gray-200 px-3 py-1 rounded-full text-sm capitalize">✗ {s}</span>
                                ))}
                            </div>
                        </div>

                    </div>
                )}
            </main>
        </div>
    )
}