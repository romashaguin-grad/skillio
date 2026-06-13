"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function LandingPage() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("token");
    const role = localStorage.getItem("role");
    if (token && role === "candidate") {
      router.push("/dashboard");
    } else if (token && role === "recruiter") {
      router.push("/recruiter");
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Navbar */}
      <nav className="border-b border-gray-800 bg-gray-900 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">Skillio</h1>
        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="text-sm text-gray-400 hover:text-white transition"
          >
            Sign in
          </Link>
          <Link
            href="/register"
            className="text-sm bg-[#9400D3] hover:bg-[#7a00b0] transition text-white font-medium px-4 py-2 rounded-lg"
          >
            Get started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <div className="max-w-4xl mx-auto px-6 py-24 text-center space-y-6">
        <div className="inline-block bg-[#9400D3]/10 border border-[#9400D3]/20 text-[#ED80E9] text-xs font-medium px-3 py-1.5 rounded-full">
          Your AI Career Matchmaker
        </div>
        <h2 className="text-5xl font-bold leading-tight">
          Find jobs that actually
          <br />
          <span className="text-[#ED80E9]">match your skills</span>
        </h2>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto">
          Upload your resume and discover relevant opportunities through AI-powered semantic matching, designed to go beyond simple keyword searches.
        </p>
        <div className="flex items-center justify-center gap-4 pt-2">
          <Link
            href="/register?role=candidate"
            className="bg-[#9400D3] hover:bg-[#7a00b0] transition text-white font-medium px-6 py-3 rounded-lg"
          >
            Find jobs as a candidate
          </Link>
          <Link
            href="/register?role=recruiter"
            className="border border-gray-700 hover:border-gray-600 transition text-gray-300 font-medium px-6 py-3 rounded-lg"
          >
            Post jobs as a recruiter
          </Link>
        </div>
      </div>

      {/* Features */}
      <div className="max-w-5xl mx-auto px-6 pb-24 grid grid-cols-1 sm:grid-cols-3 gap-6">
        {[
          {
            title: "Resume Parsing",
            description:
              "Upload your resume and let AI automatically extract your skills, experience, and educational background.",
            icon: "📄",
          },
          {
            title: "Semantic Matching",
            description:
              "Jobs are semantically ranked using AI-powered embeddings, going beyond simple keyword matching to find more relevant opportunities.",
            icon: "🧠",
          },
          {
            title: "Application Tracking",
            description:
              "Track every application in one place and follow your progress through each stage of the hiring process—from applied to offered.",
            icon: "📊",
          },
        ].map((feature) => (
          <div
            key={feature.title}
            className="bg-gray-900 border border-gray-800 rounded-2xl p-6 space-y-3"
          >
            <div className="text-3xl">{feature.icon}</div>
            <h3 className="font-semibold text-lg">{feature.title}</h3>
            <p className="text-gray-400 text-sm leading-relaxed">{feature.description}</p>
          </div>
        ))}
      </div>

      {/* CTA */}
      <div className="border-t border-gray-800 bg-gray-900">
        <div className="max-w-3xl mx-auto px-6 py-16 text-center space-y-4">
          <h3 className="text-2xl font-bold">Ready to find your next role?</h3>
          <p className="text-gray-400">
            Create an account in seconds. No credit card required.
          </p>
          <Link
            href="/register"
            className="inline-block bg-[#9400D3] hover:bg-[#7a00b0] transition text-white font-medium px-6 py-3 rounded-lg mt-2"
          >
            Get started for free
          </Link>
        </div>
      </div>
    </div>
  );
}
