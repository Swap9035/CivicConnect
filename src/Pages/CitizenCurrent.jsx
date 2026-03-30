import React, { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import CitizenNav from "../components/CitizenNav";
import api, { grievanceAPI } from "../services/api";

export default function CitizenCurrent() {
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
  const [expandedId, setExpandedId] = React.useState(null);
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
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // --- New state: clarifications grouped by grievance, UI toggles and reply buffers
  const [clarificationsByGrievance, setClarificationsByGrievance] = useState(
    {}
  );
  const [showClarifications, setShowClarifications] = useState({});
  const [replyBuffer, setReplyBuffer] = useState({});
  const [replySubmitting, setReplySubmitting] = useState({});

  useEffect(() => {
    let mounted = true;
    const tryEndpoints = async () => {
      setLoading(true);
      setError(null);
      // try to detect current user so we can call user-scoped endpoints
      let userId = null;
      try {
        const me = await api.get("/users/me");
        if (me?.data && (me.data.id || me.data.user_id))
          userId = me.data.id || me.data.user_id;
      } catch {
        // ignore - unauthenticated or endpoint missing
      }
      // Prefer official grievance endpoints first to avoid 404s from missing user-scoped routes
      const endpoints = [
        "/grievance/forms",
        "/grievance/list",
        "/grievance/my/forms",
        "/grievance/user/forms",
        "/grievance",
      ];
      // Only try user-scoped endpoints after official ones (some backends don't implement these)
      if (userId) {
        endpoints.push(
          `/users/${userId}/grievances`,
          `/users/${userId}/forms`,
          `/users/${userId}/tickets`
        );
      }
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
            // show only assigned or linked grievances for "current", and exclude completed/closed
            const filtered = list.filter((i) => {
              const s = (i.status || i.ticket_status || "")
                .toString()
                .toLowerCase();
              const isCompleted =
                s.includes("resolv") ||
                s.includes("closed") ||
                s.includes("completed") ||
                s.includes("complete");
              const isAssignedOrLinked = Boolean(
                i.assigned_officer_id ||
                  i.parent_form_id ||
                  i.parent_ticket_id ||
                  i.linked_to
              );
              return isAssignedOrLinked && !isCompleted;
            });
            setItems(filtered.length > 0 ? filtered : []);
            setLoading(false);
            return;
          }
        } catch {
          // ignore and try next
        }
      }
      // fallback: try to fetch recent submitted form if available via grievanceAPI (no list endpoint)
      try {
        const resp = await grievanceAPI.getSession(
          localStorage.getItem("last_session_id")
        );
        if (resp?.data) {
          const d = resp.data;
          if (d?.form_id || d?.session_id) {
            const entry = {
              id: d.form_id || d.session_id,
              title:
                d.extracted_data?.title ||
                d.extracted_data?.full_description ||
                "Submitted grievance",
              status: d.is_complete ? "Submitted" : "Draft",
              eta: d.is_complete ? "—" : "Pending",
            };
            if (mounted) setItems([entry]);
          }
        }
      } catch {
        // final fallback: empty
      }
      if (mounted) setLoading(false);
    };
    tryEndpoints();
    return () => {
      mounted = false;
    };
  }, []);

  // Fetch user's clarifications once on mount and group by grievance_id
  useEffect(() => {
    let mounted = true;
    const loadClarifications = async () => {
      try {
        const res = await api.get("/clarifications");
        const list = res?.data?.clarifications || res?.data || [];
        const map = {};
        for (const c of list) {
          const gid = c.grievance_id || c.grievanceId || c.grievance || "";
          if (!map[gid]) map[gid] = [];
          map[gid].push(c);
        }
        if (mounted) setClarificationsByGrievance(map);
      } catch (err) {
        // silently ignore; clarifications are optional
        console.error("Failed to load clarifications", err);
      }
    };
    loadClarifications();
    return () => (mounted = false);
  }, []);

  const toggleClarifications = (gid) => {
    setShowClarifications((s) => ({ ...s, [gid]: !s[gid] }));
  };

  const submitClarificationResponse = async (clarId, gid) => {
    const text = (replyBuffer[clarId] || "").trim();
    if (!text) return;
    setReplySubmitting((s) => ({ ...s, [clarId]: true }));
    try {
      await api.post(`/clarifications/${clarId}/respond`, {
        citizen_response: text,
      });
      // Optimistically update local state: set citizen_response and responded_at
      setClarificationsByGrievance((prev) => {
        const arr = (prev[gid] || []).map((c) =>
          (c.id || c._id || "").toString() === clarId.toString()
            ? {
                ...c,
                citizen_response: text,
                responded_at: new Date().toISOString(),
              }
            : c
        );
        return { ...prev, [gid]: arr };
      });
      setReplyBuffer((b) => ({ ...b, [clarId]: "" }));
    } catch (err) {
      console.error("Failed to submit clarification response", err);
      // optionally show an error toast - omitted for brevity
    } finally {
      setReplySubmitting((s) => ({ ...s, [clarId]: false }));
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
      <Navbar />
      <div className="max-w-6xl mx-auto px-4 py-8">
        <CitizenNav />

        {/* Header */}
        <div className="mb-8 animate-fade-in-up">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-3xl font-bold bg-gradient-to-r from-orange-600 to-orange-800 bg-clip-text text-transparent">
                Current Grievances
              </h2>
              <p className="text-slate-600 mt-1">
                Track your ongoing complaints and their progress
              </p>
            </div>
            <div className="px-4 py-2 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-xl font-bold shadow-lg">
              {items.length} Active
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-6 rounded-2xl mb-6 shadow-xl animate-pulse">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 border-4 border-white/30 border-t-white rounded-full animate-spin"></div>
              <span className="font-medium">Loading current grievances...</span>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-gradient-to-r from-red-500 to-red-600 text-white p-6 rounded-2xl mb-6 shadow-xl">
            <div className="flex items-center gap-3">
              <span className="text-2xl">⚠️</span>
              <span className="font-medium">{String(error)}</span>
            </div>
          </div>
        )}

        {/* Empty State */}
        {items.length === 0 && !loading && (
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-slate-200 shadow-xl p-12 text-center animate-fade-in-up">
            <div className="w-24 h-24 bg-gradient-to-br from-orange-100 to-blue-100 rounded-full mx-auto mb-6 flex items-center justify-center">
              <span className="text-5xl">📋</span>
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-2">
              No Current Grievances
            </h3>
            <p className="text-slate-600 mb-6">
              You don't have any ongoing complaints at the moment
            </p>
            <a
              href="/citizen"
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-orange-600 to-orange-700 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200"
            >
              Lodge New Complaint
            </a>
          </div>
        )}

        {/* Grievances List */}
        <div className="space-y-4">
          {items.map((t, idx) => {
            const itemId = resolveId(t);
            const isExpanded = itemId === expandedId;
            const status = t.status || t.ticket_status || "Unknown";
            const statusColor = status.toLowerCase().includes("progress")
              ? "from-blue-500 to-blue-600"
              : status.toLowerCase().includes("pending")
              ? "from-yellow-500 to-yellow-600"
              : status.toLowerCase().includes("assigned")
              ? "from-green-500 to-green-600"
              : "from-slate-500 to-slate-600";

            return (
              <div
                key={itemId || `curr-${idx}`}
                onClick={async () => {
                  try {
                    const id = resolveId(t);
                    if (!id) return;
                    const res = await grievanceAPI.getForm(id);
                    const updated = res?.data || res?.data?.result || res;
                    setItems((prev) =>
                      prev.map((p) =>
                        resolveId(p) === id
                          ? { ...p, ...updated, form_id: updated.form_id || id }
                          : p
                      )
                    );
                    setExpandedId(isExpanded ? null : id);
                  } catch (err) {
                    console.error("Failed to refresh grievance", err);
                  }
                }}
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
                        <span
                          className={`px-3 py-1 bg-gradient-to-r ${statusColor} text-white rounded-full text-xs font-bold shadow-md`}
                        >
                          {status}
                        </span>
                      </div>
                      <h3 className="text-lg font-bold text-slate-800 group-hover:text-orange-600 transition-colors mb-1">
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
                        <div className="text-xs text-slate-500 mb-1">ETA</div>
                        <div className="font-semibold text-slate-800">
                          {t.eta || t.estimated_resolution || "—"}
                        </div>
                      </div>
                      <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center group-hover:bg-orange-200 transition-colors">
                        <span
                          className={`text-orange-600 transform transition-transform duration-200 ${
                            isExpanded ? "rotate-180" : ""
                          }`}
                        >
                          ▼
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="mt-6 p-6 bg-gradient-to-br from-slate-50 to-blue-50 rounded-xl border border-slate-200 animate-fade-in-up">
                      <div className="grid md:grid-cols-3 gap-4 mb-4">
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
                          <div className="font-semibold text-slate-800">
                            {t.status || "-"}
                          </div>
                        </div>
                        <div className="bg-white/80 p-4 rounded-xl shadow-sm">
                          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide">
                            ETA
                          </div>
                          <div className="font-semibold text-slate-800">
                            {t.estimated_response_time || t.eta || "—"}
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
                      </div>

                      <div className="bg-white/80 p-4 rounded-xl shadow-sm mb-4">
                        <div className="text-xs text-slate-500 mb-2 uppercase tracking-wide font-semibold">
                          Description
                        </div>
                        <div className="text-sm text-slate-800 leading-relaxed">
                          {(
                            t.full_description ||
                            t.original_text ||
                            "No description available"
                          ).slice(0, 300)}
                          {(t.full_description || t.original_text || "")
                            .length > 300
                            ? "..."
                            : ""}
                        </div>
                      </div>

                      {/* Clarifications Section */}
                      <div className="bg-white/80 p-4 rounded-xl shadow-sm mb-4">
                        <div className="flex items-center justify-between mb-3">
                          <div className="text-xs text-slate-500 uppercase tracking-wide font-semibold">
                            Clarifications
                          </div>
                          <div>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleClarifications(itemId);
                              }}
                              className="px-3 py-1 bg-orange-600 text-white rounded-lg text-sm font-medium hover:brightness-105"
                            >
                              View Clarifications (
                              {(clarificationsByGrievance[itemId] || []).length}
                              )
                            </button>
                          </div>
                        </div>
                        {showClarifications[itemId] && (
                          <div className="space-y-3 mt-2">
                            {(clarificationsByGrievance[itemId] || [])
                              .length === 0 ? (
                              <div className="text-sm text-slate-500">
                                No clarifications
                              </div>
                            ) : (
                              clarificationsByGrievance[itemId].map((c) => {
                                const cid = c.id || c._id || "";
                                return (
                                  <div
                                    key={cid}
                                    className="border border-slate-100 p-3 rounded-lg"
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    <div className="text-sm text-slate-700 mb-1">
                                      <span className="font-semibold">
                                        From officer:
                                      </span>{" "}
                                      {c.officer_id || "—"}
                                    </div>
                                    <div className="text-xs text-slate-500 mb-2">
                                      Requested at:{" "}
                                      {formatDate(
                                        c.requested_at || c.requestedAt
                                      )}
                                    </div>
                                    <div className="text-sm text-slate-800 mb-2">
                                      {c.message}
                                    </div>
                                    {c.citizen_response ? (
                                      <div className="text-sm text-green-700">
                                        <div className="font-medium">
                                          You responded:
                                        </div>
                                        <div className="text-slate-800">
                                          {c.citizen_response}
                                        </div>
                                        <div className="text-xs text-slate-500 mt-1">
                                          Responded at:{" "}
                                          {formatDate(c.responded_at)}
                                        </div>
                                      </div>
                                    ) : (
                                      <div className="mt-2 flex gap-2">
                                        <textarea
                                          value={replyBuffer[cid] || ""}
                                          onChange={(e) =>
                                            setReplyBuffer((b) => ({
                                              ...b,
                                              [cid]: e.target.value,
                                            }))
                                          }
                                          placeholder="Type your response..."
                                          className="flex-1 p-2 border rounded-lg text-sm"
                                          rows={2}
                                        />
                                        <button
                                          onClick={() =>
                                            submitClarificationResponse(
                                              cid,
                                              itemId
                                            )
                                          }
                                          disabled={replySubmitting[cid]}
                                          className="px-4 py-2 bg-green-600 text-white rounded-lg font-semibold hover:brightness-105"
                                        >
                                          {replySubmitting[cid]
                                            ? "Sending..."
                                            : "Respond"}
                                        </button>
                                      </div>
                                    )}
                                  </div>
                                );
                              })
                            )}
                          </div>
                        )}
                      </div>

                      {t.resolution_photos &&
                        t.resolution_photos.length > 0 && (
                          <div className="bg-white/80 p-4 rounded-xl shadow-sm">
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
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
