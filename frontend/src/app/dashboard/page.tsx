"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { jwtDecode } from "jwt-decode"
import AppNav from "@/components/AppNav"

interface TokenPayload {
  name: string
  email: string
}

const modules = [
  {
    title: "Resume Builder",
    desc: "Create ATS-friendly resumes with live preview and multiple templates.",
    href: "/builder",
    label: "01",
  },
  {
    title: "Resume Analyzer",
    desc: "Upload your resume and a job description to get an ATS score and keyword analysis.",
    href: "/analyzer",
    label: "02",
  },
  {
    title: "Resume Buddy",
    desc: "Store your career data once. Auto-generate tailored resumes for every job.",
    href: "/buddy",
    label: "03",
  },
]

export default function DashboardPage() {
  const router = useRouter()
  const [userName, setUserName] = useState("")

  useEffect(() => {
    const token = localStorage.getItem("token")
    if (!token) {
      router.push("/login")
      return
    }
    const decoded = jwtDecode<TokenPayload>(token)
    setUserName(decoded.name)
  }, [])

  return (
    <div className="min-h-screen bg-[#fafaf7]">
      <AppNav />

      <main className="max-w-5xl mx-auto px-6 py-12">
        <div className="mb-10">
          <p className="text-xs font-mono uppercase tracking-widest text-[#6e7682] mb-2">Welcome back</p>
          <h2
            className="text-3xl font-bold text-[#16191d]"
            style={{ fontFamily: "var(--font-display)" }}
          >
            {userName} 👋
          </h2>
        </div>

        <div className="text-xs font-mono uppercase tracking-widest text-[#6e7682] mb-4">Modules</div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {modules.map((m) => (
            <div
              key={m.href}
              onClick={() => router.push(m.href)}
              className="bg-white border border-[#e3e1da] rounded-2xl p-6 hover:shadow-md cursor-pointer transition-all hover:border-[#6e7682] group"
            >
              <div className="w-8 h-8 rounded-lg bg-[#d7fb3d] flex items-center justify-center text-xs font-mono font-bold text-[#16191d] mb-4">
                {m.label}
              </div>
              <h3
                className="font-bold text-[#16191d] mb-2"
                style={{ fontFamily: "var(--font-display)" }}
              >
                {m.title}
              </h3>
              <p className="text-sm text-[#6e7682] leading-relaxed">{m.desc}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}