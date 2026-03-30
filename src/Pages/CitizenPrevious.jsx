import React, { useEffect, useState, useRef } from "react";
import ReactMarkdown from "react-markdown";
import Navbar from "../components/Navbar";
import CitizenNav from "../components/CitizenNav";
import api from "../services/api";

export default function CitizenPrevious() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedId, setExpandedId] = useState(null);
  const [showRatingModal, setShowRatingModal] = useState(false);
  const [ratingTarget, setRatingTarget] = useState(null);
  const [ratings, setRatings] = useState({ overall: 5, speed: 5, quality: 5 });
  const [feedbackComment, setFeedbackComment] = useState("");
  const [evidenceFile, setEvidenceFile] = useState(null);
  const [evidencePreview, setEvidencePreview] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [submitSuccess, setSubmitSuccess] = useState(null);
  const [pendingForms, setPendingForms] = useState(new Set());
  const [pendingLoaded, setPendingLoaded] = useState(false);
  const fileInputRef = useRef(null);

  // Helper to robustly resolve an identifier for a grievance item
  const resolveId = (it) => {
    if (!it) return null;
    return (
      it.form_id ||
      it.id ||
      it._id?.$oid ||
      it._id ||
      it.formId ||
      it.ticket_id ||
      it.ticketId ||
      null
    );
  };

  const formatDate = (v) => {
    if (!v) return "-";
    try {
      const raw = typeof v === "string" ? v : v?.$date || v;
      const d = new Date(raw);
      if (isNaN(d)) return String(v);
      return d.toLocaleString();
    } catch {
      return String(v);
    }
  };

  const buildImageUrl = (p) => {
    if (!p) return null;
    if (typeof p !== "string") return null;
    if (p.startsWith("http")) return p;
    const cleaned = p.replace(/^\.\/?/, "").replace(/\\/g, "/");
    return `${api.defaults.baseURL.replace(/\/$/, "")}/${cleaned}`;
  };

  useEffect(() => {
    let mounted = true;
    const tryEndpoints = async () => {
      setLoading(true);
      setError(null);
      // detect current user and prefer user-scoped endpoints
      let userId = null;
      try {
        const me = await api.get("/users/me");
        if (me?.data && (me.data.id || me.data.user_id))
          userId = me.data.id || me.data.user_id;
      } catch {
        // ignore
      }
      // prefer official grievance endpoints first
      const endpoints = [
        "/grievance/forms",
        "/grievance/forms?status=resolved",
        "/grievance/list",
        "/grievance/my/forms",
      ];
      if (userId)
        endpoints.push(`/users/${userId}/grievances`, `/users/${userId}/forms`);
      for (const ep of endpoints) {
        try {
          const res = await api.get(ep);
          const data = res.data;
          let list = [];
          if (Array.isArray(data)) list = data;
          else if (data && Array.isArray(data.items)) list = data.items;
          else if (data && Array.isArray(data.results)) list = data.results;
          if (list.length > 0) {
            if (!mounted) return;
            // filter resolved/completed/closed
            const resolved = list.filter((i) => {
              const s = (i.status || i.ticket_status || "")
                .toString()
                .toLowerCase();
              return (
                s.includes("resolv") ||
                s.includes("resolved") ||
                s.includes("completed") ||
                s.includes("closed") ||
                s.includes("complete")
              );
            });
            setItems(resolved.length > 0 ? resolved : []);
            setLoading(false);
            return;
          }
        } catch {
          // ignore
        }
      }
      if (mounted) setLoading(false);
    };
    tryEndpoints();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    let mounted = true;
    const fetchPending = async () => {
      try {
        const res = await api.get("/feedback/pending");
        const list = Array.isArray(res.data) ? res.data : [];
        if (!mounted) return;
        setPendingForms(new Set(list.map((d) => d.form_id)));
      } catch {
        // ignore failure - leave set empty
      } finally {
        if (mounted) setPendingLoaded(true);
      }
    };
    fetchPending();
    return () => {
      mounted = false;
    };
  }, []);

  const openRatingModal = (item) => {
    const id = resolveId(item);
    if (!id) return;
    // If pending loaded and this form is not pending => already rated
    if (pendingLoaded && !pendingForms.has(id)) {
      // show a quick toast / skip opening modal - optional
      return;
    }
    setRatingTarget(item);
    setRatings({ overall: 5, speed: 5, quality: 5 });
    setFeedbackComment("");
    setEvidenceFile(null);
    setEvidencePreview(null);
    setSubmitError(null);
    setSubmitSuccess(null);
    setShowRatingModal(true);
  };

  const closeRatingModal = () => {
    setShowRatingModal(false);
    if (evidencePreview) {
      URL.revokeObjectURL(evidencePreview);
      setEvidencePreview(null);
    }
  };

  const handleEvidenceChange = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setEvidenceFile(f);
    const url = URL.createObjectURL(f);
    setEvidencePreview(url);
  };

  const submitRating = async () => {
    if (!ratingTarget) return;
    const formId = resolveId(ratingTarget);
    if (!formId) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const payload = {
        form_id: formId,
        ratings: { ...ratings },
        is_resolved_by_user: true,
        user_comment: feedbackComment || undefined,
      };
      const fd = new FormData();
      fd.append("feedback_data", JSON.stringify(payload));
      if (evidenceFile) fd.append("evidence", evidenceFile);

      const res = await api.post("/feedback/submit", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setSubmitSuccess("Feedback submitted successfully");
      // Remove from pending set (if present)
      setPendingForms((prev) => {
        const s = new Set(prev);
        s.delete(formId);
        return s;
      });

      // Update local item flag so UI can reflect rating done
      setItems((prev) =>
        prev.map((p) =>
          resolveId(p) === formId ? { ...p, _rated_by_user: true } : p
        )
      );

      closeRatingModal();
    } catch (err) {
      setSubmitError(
        err?.response?.data?.detail ||
          err?.response?.data ||
          err.message ||
          "Failed to submit"
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-green-50 to-slate-100">
      <Navbar />
      <div className="max-w-6xl mx-auto px-4 py-8">
        <CitizenNav />

        {/* Header */}
        <div className="mb-8 animate-fade-in-up">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-3xl font-bold bg-gradient-to-r from-green-600 to-green-800 bg-clip-text text-transparent">
                Previous Grievances
              </h2>
              <p className="text-slate-600 mt-1">
                View your resolved and completed complaints
              </p>
            </div>
            <div className="px-4 py-2 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl font-bold shadow-lg">
              {items.length} Resolved
            </div>
          </div>
        </div>

        {loading && (
          <div className="bg-gradient-to-r from-green-500 to-green-600 text-white p-6 rounded-2xl mb-6 shadow-xl animate-pulse">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 border-4 border-white/30 border-t-white rounded-full animate-spin"></div>
              <span className="font-medium">
                Loading previous grievances...
              </span>
            </div>
          </div>
        )}
        {error && (
          <div className="bg-gradient-to-r from-red-500 to-red-600 text-white p-6 rounded-2xl mb-6 shadow-xl">
            <div className="flex items-center gap-3">
              <span className="text-2xl">⚠️</span>
              <span className="font-medium">{String(error)}</span>
            </div>
          </div>
        )}

        {items.length === 0 && !loading && (
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-slate-200 shadow-xl p-12 text-center animate-fade-in-up">
            <div className="w-24 h-24 bg-gradient-to-br from-green-100 to-blue-100 rounded-full mx-auto mb-6 flex items-center justify-center">
              <span className="text-5xl">✅</span>
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-2">
              No Previous Grievances
            </h3>
            <p className="text-slate-600 mb-6">
              You don't have any resolved complaints yet
            </p>
            <a
              href="/citizen/current"
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200"
            >
              View Current Grievances
            </a>
          </div>
        )}

        <div className="space-y-4">
          {items.map((t, idx) => {
            const itemId = resolveId(t);
            const isExpanded = itemId === expandedId;
            const resolvedDate =
              t.resolved_at || t.resolved_on || t.resolvedOn || t.closed_at;

            const handleToggle = async (e) => {
              e.stopPropagation();
              try {
                const id = resolveId(t);
                if (!id) return;
                const res = await (
                  await import("../services/api")
                ).grievanceAPI.getForm(id);
                const updated = res?.data || res;
                setItems((prev) =>
                  prev.map((p) =>
                    resolveId(p) === id
                      ? { ...p, ...updated, form_id: updated.form_id || id }
                      : p
                  )
                );
                setExpandedId(isExpanded ? null : id);
              } catch (e) {
                console.error("Failed to refresh grievance", e);
              }
            };

            return (
              <div
                key={itemId || `prev-${idx}`}
                className="bg-white/80 backdrop-blur-sm rounded-2xl border border-slate-200 shadow-lg hover:shadow-2xl transition-all duration-300 cursor-pointer group animate-fade-in-up overflow-hidden"
                style={{ animationDelay: `${idx * 0.1}s` }}
              >
                <div className="p-6">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="px-3 py-1 bg-slate-100 text-slate-600 rounded-full text-xs font-mono font-semibold">
                          {itemId}
                        </span>
                        <span className="px-3 py-1 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-full text-xs font-bold shadow-md flex items-center gap-1">
                          <span className="text-lg">✓</span>
                          {t.status || t.ticket_status || "Resolved"}
                        </span>
                      </div>
                      <h3 className="text-lg font-bold text-slate-800 group-hover:text-green-600 transition-colors mb-1">
                        {t.title ||
                          t.subject ||
                          t.extracted_data?.title ||
                          "Untitled Grievance"}
                      </h3>
                      <p className="text-sm text-slate-600">
                        {t.category && (
                          <span className="font-medium">{t.category}</span>
                        )}
                        {t.category && t.priority && (
                          <span className="mx-2">•</span>
                        )}
                        {t.priority && (
                          <span className="font-medium">
                            Priority: {t.priority}
                          </span>
                        )}
                      </p>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-xs text-slate-500 mb-1">
                          Resolved On
                        </div>
                        <div className="font-semibold text-slate-800 text-sm">
                          {resolvedDate
                            ? formatDate(resolvedDate?.$date || resolvedDate)
                            : "—"}
                        </div>
                      </div>
                      <div
                        className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center group-hover:bg-green-200 transition-colors cursor-pointer"
                        onClick={handleToggle}
                      >
                        <span
                          className={`text-green-600 transform transition-transform duration-200 ${
                            isExpanded ? "rotate-180" : ""
                          }`}
                        >
                          ▼
                        </span>
                      </div>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="mt-6 p-6 bg-gradient-to-br from-slate-50 to-green-50 rounded-xl border border-slate-200 animate-fade-in-up">
                      <div className="grid md:grid-cols-4 gap-4 mb-4">
                        <div className="bg-white/80 p-4 rounded-xl shadow-sm">
                          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide">
                            Category
                          </div>
                          <div className="font-semibold text-slate-800">
                            {t.category || "-"}
                          </div>
                        </div>
                        <div className="bg-white/80 p-4 rounded-xl shadow-sm">
                          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide">
                            Priority
                          </div>
                          <div className="font-semibold text-slate-800">
                            {t.priority || "-"}
                          </div>
                        </div>
                        <div className="bg-white/80 p-4 rounded-xl shadow-sm">
                          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide">
                            Assigned Officer
                          </div>
                          <div className="font-semibold text-slate-800">
                            {t.assigned_officer_name || "-"}
                          </div>
                        </div>
                        <div className="bg-white/80 p-4 rounded-xl shadow-sm">
                          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide">
                            Status
                          </div>
                          <div className="font-semibold text-green-700 flex items-center gap-2">
                            <span className="text-lg">✓</span>
                            {t.status || "Resolved"}
                          </div>
                        </div>
                        <div className="bg-white/80 p-4 rounded-xl shadow-sm">
                          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide">
                            Response Time
                          </div>
                          <div className="font-semibold text-slate-800">
                            {t.estimated_response_time || t.eta || "-"}
                          </div>
                        </div>
                        <div className="bg-white/80 p-4 rounded-xl shadow-sm">
                          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide">
                            Resolved At
                          </div>
                          <div className="font-semibold text-slate-800 text-sm">
                            {t.resolved_at
                              ? formatDate(
                                  t.resolved_at?.$date || t.resolved_at
                                )
                              : "-"}
                          </div>
                        </div>
                        <div className="bg-white/80 p-4 rounded-xl shadow-sm">
                          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide">
                            Urgency Level
                          </div>
                          <div className="font-semibold text-slate-800">
                            {t.urgency_level || "-"}
                          </div>
                        </div>
                        <div className="bg-white/80 p-4 rounded-xl shadow-sm">
                          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide">
                            Priority Score
                          </div>
                          <div className="font-semibold text-slate-800">
                            {t.priority_score || "-"}
                          </div>
                        </div>
                        <div className="bg-white/80 p-4 rounded-xl shadow-sm">
                          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide">
                            Incident DateTime
                          </div>
                          <div className="font-semibold text-slate-800 text-sm">
                            {t.incident_datetime
                              ? formatDate(t.incident_datetime)
                              : "-"}
                          </div>
                        </div>
                        <div className="bg-white/80 p-4 rounded-xl shadow-sm">
                          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide">
                            Action Taken
                          </div>
                          <div className="font-semibold text-slate-800">
                            {t.action_taken || "-"}
                          </div>
                        </div>
                        <div className="bg-white/80 p-4 rounded-xl shadow-sm">
                          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide">
                            Closing Remark
                          </div>
                          <div className="font-semibold text-slate-800">
                            {t.closing_remark || "-"}
                          </div>
                        </div>
                        <div className="bg-white/80 p-4 rounded-xl shadow-sm">
                          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide">
                            Assigned Department
                          </div>
                          <div className="font-semibold text-slate-800">
                            {t.assigned_department || "-"}
                          </div>
                        </div>
                      </div>

                      <div className="bg-white/80 p-4 rounded-xl shadow-sm mb-4">
                        <div className="text-xs text-slate-500 mb-2 uppercase tracking-wide font-semibold">
                          Description
                        </div>
                        <div className="text-sm text-slate-800 leading-relaxed prose max-w-none">
                          <ReactMarkdown>
                            {t.full_description ||
                              t.original_text ||
                              "No description available"}
                          </ReactMarkdown>
                        </div>
                        {t.document_insights && (
                          <div className="mt-4">
                            <div className="text-xs text-slate-500 mb-2 uppercase tracking-wide font-semibold">
                              Document Insights
                            </div>
                            <div className="text-sm text-slate-800 leading-relaxed prose max-w-none">
                              <ReactMarkdown>
                                {t.document_insights}
                              </ReactMarkdown>
                            </div>
                          </div>
                        )}
                        {t.message && (
                          <div className="mt-4">
                            <div className="text-xs text-slate-500 mb-2 uppercase tracking-wide font-semibold">
                              Message
                            </div>
                            <div className="text-sm text-slate-800 leading-relaxed prose max-w-none">
                              <ReactMarkdown>{t.message}</ReactMarkdown>
                            </div>
                          </div>
                        )}
                      </div>

                      {t.resolution_photos &&
                        t.resolution_photos.length > 0 && (
                          <div className="bg-white/80 p-4 rounded-xl shadow-sm mb-4">
                            <div className="text-xs text-slate-500 mb-3 uppercase tracking-wide font-semibold">
                              Resolution Photos
                            </div>
                            <div className="flex gap-3 flex-wrap">
                              {t.resolution_photos.map((photo, i) => (
                                <img
                                  key={i}
                                  src={buildImageUrl(photo)}
                                  alt={`resolution-${i}`}
                                  className="w-32 h-24 object-cover rounded-lg shadow-md hover:scale-105 transition-transform duration-200"
                                />
                              ))}
                            </div>
                          </div>
                        )}

                      <div className="flex gap-3 mt-4">
                        {/** Only allow rating when pending (once pending loaded). If not pending show disabled "Rated" */}
                        {(!pendingLoaded || pendingForms.has(itemId)) &&
                        !t._rated_by_user ? (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              openRatingModal(t);
                            }}
                            className="flex-1 px-4 py-2.5 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200"
                          >
                            ⭐ Rate Experience
                          </button>
                        ) : (
                          <button
                            disabled
                            className="flex-1 px-4 py-2.5 bg-white border-2 border-slate-200 text-slate-400 rounded-xl font-semibold cursor-not-allowed"
                          >
                            ⭐ Rated
                          </button>
                        )}
                        <button className="flex-1 px-4 py-2.5 bg-white border-2 border-slate-200 text-slate-700 rounded-xl font-semibold hover:bg-slate-50 hover:border-slate-300 transition-all duration-200">
                          📥 Download Report
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Rating Modal */}
      {showRatingModal && ratingTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-2xl bg-white rounded-2xl shadow-xl p-6 overflow-auto">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-bold">Rate Experience</h3>
                <div className="text-sm text-slate-500">
                  {ratingTarget.title ||
                    ratingTarget.subject ||
                    resolveId(ratingTarget)}
                </div>
              </div>
              <button onClick={closeRatingModal} className="text-slate-500">
                ✕
              </button>
            </div>

            <div className="space-y-4">
              {/* simple star selector for three metrics */}
              {["overall", "speed", "quality"].map((k) => (
                <div key={k}>
                  <div className="text-xs text-slate-500 uppercase tracking-wide font-semibold mb-1">
                    {k === "overall"
                      ? "Overall"
                      : k.charAt(0).toUpperCase() + k.slice(1)}
                  </div>
                  <div className="flex items-center gap-2">
                    {[1, 2, 3, 4, 5].map((n) => (
                      <button
                        key={n}
                        onClick={() => setRatings((r) => ({ ...r, [k]: n }))}
                        className={`text-2xl ${
                          ratings[k] >= n ? "text-yellow-500" : "text-slate-300"
                        }`}
                        aria-label={`${k} ${n} stars`}
                      >
                        ★
                      </button>
                    ))}
                    <div className="text-sm text-slate-500 ml-2">
                      {ratings[k]} / 5
                    </div>
                  </div>
                </div>
              ))}

              <div>
                <div className="text-xs text-slate-500 uppercase tracking-wide font-semibold mb-1">
                  Comment
                </div>
                <textarea
                  value={feedbackComment}
                  onChange={(e) => setFeedbackComment(e.target.value)}
                  className="w-full border rounded-lg p-3"
                  rows={3}
                  placeholder="Optional comment about your experience"
                />
              </div>

              <div>
                <div className="text-xs text-slate-500 uppercase tracking-wide font-semibold mb-1">
                  Evidence (optional)
                </div>
                <div className="flex items-center gap-3">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleEvidenceChange}
                    className="hidden"
                  />
                  <button
                    onClick={() =>
                      fileInputRef.current && fileInputRef.current.click()
                    }
                    className="px-4 py-2 rounded-lg bg-slate-100"
                  >
                    Upload Image
                  </button>
                  {evidencePreview && (
                    <img
                      src={evidencePreview}
                      alt="preview"
                      className="w-24 h-16 object-cover rounded-md border"
                    />
                  )}
                </div>
              </div>

              {submitError && (
                <div className="text-sm text-red-600">{submitError}</div>
              )}
              {submitSuccess && (
                <div className="text-sm text-green-600">{submitSuccess}</div>
              )}

              <div className="flex gap-2 justify-end mt-2">
                <button
                  onClick={closeRatingModal}
                  className="px-4 py-2 rounded-lg border"
                >
                  Cancel
                </button>
                <button
                  onClick={submitRating}
                  disabled={submitting}
                  className="px-4 py-2 rounded-lg bg-green-600 text-white font-semibold disabled:opacity-50"
                >
                  {submitting ? "Submitting..." : "Submit Feedback"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
