"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const router = useRouter()

  const handleLogin = async () => {
    const res = await fetch(`http://localhost:8000/auth/login?email=${email}&password=${password}`, {
      method: "POST",
    })
    const data = await res.json()
    if (data.access_token) {
      localStorage.setItem("token", data.access_token)
      router.push("/dashboard")
    } else {
      alert("Login failed")
    }
  }

  return (
    <div className="min-h-screen bg-[#fafaf7] flex items-center justify-center">
      <div className="w-full max-w-md">

        <div className="text-center mb-8">
          <span className="font-bold text-2xl text-[#16191d]" style={{ fontFamily: "var(--font-display)" }}>
            ResumeX
          </span>
        </div>

        <div className="bg-white border border-[#e3e1da] rounded-2xl p-8">
          <h1 className="text-2xl font-bold text-[#16191d] mb-1" style={{ fontFamily: "var(--font-display)" }}>
            Welcome back
          </h1>
          <p className="text-[#6e7682] text-sm mb-6">Login to your ResumeX account</p>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-[#16191d]">Email</label>
              <input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 w-full px-3 py-2 border border-[#e3e1da] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#16191d] bg-white"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-[#16191d]">Password</label>
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleLogin()}
                className="mt-1 w-full px-3 py-2 border border-[#e3e1da] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#16191d] bg-white"
              />
            </div>

            <button
              onClick={handleLogin}
              className="w-full bg-[#16191d] text-white py-2.5 rounded-lg font-medium hover:bg-[#2a2d32] transition-colors"
            >
              Login
            </button>

            <p className="text-center text-sm text-[#6e7682]">
              Don't have an account?{" "}
              <Link href="/register" className="text-[#16191d] font-medium hover:underline">
                Register
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}