"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  requirements: string;
  salary_range: string;
  job_type: string;
  similarity_score?: number;
}

interface Profile {
  bio: string;
  skills: string[];
  experience: string;
  education: string;
  resume_url: string;
  resume_text: string;
}

interface Application {
  id: string;
  job_id: string;
  status: string;
  cover_note: string;
  applied_at: string;
  job_title: string;
  job_company: string;
  job_is_active: boolean;
}

interface SkillGap {
  missing_skills: string[];
  matching_skills: string[];
  match_score: number;
}

const PAGE_SIZE = 5;

export default function DashboardPage() {
  const router = useRouter();
  const { fullName, logout } = useAuthStore();

  const [jobs, setJobs] = useState<Job[]>([]);
  const [recommendations, setRecommendations] = useState<Job[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [appliedJobIds, setAppliedJobIds] = useState<Set<string>>(new Set());
  const [profile, setProfile] = useState<Profile | null>(null);
  const [activeTab, setActiveTab] = useState<"recommended" | "jobs" | "applications">("recommended");
  const [expandedJob, setExpandedJob] = useState<string | null>(null);
  const [skillGaps, setSkillGaps] = useState<Record<string, SkillGap>>({});

  const [search, setSearch] = useState("");
  const [location, setLocation] = useState("");
  const [jobType, setJobType] = useState("");
  const [page, setPage] = useState(0);

  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [applyingJob, setApplyingJob] = useState<Job | null>(null);
  const [coverLetter, setCoverLetter] = useState("");
  const [generatingCoverLetter, setGeneratingCoverLetter] = useState(false);
  const [submittingApplication, setSubmittingApplication] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const savedRole = localStorage.getItem("role");
    if (!token) {
      router.push("/login");
      return;
    }
    if (savedRole === "recruiter") {
      router.push("/recruiter");
      return;
    }
    if (savedRole !== "candidate") {
      router.push("/login");
      return;
    }
    fetchProfile().catch(() => setError("Failed to load profile. Please refresh."));
    fetchApplications().catch(() => setError("Failed to load applications. Please refresh."));
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [search, location, jobType, page]);

  async function fetchProfile() {
    try {
      const res = await api.get("/candidates/profile");
      setProfile(res.data);
      try {
        const recRes = await api.get("/recommendations/");
        setRecommendations(recRes.data);
      } catch {
        // No embedding yet
      }
    } catch (err) {
      console.error(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }

  async function fetchJobs() {
    try {
      const params = new URLSearchParams();
      if (search) params.append("search", search);
      if (location) params.append("location", location);
      if (jobType) params.append("job_type", jobType);
      params.append("skip", String(page * PAGE_SIZE));
      params.append("limit", String(PAGE_SIZE));
      const res = await api.get(`/jobs/?${params.toString()}`);
      setJobs(res.data);
    } catch (err) {
      console.error(err);
    }
  }

  async function fetchApplications() {
    try {
      const res = await api.get("/applications/my-applications");
      setApplications(res.data);
      setAppliedJobIds(new Set(res.data.map((a: Application) => a.job_id)));
    } catch (err) {
      console.error(err);
      throw err;
    }
  }

  async function fetchSkillGap(jobId: string) {
    if (skillGaps[jobId]) return;
    try {
      const res = await api.get(`/recommendations/skill-gap/${jobId}`);
      setSkillGaps((prev) => ({ ...prev, [jobId]: res.data }));
    } catch (err) {
      console.error(err);
    }
  }

  async function handleResumeUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadMsg("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      await api.post("/candidates/profile/resume", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadMsg("Resume uploaded and parsed successfully!");
      fetchProfile();
    } catch (err: any) {
      setUploadMsg(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function handleApplyClick(job: Job) {
    if (appliedJobIds.has(job.id)) return;
    setApplyingJob(job);
    setCoverLetter("");
    setGeneratingCoverLetter(true);
    try {
      const res = await api.post("/applications/generate-cover-letter", {
        job_id: job.id,
      });
      setCoverLetter(res.data.cover_letter);
    } catch (err: any) {
      setCoverLetter("");
    } finally {
      setGeneratingCoverLetter(false);
    }
  }

  async function handleSubmitApplication() {
    if (!applyingJob) return;
    setSubmittingApplication(true);
    try {
      await api.post("/applications/", {
        job_id: applyingJob.id,
        cover_note: coverLetter,
      });
      await fetchApplications();
      setApplyingJob(null);
      setCoverLetter("");
    } catch (err: any) {
      console.error(err);
    } finally {
      setSubmittingApplication(false);
    }
  }

  function handleLogout() {
    logout();
    router.push("/login");
  }

  const displayJobs = (activeTab === "recommended" ? recommendations : jobs)
    .filter((job) => !appliedJobIds.has(job.id));

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-gray-400 text-sm">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-red-400 text-sm">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Cover Letter Modal */}
      {applyingJob && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4">
          <div className="bg-gray-900 rounded-2xl border border-gray-800 w-full max-w-2xl p-6 space-y-4">
            <div>
              <h2 className="font-semibold text-lg">Apply to {applyingJob.title}</h2>
              <p className="text-gray-400 text-sm mt-0.5">{applyingJob.company}</p>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm text-gray-400">Cover Letter</label>
                {generatingCoverLetter && (
                  <span className="text-xs text-[#ED80E9] animate-pulse">
                    Generating with AI...
                  </span>
                )}
              </div>
              <textarea
                value={coverLetter}
                onChange={(e) => setCoverLetter(e.target.value)}
                rows={10}
                placeholder={generatingCoverLetter ? "Generating your cover letter..." : "Write your cover letter or wait for AI to generate one..."}
                disabled={generatingCoverLetter}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-[#9400D3] transition text-sm resize-none disabled:opacity-50"
              />
            </div>
            <div className="flex items-center gap-3 justify-end">
              <button
                onClick={() => { setApplyingJob(null); setCoverLetter(""); }}
                className="text-sm text-gray-400 hover:text-white transition px-4 py-2"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitApplication}
                disabled={submittingApplication || generatingCoverLetter}
                className="bg-[#9400D3] hover:bg-[#7a00b0] disabled:opacity-50 text-white text-sm font-medium px-6 py-2 rounded-lg transition"
              >
                {submittingApplication ? "Submitting..." : "Submit Application"}
              </button>
            </div>
          </div>
        </div>
      )}

      <nav className="border-b border-gray-800 bg-gray-900 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">Skillio</h1>
        <div className="flex items-center gap-4">
          <span className="text-gray-400 text-sm">Hi, {fullName}</span>
          <button onClick={handleLogout} className="text-sm text-gray-400 hover:text-white transition">
            Logout
          </button>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
        {/* Resume Upload */}
        <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h2 className="font-semibold text-lg">Your Resume</h2>
              <p className="text-gray-400 text-sm mt-1">
                {profile?.resume_url
                  ? "Resume uploaded. Upload a new one to refresh recommendations."
                  : "Upload your resume to get personalized job recommendations."}
              </p>
            </div>
            <label className="cursor-pointer bg-[#9400D3] hover:bg-[#7a00b0] transition text-white text-sm font-medium px-4 py-2 rounded-lg">
              {uploading ? "Uploading..." : "Upload Resume (PDF)"}
              <input
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={handleResumeUpload}
                disabled={uploading}
              />
            </label>
          </div>
          {uploadMsg && (
            <p className={`mt-3 text-sm ${uploadMsg.includes("success") ? "text-green-400" : "text-red-400"}`}>
              {uploadMsg}
            </p>
          )}
          {profile?.skills && profile.skills.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {profile.skills.map((skill) => (
                <span key={skill} className="bg-gray-800 text-gray-300 text-xs px-3 py-1 rounded-full">
                  {skill}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-gray-800">
          {[
            { key: "recommended", label: "Recommended for You" },
            { key: "jobs", label: "All Jobs" },
            { key: "applications", label: `My Applications (${applications.length})` },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`pb-3 px-1 text-sm font-medium border-b-2 transition ${
                activeTab === tab.key
                  ? "border-[#9400D3] text-[#ED80E9]"
                  : "border-transparent text-gray-500 hover:text-gray-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search and filters */}
        {activeTab === "jobs" && (
          <div className="flex flex-wrap gap-3">
            <input
              type="text"
              placeholder="Search jobs..."
              value={search}
              onChange={(e) => { setPage(0); setSearch(e.target.value); }}
              className="flex-1 min-w-48 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-[#9400D3] transition text-sm"
            />
            <input
              type="text"
              placeholder="Location..."
              value={location}
              onChange={(e) => { setPage(0); setLocation(e.target.value); }}
              className="w-40 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-[#9400D3] transition text-sm"
            />
            <select
              value={jobType}
              onChange={(e) => { setPage(0); setJobType(e.target.value); }}
              className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-[#9400D3] transition text-sm"
            >
              <option value="">All Types</option>
              <option value="Full-time">Full-time</option>
              <option value="Part-time">Part-time</option>
              <option value="Contract">Contract</option>
              <option value="Internship">Internship</option>
            </select>
          </div>
        )}

        {/* Recommended empty state */}
        {activeTab === "recommended" && recommendations.length === 0 && (
          <div className="text-center text-gray-500 py-12">
            Upload your resume to get personalized recommendations.
          </div>
        )}

        {/* Applications tab */}
        {activeTab === "applications" && (
          <div className="space-y-4">
            {applications.length === 0 && (
              <div className="text-center text-gray-500 py-12">
                You haven't applied to any jobs yet.
              </div>
            )}
            {applications.map((app) => (
              <div key={app.id} className="bg-gray-900 rounded-2xl p-6 border border-gray-800 flex items-start justify-between flex-wrap gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-white">{app.job_title}</p>
                    {!app.job_is_active && (
                      <span className="text-xs bg-gray-700 text-gray-400 px-2 py-0.5 rounded-full">Position closed</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-400 mt-0.5">{app.job_company}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Applied {new Date(app.applied_at).toLocaleDateString()}
                  </p>
                  {app.cover_note && (
                    <p className="text-sm text-gray-300 mt-2 leading-relaxed">{app.cover_note}</p>
                  )}
                </div>
                <span className={`text-xs font-medium px-3 py-1 rounded-full shrink-0 ${
                  app.status === "offered" ? "bg-green-500/10 text-green-400" :
                  app.status === "rejected" ? "bg-red-500/10 text-red-400" :
                  app.status === "reviewed" ? "bg-yellow-500/10 text-yellow-400" :
                  "bg-[#9400D3]/10 text-[#ED80E9]"
                }`}>
                  {app.status.charAt(0).toUpperCase() + app.status.slice(1)}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Job listings */}
        {activeTab !== "applications" && (
          <div className="space-y-4">
            {displayJobs.length === 0 && (
              <div className="text-center text-gray-500 py-12">
                No jobs found.
              </div>
            )}
            {displayJobs.map((job) => (
              <div
                key={job.id}
                className="bg-gray-900 rounded-2xl p-6 border border-gray-800 hover:border-gray-700 transition"
              >
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div>
                    <h3 className="font-semibold text-lg">{job.title}</h3>
                    <p className="text-gray-400 text-sm mt-1">
                      {job.company} · {job.location} · {job.job_type}
                    </p>
                    {job.salary_range && (
                      <p className="text-green-400 text-sm mt-1">{job.salary_range}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    {job.similarity_score !== undefined && (
                      <span className="text-xs text-[#ED80E9] bg-[#9400D3]/10 px-3 py-1 rounded-full">
                        {Math.round(job.similarity_score * 100)}% match
                      </span>
                    )}
                    <button
                      onClick={() => handleApplyClick(job)}
                      disabled={appliedJobIds.has(job.id)}
                      className="bg-[#9400D3] hover:bg-[#7a00b0] disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition"
                    >
                      {appliedJobIds.has(job.id) ? "Applied" : "Apply"}
                    </button>
                  </div>
                </div>
                <p className={`text-gray-400 text-sm mt-4 ${expandedJob === job.id ? "" : "line-clamp-2"}`}>
                  {job.description}
                </p>
                <button
                  onClick={() => {
                    const newExpanded = expandedJob === job.id ? null : job.id;
                    setExpandedJob(newExpanded);
                    if (newExpanded) fetchSkillGap(job.id);
                  }}
                  className="text-xs text-[#ED80E9] mt-1 hover:text-[#D3D3FF] transition"
                >
                  {expandedJob === job.id ? "Show less" : "Show more"}
                </button>
                {job.requirements && (
                  <p className="text-gray-500 text-xs mt-2">
                    <span className="text-gray-400">Requirements:</span> {job.requirements}
                  </p>
                )}
                {expandedJob === job.id && skillGaps[job.id] && (
                  <div className="mt-4 space-y-3">
                    {skillGaps[job.id].matching_skills.length > 0 && (
                      <div>
                        <p className="text-xs text-gray-400 mb-1.5">Skills you have:</p>
                        <div className="flex flex-wrap gap-1.5">
                          {skillGaps[job.id].matching_skills.map((skill) => (
                            <span key={skill} className="text-xs bg-green-500/10 text-green-400 px-2.5 py-1 rounded-full">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {skillGaps[job.id].missing_skills.length > 0 && (
                      <div>
                        <p className="text-xs text-gray-400 mb-1.5">Skills to develop:</p>
                        <div className="flex flex-wrap gap-1.5">
                          {skillGaps[job.id].missing_skills.map((skill) => (
                            <span key={skill} className="text-xs bg-red-500/10 text-red-400 px-2.5 py-1 rounded-full">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}

            {/* Pagination */}
            {activeTab === "jobs" && (
              <div className="flex items-center justify-center gap-3 pt-2">
                <button
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="px-4 py-2 text-sm bg-gray-800 rounded-lg disabled:opacity-40 hover:bg-gray-700 transition"
                >
                  Previous
                </button>
                <span className="text-sm text-gray-400">Page {page + 1}</span>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={jobs.length < PAGE_SIZE}
                  className="px-4 py-2 text-sm bg-gray-800 rounded-lg disabled:opacity-40 hover:bg-gray-700 transition"
                >
                  Next
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}