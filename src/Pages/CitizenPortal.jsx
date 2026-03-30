import React, { useState, useRef } from "react";
import {
  Mic,
  Camera,
  Send,
  CheckCircle,
  Clock,
  MessageCircle,
  Star,
  History,
} from "lucide-react";
import { grievanceAPI } from "../services/api";
import Navbar from "../components/Navbar";

export default function CitizenPortal() {
  const [view, setView] = useState("dashboard"); // 'dashboard' or 'new-complaint'
  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef(null);
  const [step, setStep] = useState(1); // 1: Input, 2: AI Verify, 3: Success
  const [sessionId, setSessionId] = useState(null);
  const [_extractedData, setExtractedData] = useState({});
  const [missingInfo, setMissingInfo] = useState([]);
  const [_clarificationQuestions, setClarificationQuestions] = useState([]);
  const [_isComplete, setIsComplete] = useState(false);
  const [serverMessage, setServerMessage] = useState("");
  const [textInput, setTextInput] = useState("");
  const [submittedFormResult, setSubmittedFormResult] = useState(null);
  const [formFields, setFormFields] = useState({
    category: "",
    location: "",
    description: "",
  });
  const [clarifyAnswers, setClarifyAnswers] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [rawError, setRawError] = useState(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [ticketProgress, setTicketProgress] = useState(null);
  const [ticketStatus, setTicketStatus] = useState("");
  const [ticketStatusMessage, setTicketStatusMessage] = useState("");

  // Safe serializer for errors (handles circular refs and File objects)
  function safeSerialize(obj) {
    try {
      const seen = new Set();
      return JSON.stringify(
        obj,
        function (key, value) {
          // represent File objects in a small form
          try {
            if (typeof File !== "undefined" && value instanceof File) {
              return {
                __file__: true,
                name: value.name,
                size: value.size,
                type: value.type,
              };
            }
          } catch {
            // ignore instanceof errors in some environments
          }
          if (typeof value === "object" && value !== null) {
            if (seen.has(value)) return "[Circular]";
            seen.add(value);
          }
          return value;
        },
        2
      );
    } catch {
      try {
        return String(obj);
      } catch {
        return "[unserializable]";
      }
    }
  }

  // Helper: start a grievance session with captured text (or from file upload)
  async function startSessionWithText(spoken) {
    setIsLoading(true);
    setServerMessage("Starting grievance session...");
    try {
      const fd = new FormData();
      fd.append("text", spoken || "");
      // include selected file if present
      if (selectedFile) {
        fd.append("files", selectedFile);
        fd.append("files[]", selectedFile);
      }
      const res = await grievanceAPI.start(fd);
      const data = res.data || {};
      setSessionId(data.session_id || data.sessionId || null);
      const extracted = data.extracted_data || {};
      setExtractedData(extracted);
      setFormFields({
        category: extracted.category || "",
        location: extracted.location || "",
        description: extracted.description || spoken || "",
      });
      setMissingInfo(data.missing_info || []);
      setClarificationQuestions(data.clarification_questions || []);
      setIsComplete(Boolean(data.is_complete));
      setServerMessage(data.message || "Session started");
      setStep(2);
    } catch (err) {
      console.error("startSession error", err);
      console.debug("startSession response data:", err?.response?.data);
      const msg =
        err?.response?.data?.message ||
        err?.response?.data ||
        err?.message ||
        "Failed to start session";
      setServerMessage(String(msg));
      // create a short, safe summary for UI and log full object to console
      try {
        const respData = err?.response?.data;
        let summary = err?.message || "Error";
        if (respData) {
          if (typeof respData === "string") summary = respData;
          else if (respData.message) summary = respData.message;
          else if (respData.detail)
            summary = Array.isArray(respData.detail)
              ? JSON.stringify(respData.detail)
              : String(respData.detail);
          else summary = "[server error — see console]";
        }
        setRawError(summary);
        console.debug(
          "full startSession error object:",
          err?.response?.data || err
        );
      } catch {
        setRawError(String(err));
      }
    } finally {
      setIsRecording(false);
      setIsLoading(false);
    }
  }

  // Mock History Data (Diagram Requirement: "Previous Grievances")
  // Recent activity - load dynamically from backend (/grievance/forms)
  const [recent, setRecent] = useState([]);
  const [recentLoading, setRecentLoading] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailData, setDetailData] = useState(null);

  React.useEffect(() => {
    let mounted = true;
    const loadRecent = async () => {
      setRecentLoading(true);
      try {
        const res = await grievanceAPI.getForms();
        const data = res?.data ?? res;
        let list = [];
        if (Array.isArray(data)) list = data;
        else if (data && Array.isArray(data.items)) list = data.items;
        else if (data && Array.isArray(data.results)) list = data.results;
        // normalize and pick most recent 5
        const mapped = (list || []).map((it) => ({
          id: it.form_id || it.id || it._id?.$oid || it._id,
          title:
            it.title ||
            it.full_description?.slice(0, 80) ||
            it.original_text?.slice(0, 80) ||
            "Grievance",
          status:
            it.status ||
            it.ticket_status ||
            (it.resolved_at ? "Resolved" : "Open"),
          date:
            it.submitted_at?.$date ||
            it.submitted_at ||
            it.created_at?.$date ||
            it.created_at ||
            null,
          photo:
            (it.resolution_photos && it.resolution_photos[0]) ||
            (it.document_paths && it.document_paths[0]) ||
            null,
        }));
        if (mounted) setRecent(mapped.slice(0, 5));
      } catch (e) {
        console.debug("Failed to load recent grievances", e);
      } finally {
        if (mounted) setRecentLoading(false);
      }
    };
    loadRecent();
    return () => {
      mounted = false;
    };
  }, []);

  const formatDate = (v) => {
    if (!v) return "-";
    try {
      const raw = typeof v === "string" ? v : v?.$date || v;
      const d = new Date(raw);
      return isNaN(d) ? String(v) : d.toLocaleString();
    } catch {
      return String(v);
    }
  };
  const buildImageUrl = (p) => {
    if (!p) return null;
    if (typeof p !== "string") return null;
    if (p.startsWith("http")) return p;
    const cleaned = p.replace(/^\.\/?/, "").replace(/\\/g, "/");
    return `${grievanceAPI.getForms ? window.location.origin : ""}/${cleaned}`;
  };

  const openDetailModal = async (id) => {
    if (!id) return;
    setDetailLoading(true);
    setDetailModalOpen(true);
    try {
      const res = await grievanceAPI.getForm(id);
      const data = res?.data || res;
      setDetailData(data);
    } catch (err) {
      console.error("Failed to load detail", err);
      setDetailData({ error: "Failed to load details" });
    } finally {
      setDetailLoading(false);
    }
  };

  const handleConfirm = async (id) => {
    if (!id) return;
    try {
      setDetailLoading(true);
      await grievanceAPI.confirmResolution(id);
      // try to refresh recent list and detail
      const refreshed = await (await grievanceAPI.getForm(id)).data;
      setDetailData(refreshed || {});
      // refresh recent list
      setRecent((r) =>
        r.map((i) =>
          i.id === id ? { ...i, status: refreshed.status || "Resolved" } : i
        )
      );
      alert("Confirmed. Thank you.");
      setDetailLoading(false);
    } catch (e) {
      console.error("Confirm error", e);
      alert(
        "Failed to confirm: " +
          (e?.response?.data?.message || e.message || "Unknown")
      );
      setDetailLoading(false);
    }
  };

  const sampleTicketProgress = {
    id: "GR-2024-99",
    steps: ["Received", "Triaged", "Assigned", "In-Field Action", "Resolved"],
    current: 2,
    slaHours: 48,
  };

  // file input ref + handlers
  const fileInputRef = useRef(null);
  const onFileChange = async (file) => {
    if (!file) return;
    setSelectedFile(file);
    setIsLoading(true);
    setServerMessage("Uploading photo and extracting info...");
    try {
      const fd = new FormData();
      fd.append("text", textInput || "");
      fd.append("files", file);
      fd.append("files[]", file);
      const res = await grievanceAPI.start(fd);
      const data = res.data || {};
      setSessionId(data.session_id || null);
      const extracted = data.extracted_data || {};
      setExtractedData(extracted);
      setFormFields({
        category: extracted.category || formFields.category,
        location: extracted.location || formFields.location,
        description: extracted.description || formFields.description,
      });
      setMissingInfo(data.missing_info || []);
      setClarificationQuestions(data.clarification_questions || []);
      setIsComplete(Boolean(data.is_complete));
      setServerMessage(data.message || "Photo processed");
      setStep(2);
    } catch (err) {
      console.error("photo upload error", err);
      const msg =
        err?.response?.data?.message || err?.message || "Photo upload failed";
      setServerMessage(String(msg));
      try {
        const respData = err?.response?.data;
        let summary = err?.message || "Error";
        if (respData) {
          if (typeof respData === "string") summary = respData;
          else if (respData.message) summary = respData.message;
          else if (respData.detail)
            summary = Array.isArray(respData.detail)
              ? JSON.stringify(respData.detail)
              : String(respData.detail);
          else summary = "[server error — see console]";
        }
        setRawError(summary);
      } catch {
        setRawError(String(err));
      }
    } finally {
      setIsLoading(false);
    }
  };
  const removeSelectedFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // New helper to submit typed text
  const handleSubmitText = async () => {
    if (!textInput || !String(textInput).trim()) {
      setServerMessage("Please enter a grievance or use the mic.");
      return;
    }
    setServerMessage("Starting grievance session...");
    await startSessionWithText(String(textInput).trim());
  };

  // keyboard shortcut for quick send (Ctrl/Cmd+Enter)
  const handleTextareaKeyDown = (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSubmitText();
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      <Navbar />
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-white p-4 shadow-sm rounded-md flex justify-between items-center sticky top-24 z-10">
          <h1 className="text-lg font-bold text-slate-800">Citizen Portal</h1>
          <div className="flex items-center gap-3">
            <a
              href="/citizen/profile"
              className="w-9 h-9 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 font-bold"
            >
              JD
            </a>
          </div>
        </div>
        <div className="mt-4">
          <div className="bg-white p-6 rounded-xl border border-slate-100">
            <h2 className="text-lg font-bold mb-2">Welcome to your portal</h2>
            <p className="text-sm text-slate-600">
              Use the links below to view profile, current or previous
              grievances, and track status.
            </p>
            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
              <a
                href="/citizen/profile"
                className="p-3 bg-slate-50 rounded-md text-sm font-medium text-slate-700 border border-slate-100"
              >
                Profile
              </a>
              <a
                href="/citizen/current"
                className="p-3 bg-slate-50 rounded-md text-sm font-medium text-slate-700 border border-slate-100"
              >
                Current Grievances
              </a>
              <a
                href="/citizen/previous"
                className="p-3 bg-slate-50 rounded-md text-sm font-medium text-slate-700 border border-slate-100"
              >
                Previous Grievances
              </a>
              <a
                href="/citizen/status"
                className="p-3 bg-slate-50 rounded-md text-sm font-medium text-slate-700 border border-slate-100"
              >
                Status Tracker
              </a>
            </div>
          </div>
        </div>

        {/* VIEW 1: DASHBOARD (History & Status) */}
        {view === "dashboard" && (
          <div className="p-4 space-y-6">
            {/* WhatsApp Bot Promo (Diagram Requirement) */}
            <div className="bg-green-50 border border-green-200 p-4 rounded-xl flex items-center gap-3">
              <div className="bg-green-500 text-white p-2 rounded-full">
                <MessageCircle size={20} />
              </div>
              <div>
                <div className="font-bold text-green-900 text-sm">
                  Use WhatsApp Bot
                </div>
                <div className="text-green-700 text-xs">
                  Send photo to +91-999-888-777
                </div>
              </div>
            </div>

            {/* Current Status Cards */}
            <h2 className="text-sm font-bold text-slate-500 uppercase">
              Recent Activity
            </h2>
            <div className="space-y-3">
              {recentLoading && (
                <div className="text-sm text-slate-500">
                  Loading recent activity…
                </div>
              )}
              {!recentLoading && recent.length === 0 && (
                <div className="text-sm text-slate-500">
                  No recent activity.
                </div>
              )}
              {recent.map((item) => (
                <div
                  key={item.id}
                  className="bg-white p-4 rounded-xl shadow-sm border border-slate-100"
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-bold text-slate-800">{item.title}</h3>
                    <span
                      className={`text-xs px-2 py-1 rounded font-bold ${
                        item.status &&
                        item.status.toLowerCase().includes("resolv")
                          ? "bg-green-100 text-green-700"
                          : "bg-yellow-100 text-yellow-700"
                      }`}
                    >
                      {item.status}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-xs text-slate-400">
                    <span>
                      {item.date ? new Date(item.date).toLocaleString() : ""}
                    </span>
                    <div className="flex gap-2">
                      <button
                        onClick={() => openDetailModal(item.id)}
                        className="text-sm text-blue-600 font-bold"
                      >
                        View & Confirm
                      </button>
                      {item.status &&
                      item.status.toLowerCase().includes("resolv") ? (
                        <button className="text-blue-600 font-bold flex items-center gap-1">
                          <Star size={12} /> Give Feedback
                        </button>
                      ) : null}
                    </div>
                  </div>
                  {item.photo && (
                    <div className="mt-3 border-t pt-3 flex items-center gap-3">
                      <img
                        src={
                          item.photo &&
                          (item.photo.startsWith("http")
                            ? item.photo
                            : buildImageUrl(item.photo))
                        }
                        alt="thumb"
                        className="w-20 h-14 object-cover rounded"
                      />
                      <div className="flex-1 text-xs text-slate-600">
                        Click to view updates in Current / Previous sections.
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Detail Modal */}
            {detailModalOpen && (
              <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
                <div className="bg-white max-w-2xl w-full rounded-xl shadow-lg p-6 overflow-auto max-h-[80vh]">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="font-bold text-lg">Grievance Details</h3>
                    <button
                      onClick={() => {
                        setDetailModalOpen(false);
                        setDetailData(null);
                      }}
                      className="text-slate-500"
                    >
                      Close
                    </button>
                  </div>
                  {detailLoading && <div>Loading…</div>}
                  {!detailLoading && detailData && (
                    <div className="space-y-3 text-sm">
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <strong>Form ID:</strong>{" "}
                          {detailData.form_id ||
                            detailData.formId ||
                            detailData._id?.$oid}
                        </div>
                        <div>
                          <strong>Status:</strong>{" "}
                          {detailData.status || detailData.ticket_status || "-"}
                        </div>
                        <div>
                          <strong>Category:</strong>{" "}
                          {detailData.category || "-"}
                        </div>
                        <div>
                          <strong>Priority:</strong>{" "}
                          {detailData.priority || "-"}
                        </div>
                        <div>
                          <strong>Assigned:</strong>{" "}
                          {detailData.assigned_officer_name || "-"}
                        </div>
                        <div>
                          <strong>Resolved At:</strong>{" "}
                          {formatDate(
                            detailData.resolved_at?.$date ||
                              detailData.resolved_at
                          )}
                        </div>
                      </div>
                      <div>
                        <strong>Description:</strong>
                        <div className="mt-1 text-slate-800 whitespace-pre-line">
                          {detailData.full_description ||
                            detailData.original_text ||
                            "-"}
                        </div>
                      </div>
                      {detailData.resolution_photos &&
                        detailData.resolution_photos.length > 0 && (
                          <div className="flex gap-2 flex-wrap mt-2">
                            {detailData.resolution_photos.map((p, i) => (
                              <img
                                key={i}
                                src={buildImageUrl(p)}
                                alt={`res-${i}`}
                                className="w-32 h-24 object-cover rounded"
                              />
                            ))}
                          </div>
                        )}
                      <div className="flex gap-3 justify-end">
                        <button
                          onClick={() => setDetailModalOpen(false)}
                          className="px-4 py-2 border rounded"
                        >
                          Close
                        </button>
                        <button
                          onClick={() =>
                            handleConfirm(
                              detailData.form_id ||
                                detailData.formId ||
                                detailData._id?.$oid
                            )
                          }
                          disabled={detailLoading}
                          className="px-4 py-2 bg-green-600 text-white rounded"
                        >
                          {detailLoading ? "Confirming…" : "Confirm Resolution"}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Floating Action Button for New Complaint */}
            <button
              onClick={() => setView("new-complaint")}
              className="fixed bottom-8 right-8 bg-orange-600 text-white p-4 rounded-full shadow-lg hover:scale-105 transition-transform"
              aria-label="New complaint"
            >
              <Mic size={24} />
            </button>
          </div>
        )}

        {/* VIEW 2: NEW COMPLAINT FLOW (NLP -> Form -> Verify) */}
        {view === "new-complaint" && (
          <div className="p-6 flex flex-col">
            {" "}
            {/* removed h-screen to avoid huge centering */}
            <button
              onClick={() => setView("dashboard")}
              className="text-slate-400 mb-4 text-sm font-bold"
            >
              ← Back
            </button>
            {/* Step 1: Speak */}
            {step === 1 && (
              <div className="w-full max-w-md mx-auto mt-2">
                <h2 className="text-xl font-semibold text-slate-800 mb-3">
                  What is the issue?
                </h2>

                <div className="bg-white border border-slate-100 rounded-lg p-3 shadow-sm">
                  <textarea
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    onKeyDown={handleTextareaKeyDown}
                    placeholder="Type your grievance here (Ctrl/Cmd + Enter to send)"
                    className="w-full p-2 border rounded h-28 text-sm resize-none"
                  />

                  <hr className="my-3 border-slate-100" />

                  <div className="flex items-center gap-3">
                    {/* Left: mic + clear */}
                    <div className="flex items-center gap-2">
                      <button
                        onClick={async () => {
                          // existing mic start logic compacted
                          const SpeechRecognition =
                            window.SpeechRecognition ||
                            window.webkitSpeechRecognition;
                          if (!SpeechRecognition) {
                            // Don't auto-submit when mic isn't available — just inform user.
                            setServerMessage(
                              "Speech recognition not supported. Type your grievance or use the Send button."
                            );
                            return;
                          }
                          if (recognitionRef.current) {
                            recognitionRef.current.stop();
                            recognitionRef.current = null;
                            setIsRecording(false);
                            return;
                          }
                          setIsRecording(true);
                          try {
                            const recog = new SpeechRecognition();
                            recog.lang = "en-US";
                            recog.interimResults = false;
                            recog.maxAlternatives = 1;
                            recog.onresult = (event) => {
                              // Only populate the textarea — do not auto-submit.
                              const transcript =
                                event.results?.[0]?.[0]?.transcript || "";
                              setTextInput(transcript);
                              setServerMessage(
                                "Recording captured. Review the text and click Send to submit."
                              );
                            };
                            recog.onerror = (ev) => {
                              console.error("Speech error", ev);
                              setServerMessage("Speech recognition error");
                              setIsRecording(false);
                              recognitionRef.current = null;
                            };
                            recog.onend = () => {
                              setIsRecording(false);
                              recognitionRef.current = null;
                            };
                            recognitionRef.current = recog;
                            recog.start();
                          } catch (err) {
                            console.error(err);
                            setServerMessage(
                              err?.message || "Failed to start mic"
                            );
                            setIsRecording(false);
                            recognitionRef.current = null;
                          }
                        }}
                        className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          isRecording
                            ? "bg-red-100 ring-1 ring-red-200"
                            : "bg-orange-100"
                        }`}
                        aria-label="Record"
                      >
                        <Mic
                          size={16}
                          className={
                            isRecording ? "text-red-500" : "text-blue-600"
                          }
                        />
                      </button>

                      <button
                        onClick={() => {
                          setTextInput("");
                          setServerMessage("");
                          setRawError(null);
                        }}
                        className="px-2 py-1 bg-slate-100 rounded text-sm"
                      >
                        Clear
                      </button>
                    </div>

                    {/* Center: file name + attach */}
                    <div className="flex-1 flex items-center gap-2 text-sm text-slate-600">
                      {selectedFile ? (
                        <div className="flex items-center gap-2">
                          <span className="truncate max-w-[200px]">
                            {selectedFile.name}
                          </span>
                          <button
                            onClick={removeSelectedFile}
                            className="text-xs text-slate-500 px-1"
                          >
                            Remove
                          </button>
                        </div>
                      ) : (
                        <div className="text-xs">No attachment</div>
                      )}
                      <label className="ml-2 inline-flex items-center gap-2 text-xs text-blue-600 cursor-pointer">
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept="image/*"
                          className="hidden"
                          onChange={(e) => onFileChange(e.target.files?.[0])}
                        />
                        Attach
                      </label>
                    </div>

                    {/* Right: Send */}
                    <div>
                      <button
                        onClick={handleSubmitText}
                        disabled={isLoading}
                        className="px-4 py-2 bg-orange-600 text-white rounded-md font-bold text-sm"
                      >
                        Send
                      </button>
                    </div>
                  </div>
                  {/* helper row */}
                  <div className="mt-2 text-xs text-slate-400 flex justify-between">
                    <div>Tip: Press Ctrl/Cmd + Enter to send</div>
                    <div className="text-xs text-slate-500">
                      {serverMessage}
                    </div>
                  </div>
                </div>
              </div>
            )}
            {/* Step 2: AI Verify (Diagram: "NLP -> Form -> Edit") */}
            {step === 2 && (
              <div className="animate-in slide-in-from-bottom-10">
                {isLoading && (
                  <div className="mb-2 p-2 bg-blue-50 border border-blue-100 rounded text-sm text-blue-700">
                    Processing... {serverMessage}
                  </div>
                )}
                <div className="bg-green-50 p-2 rounded-lg flex items-center gap-2 text-green-800 font-bold mb-4">
                  <CheckCircle size={16} /> AI Analyzed your voice
                </div>
                <form className="space-y-3">
                  <div className="text-xs text-slate-500">
                    Session: <strong>{sessionId || "—"}</strong>
                  </div>
                  {serverMessage && (
                    <div className="text-sm text-slate-600">
                      {serverMessage}
                    </div>
                  )}
                  <div>
                    <label className="text-xs font-bold text-slate-400 uppercase">
                      CATEGORY
                    </label>
                    <input
                      type="text"
                      value={formFields.category}
                      onChange={(e) =>
                        setFormFields({
                          ...formFields,
                          category: e.target.value,
                        })
                      }
                      className="w-full p-2 border rounded-lg font-bold text-slate-800 bg-white text-sm"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-bold text-slate-400 uppercase">
                      LOCATION
                    </label>
                    <input
                      type="text"
                      value={formFields.location}
                      onChange={(e) =>
                        setFormFields({
                          ...formFields,
                          location: e.target.value,
                        })
                      }
                      className="w-full p-2 border rounded-lg text-slate-800 bg-white text-sm"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-bold text-slate-400 uppercase">
                      DESCRIPTION
                    </label>
                    <textarea
                      value={formFields.description}
                      onChange={(e) =>
                        setFormFields({
                          ...formFields,
                          description: e.target.value,
                        })
                      }
                      className="w-full p-2 border rounded-lg text-slate-800 bg-white h-20 text-sm"
                    ></textarea>
                  </div>

                  {/* Missing info / Clarifications */}
                  {missingInfo && missingInfo.length > 0 && (
                    <div className="p-2 bg-yellow-50 border border-yellow-100 rounded-lg">
                      <div className="text-sm font-bold text-yellow-800 mb-1">
                        Missing information detected
                      </div>
                      <ul className="text-xs text-slate-600 space-y-1 mb-2">
                        {missingInfo.map((m) => (
                          <li key={m}>• {m}</li>
                        ))}
                      </ul>
                      {missingInfo.map((m) => (
                        <input
                          key={m}
                          placeholder={`Add ${m}`}
                          value={clarifyAnswers[m] || ""}
                          onChange={(e) =>
                            setClarifyAnswers({
                              ...clarifyAnswers,
                              [m]: e.target.value,
                            })
                          }
                          className="w-full mb-1 p-2 border rounded text-sm"
                        />
                      ))}
                      <div className="flex gap-2 mt-2">
                        <button
                          type="button"
                          onClick={async () => {
                            try {
                              setIsLoading(true);
                              setServerMessage("Sending clarification...");
                              // Normalize answer keys and formats to match backend expectations
                              const normalizeAnswers = (answers) => {
                                const out = {};
                                for (const keyRaw of Object.keys(
                                  answers || {}
                                )) {
                                  const val = answers[keyRaw];
                                  const key = String(keyRaw).toLowerCase();
                                  if (key.includes("landmark")) {
                                    out["landmark"] = val;
                                  } else if (
                                    key.includes("area_ward") ||
                                    key.includes("ward") ||
                                    key.includes("area")
                                  ) {
                                    out["area_ward_name"] = val;
                                  } else if (
                                    key.includes("incident") ||
                                    key.includes("datetime")
                                  ) {
                                    // convert date-only YYYY-MM-DD to ISO datetime with a safe default time
                                    if (
                                      /^\d{4}-\d{2}-\d{2}$/.test(
                                        String(val).trim()
                                      )
                                    ) {
                                      out["incident_datetime"] =
                                        String(val).trim() + "T09:00:00+05:30";
                                    } else {
                                      out["incident_datetime"] = val;
                                    }
                                  } else if (
                                    key.includes("specific") ||
                                    key.includes("location_hint") ||
                                    key.includes("location details") ||
                                    key.includes("location")
                                  ) {
                                    out["location_hint"] = val;
                                  } else {
                                    out[keyRaw] = val;
                                  }
                                }
                                return out;
                              };

                              const normalized =
                                normalizeAnswers(clarifyAnswers);
                              const payload = {
                                session_id: sessionId,
                                answers: normalized,
                              };
                              console.debug("clarify payload:", payload);
                              const resp = await grievanceAPI.clarify(payload);
                              const d = resp.data || {};
                              const extracted = d.extracted_data || {};
                              setExtractedData(extracted);
                              setFormFields({
                                category:
                                  extracted.category || formFields.category,
                                location:
                                  extracted.location || formFields.location,
                                description:
                                  extracted.description ||
                                  formFields.description,
                              });
                              setMissingInfo(d.missing_info || []);
                              setClarificationQuestions(
                                d.clarification_questions || []
                              );
                              setIsComplete(Boolean(d.is_complete));
                              setServerMessage(
                                d.message || "Clarification submitted"
                              );
                              setRawError(null);
                            } catch (err) {
                              console.error("clarify error", err);
                              console.debug(
                                "clarify response data:",
                                err?.response?.data
                              );
                              const respData = err?.response?.data;
                              let summary =
                                err?.message || "Failed to send clarification";
                              if (respData) {
                                if (typeof respData === "string")
                                  summary = respData;
                                else if (respData.message)
                                  summary = respData.message;
                                else if (respData.detail)
                                  summary = Array.isArray(respData.detail)
                                    ? JSON.stringify(respData.detail)
                                    : String(respData.detail);
                                else summary = "[server error — see console]";
                              }
                              setServerMessage(String(summary));
                              try {
                                setRawError(
                                  typeof respData === "object" &&
                                    respData !== null
                                    ? safeSerialize(respData)
                                    : String(respData)
                                );
                              } catch {
                                setRawError(
                                  String(respData || err?.message || "Error")
                                );
                              }
                            } finally {
                              setIsLoading(false);
                            }
                          }}
                          className="px-3 py-1 bg-blue-600 text-white rounded text-sm"
                        >
                          Send Clarification
                        </button>
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-2 items-center">
                    <div className="text-sm text-slate-500">
                      Estimated SLA:{" "}
                      <strong>{sampleTicketProgress.slaHours} hrs</strong>
                    </div>
                    <button
                      type="button"
                      onClick={async () => {
                        try {
                          const payload = {
                            session_id: sessionId,
                            confirmed: true,
                            edits: formFields,
                          };
                          const res = await grievanceAPI.submit(payload);
                          const d = res.data || {};
                          setSubmittedFormResult(d);
                          // persist last form id for later lookup
                          const fid =
                            d.form_id || d.formId || d.id || d.ticket_id;
                          if (fid) localStorage.setItem("last_form_id", fid);
                          if (sessionId)
                            localStorage.setItem("last_session_id", sessionId);

                          // Fetch live status from backend and update progress
                          if (fid) {
                            try {
                              const statusRes = await grievanceAPI.getStatus(
                                fid
                              );
                              const s = (statusRes && statusRes.data) || {};
                              setTicketProgress({
                                steps: sampleTicketProgress.steps,
                                current:
                                  typeof s.progress === "number"
                                    ? s.progress
                                    : 0,
                                slaHours: sampleTicketProgress.slaHours,
                              });
                              setTicketStatus(
                                s.status || d.status || "Submitted"
                              );
                              setTicketStatusMessage(s.message || "");
                              // also keep status in submittedFormResult for UI
                              setSubmittedFormResult((prev) => ({
                                ...(prev || {}),
                                status: s.status || prev?.status,
                              }));
                            } catch (e) {
                              console.debug(
                                "Failed to fetch status after submit",
                                e
                              );
                            }
                          }

                          setServerMessage(d.message || "Submitted");
                          setStep(3);
                        } catch (err) {
                          console.error("submit error", err);
                          const msg =
                            err?.response?.data?.message ||
                            err?.message ||
                            "Failed to submit form";
                          setServerMessage(String(msg));
                        }
                      }}
                      className="w-full bg-orange-600 text-white py-2 rounded-xl font-bold text-sm"
                    >
                      Confirm & Submit
                    </button>
                  </div>
                </form>
              </div>
            )}
            {/* Step 3: Success */}
            {step === 3 && (
              <div className="flex-1 flex flex-col items-center justify-center text-center">
                <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-6">
                  <CheckCircle size={40} className="text-green-600" />
                </div>
                <h2 className="text-2xl font-bold text-slate-800">
                  Complaint Registered!
                </h2>
                <p className="text-slate-500 mt-2">
                  Ticket ID:{" "}
                  {submittedFormResult?.form_id ||
                    ticketProgress?.id ||
                    sampleTicketProgress.id}
                </p>
                <p className="text-sm text-slate-500 mt-2">
                  Status:{" "}
                  <strong>
                    {submittedFormResult?.status || ticketStatus || "Submitted"}
                  </strong>
                </p>

                <div className="w-full max-w-md mt-6">
                  <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
                    {(ticketProgress?.steps || sampleTicketProgress.steps).map(
                      (s, i) => (
                        <div
                          key={s}
                          className={`flex-1 text-center ${
                            i <=
                            (ticketProgress?.current ??
                              sampleTicketProgress.current)
                              ? "text-slate-900 font-bold"
                              : ""
                          }`}
                        >
                          {s}
                        </div>
                      )
                    )}
                  </div>
                  <div className="relative h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className="absolute left-0 top-0 bottom-0 bg-orange-500 rounded-full"
                      style={{
                        width: `${
                          (((ticketProgress?.current ??
                            sampleTicketProgress.current) +
                            1) /
                            (ticketProgress?.steps?.length ||
                              sampleTicketProgress.steps.length)) *
                          100
                        }%`,
                      }}
                    />
                  </div>
                  {ticketStatusMessage && (
                    <div className="mt-2 text-xs text-slate-500">
                      {ticketStatusMessage}
                    </div>
                  )}
                </div>

                <button
                  onClick={() => setView("dashboard")}
                  className="mt-8 text-orange-600 font-bold"
                >
                  Go to Dashboard
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
