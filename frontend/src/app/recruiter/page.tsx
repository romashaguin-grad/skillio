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
  is_active: boolean;
  created_at: string;
}

interface Application {
  id: string;
  candidate_id: string;
  candidate_name: string;
  candidate_email: string;
  candidate_resume_url: string;
  match_score: number;
  status: string;
  cover_note: string;
  applied_at: string;
}

const emptyForm = {
  title: "",
  company: "",
  location: "Remote",
  description: "",
  requirements: "",
  salary_range: "",
  job_type: "Full-time",
};

type JobForm = typeof emptyForm;
type JobFormField = keyof JobForm;

const formFields: {
  name: JobFormField;
  label: string;
  placeholder: string;
}[] = [
  { name: "title", label: "Job Title", placeholder: "Backend Engineer" },
  { name: "company", label: "Company", placeholder: "Acme Corp" },
  { name: "location", label: "Location", placeholder: "Remote" },
  { name: "salary_range", label: "Salary Range", placeholder: "$100k - $130k" },
];

function getErrorMessage(err: unknown, fallback: string) {
  if (typeof err === "object" && err !== null && "response" in err) {
    const response = (err as { response?: { data?: { detail?: string } } }).response;
    return response?.data?.detail || fallback;
  }

  return fallback;
}

export default function RecruiterPage() {
  const router = useRouter();
  const { fullName, logout } = useAuthStore();

  const [jobs, setJobs] = useState<Job[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [posting, setPosting] = useState(false);
  const [postMsg, setPostMsg] = useState("");
  const [selectedJob, setSelectedJob] = useState<string | null>(null);
  const [applications, setApplications] = useState<Application[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusMsg, setStatusMsg] = useState("");
  const [expandedJob, setExpandedJob] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const savedRole = localStorage.getItem("role");
    if (!token) {
      router.push("/login");
      return;
    }
    if (savedRole === "candidate") {
      router.push("/dashboard");
      return;
    }
    if (savedRole !== "recruiter") {
      router.push("/login");
      return;
    }
    fetchJobs().catch(() => setError("Failed to load jobs. Please refresh."));
  }, [router]);

  async function fetchJobs() {
    try {
      const res = await api.get("/jobs/recruiter/my-jobs");
      // Show all jobs, both active and inactive
      setJobs(res.data);
    } catch (err) {
      console.error(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }

  async function fetchApplications(jobId: string) {
    try {
      const res = await api.get(`/applications/job/${jobId}`);
      setApplications(res.data);
      setSelectedJob(jobId);
    } catch (err) {
      console.error(err);
    }
  }

  async function handlePost(e: React.FormEvent) {
    e.preventDefault();
    setPosting(true);
    setPostMsg("");
    try {
      await api.post("/jobs/", form);
      setPostMsg("Job posted successfully!");
      setForm(emptyForm);
      setShowForm(false);
      fetchJobs();
    } catch (err: unknown) {
      setPostMsg(getErrorMessage(err, "Failed to post job"));
    } finally {
      setPosting(false);
    }
  }

  async function handleToggle(jobId: string) {
    try {
      await api.patch(`/jobs/${jobId}/toggle`);
      if (selectedJob === jobId) setSelectedJob(null);
      fetchJobs();
    } catch (err) {
      console.error(err);
    }
  }

  async function handleStatusUpdate(applicationId: string, status: string) {
    try {
      await api.patch(`/applications/${applicationId}/status`, { status });
      setStatusMsg("Status updated!");
      setTimeout(() => setStatusMsg(""), 3000);
      if (selectedJob) fetchApplications(selectedJob);
    } catch (err) {
      console.error(err);
    }
  }

  function handleLogout() {
    logout();
    router.push("/login");
  }

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

  const activeJobs = jobs.filter((j) => j.is_active);
  const closedJobs = jobs.filter((j) => !j.is_active);

  return (
    <div className="min-h-screen bg-gray-950 text-white">
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
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">Your Job Postings</h2>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-[#9400D3] hover:bg-[#7a00b0] transition text-white text-sm font-medium px-4 py-2 rounded-lg"
          >
            {showForm ? "Cancel" : "+ Post a Job"}
          </button>
        </div>

        {showForm && (
          <form
            onSubmit={handlePost}
            className="bg-gray-900 rounded-2xl p-6 border border-gray-800 space-y-4"
          >
            <h3 className="font-semibold text-lg">New Job Posting</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {formFields.map((field) => (
                <div key={field.name}>
                  <label className="block text-sm text-gray-400 mb-1.5">{field.label}</label>
                  <input
                    type="text"
                    value={form[field.name]}
                    onChange={(e) => setForm({ ...form, [field.name]: e.target.value })}
                    placeholder={field.placeholder}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-[#9400D3] transition"
                  />
                </div>
              ))}
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1.5">Job Type</label>
              <select
                value={form.job_type}
                onChange={(e) => setForm({ ...form, job_type: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-[#9400D3] transition"
              >
                <option>Full-time</option>
                <option>Part-time</option>
                <option>Contract</option>
                <option>Internship</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1.5">Description</label>
              <textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                required
                rows={4}
                placeholder="Describe the role..."
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-[#9400D3] transition resize-none"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1.5">Requirements</label>
              <textarea
                value={form.requirements}
                onChange={(e) => setForm({ ...form, requirements: e.target.value })}
                rows={2}
                placeholder="Python, FastAPI, Docker..."
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-[#9400D3] transition resize-none"
              />
            </div>
            {postMsg && (
              <p className={`text-sm ${postMsg.includes("success") ? "text-green-400" : "text-red-400"}`}>
                {postMsg}
              </p>
            )}
            <button
              type="submit"
              disabled={posting}
              className="bg-[#9400D3] hover:bg-[#7a00b0] disabled:opacity-50 text-white font-medium px-6 py-2.5 rounded-lg transition"
            >
              {posting ? "Posting..." : "Post Job"}
            </button>
          </form>
        )}

        {/* Active jobs */}
        {activeJobs.length === 0 && closedJobs.length === 0 && (
          <div className="text-center text-gray-500 py-12">
            No jobs posted yet. Click &quot;+ Post a Job&quot; to get started.
          </div>
        )}

        {activeJobs.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">Active</h3>
            {activeJobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                selectedJob={selectedJob}
                applications={applications}
                expandedJob={expandedJob}
                statusMsg={statusMsg}
                onToggle={handleToggle}
                onFetchApplications={fetchApplications}
                onSetSelectedJob={setSelectedJob}
                onSetExpandedJob={setExpandedJob}
                onStatusUpdate={handleStatusUpdate}
              />
            ))}
          </div>
        )}

        {/* Closed jobs */}
        {closedJobs.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">Closed</h3>
            {closedJobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                selectedJob={selectedJob}
                applications={applications}
                expandedJob={expandedJob}
                statusMsg={statusMsg}
                onToggle={handleToggle}
                onFetchApplications={fetchApplications}
                onSetSelectedJob={setSelectedJob}
                onSetExpandedJob={setExpandedJob}
                onStatusUpdate={handleStatusUpdate}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function JobCard({
  job,
  selectedJob,
  applications,
  expandedJob,
  statusMsg,
  onToggle,
  onFetchApplications,
  onSetSelectedJob,
  onSetExpandedJob,
  onStatusUpdate,
}: {
  job: Job;
  selectedJob: string | null;
  applications: Application[];
  expandedJob: string | null;
  statusMsg: string;
  onToggle: (id: string) => void;
  onFetchApplications: (id: string) => void;
  onSetSelectedJob: (id: string | null) => void;
  onSetExpandedJob: (id: string | null) => void;
  onStatusUpdate: (id: string, status: string) => void;
}) {
  return (
    <div className={`bg-gray-900 rounded-2xl p-6 border transition ${
      job.is_active ? "border-gray-800 hover:border-gray-700" : "border-gray-800 opacity-60"
    }`}>
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-lg">{job.title}</h3>
            {!job.is_active && (
              <span className="text-xs bg-gray-700 text-gray-400 px-2 py-0.5 rounded-full">Closed</span>
            )}
          </div>
          <p className="text-gray-400 text-sm mt-1">
            {job.company} · {job.location} · {job.job_type}
          </p>
          {job.salary_range && (
            <p className="text-green-400 text-sm mt-1">{job.salary_range}</p>
          )}
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={() =>
              selectedJob === job.id
                ? onSetSelectedJob(null)
                : onFetchApplications(job.id)
            }
            className="text-sm text-[#ED80E9] hover:text-[#D3D3FF] transition"
          >
            {selectedJob === job.id ? "Hide applicants" : "View applicants"}
          </button>
          <button
            onClick={() => onToggle(job.id)}
            className={`text-sm transition ${
              job.is_active
                ? "text-red-400 hover:text-red-300"
                : "text-green-400 hover:text-green-300"
            }`}
          >
            {job.is_active ? "Close" : "Reactivate"}
          </button>
        </div>
      </div>

      <p className={`text-gray-400 text-sm mt-4 ${expandedJob === job.id ? "" : "line-clamp-2"}`}>
        {job.description}
      </p>
      <button
        onClick={() => onSetExpandedJob(expandedJob === job.id ? null : job.id)}
        className="text-xs text-[#ED80E9] mt-1 hover:text-[#D3D3FF] transition"
      >
        {expandedJob === job.id ? "Show less" : "Show more"}
      </button>

      {selectedJob === job.id && (
        <div className="mt-6 border-t border-gray-800 pt-4 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-gray-300">
              Applicants ({applications.length}) -- ranked by match
            </h4>
            {statusMsg && <p className="text-green-400 text-xs">{statusMsg}</p>}
          </div>
          {applications.length === 0 && (
            <p className="text-gray-500 text-sm">No applicants yet.</p>
          )}
          {applications.map((app) => (
            <div key={app.id} className="bg-gray-800 rounded-xl px-4 py-4 space-y-3">
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div>
                  <p className="text-sm text-white font-medium">{app.candidate_name}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{app.candidate_email}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Applied {new Date(app.applied_at).toLocaleDateString()}
                  </p>
                  {app.cover_note && (
                    <p className="text-xs text-gray-400 mt-1">{app.cover_note}</p>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  {app.match_score > 0 && (
                    <span className="text-xs text-[#ED80E9] bg-[#9400D3]/10 px-3 py-1 rounded-full">
                      {Math.round(app.match_score * 100)}% match
                    </span>
                  )}
                  {app.candidate_resume_url && (
                    <a
                      href={app.candidate_resume_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-400 hover:text-blue-300 transition underline"
                    >
                      View Resume
                    </a>
                  )}
                </div>
              </div>
              <div className="flex justify-end">
                <select
                  value={app.status}
                  onChange={(e) => onStatusUpdate(app.id, e.target.value)}
                  className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-[#9400D3] transition"
                >
                  <option value="applied">Applied</option>
                  <option value="reviewed">Reviewed</option>
                  <option value="rejected">Rejected</option>
                  <option value="offered">Offered</option>
                </select>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
