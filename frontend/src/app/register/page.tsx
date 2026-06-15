"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"

export default function RegisterPage() {
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const router = useRouter()

  const handleRegister = async () => {
    const res = await fetch("http://localhost:8000/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    })
    const data = await res.json()
    if (data.id) {
      router.push("/login")
    } else {
      alert("Registration failed")
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
            Create an account
          </h1>
          <p className="text-[#6e7682] text-sm mb-6">Start building your perfect resume</p>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-[#16191d]">Name</label>
              <input
                type="text"
                placeholder="John Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="mt-1 w-full px-3 py-2 border border-[#e3e1da] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#16191d] bg-white"
              />
            </div>
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
                onKeyDown={(e) => e.key === "Enter" && handleRegister()}
                className="mt-1 w-full px-3 py-2 border border-[#e3e1da] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#16191d] bg-white"
              />
            </div>

            <button
              onClick={handleRegister}
              className="w-full bg-[#16191d] text-white py-2.5 rounded-lg font-medium hover:bg-[#2a2d32] transition-colors"
            >
              Register
            </button>

            <p className="text-center text-sm text-[#6e7682]">
              Already have an account?{" "}
              <Link href="/login" className="text-[#16191d] font-medium hover:underline">
                Login
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}