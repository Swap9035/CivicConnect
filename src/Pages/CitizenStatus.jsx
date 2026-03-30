import React, { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
import CitizenNav from "../components/CitizenNav";
import { grievanceAPI } from "../services/api";

export default function CitizenStatus() {
  const [grievances, setGrievances] = useState([]);
  const [expandedFormId, setExpandedFormId] = useState(null);
  const [statusData, setStatusData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchGrievances = async () => {
      try {
        console.log("Fetching grievances...");
        const response = await grievanceAPI.getForms();
        console.log("Grievances response:", response);
        setGrievances(response.data || []);
      } catch (err) {
        console.error("Error fetching grievances:", err);
        setError(`Failed to load grievances: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };
    fetchGrievances();
  }, []);

  const handleExpand = async (formId) => {
    if (expandedFormId === formId) {
      setExpandedFormId(null);
      setStatusData(null);
    } else {
      setExpandedFormId(formId);
      try {
        console.log(`Fetching status for ${formId}...`);
        const response = await grievanceAPI.getStatus(formId);
        console.log("Status response:", response);
        setStatusData(response.data);
      } catch (err) {
        console.error("Error fetching status:", err);
        setError(`Failed to load status: ${err.message}`);
      }
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;

  const steps = [
    {
      label: "Submitted",
      description: "Your grievance has been received and is being processed.",
    },
    {
      label: "Analyzed",
      description:
        "AI has analyzed your grievance for duplicates and priority.",
    },
    {
      label: "Assigned",
      description: "Assigned to an officer or linked to an existing case.",
    },
    {
      label: "In Progress",
      description: "Officer is working on resolving your grievance.",
    },
    {
      label: "Resolved",
      description:
        "Your grievance has been resolved. Check for feedback options.",
    },
  ];

  const currentProgress = statusData ? statusData.progress : 0;

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <div className="max-w-4xl mx-auto p-6">
        <CitizenNav />
        <h2 className="text-xl font-bold mb-4">Your Grievances</h2>
        {grievances.length === 0 ? (
          <div className="bg-white p-6 rounded-xl border border-slate-100">
            No grievances found.
          </div>
        ) : (
          grievances.map((grievance) => (
            <div
              key={grievance.form_id}
              className="bg-white p-6 rounded-xl border border-slate-100 mb-4"
            >
              <div className="flex justify-between items-center">
                <div>
                  <div className="text-sm text-slate-500">
                    Grievance ID: {grievance.form_id}
                  </div>
                  <div className="text-sm text-slate-600">
                    Status: {grievance.status}
                  </div>
                  <div className="text-sm text-slate-600">
                    Category: {grievance.category || "N/A"}
                  </div>
                </div>
                <button
                  onClick={() => handleExpand(grievance.form_id)}
                  className="px-4 py-2 bg-orange-500 text-white rounded"
                >
                  {expandedFormId === grievance.form_id
                    ? "Collapse"
                    : "View Status"}
                </button>
              </div>
              {expandedFormId === grievance.form_id && statusData && (
                <div className="mt-4">
                  <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
                    {steps.map((step, i) => (
                      <div
                        key={step.label}
                        className={`flex-1 text-center ${
                          i <= currentProgress ? "text-slate-900 font-bold" : ""
                        }`}
                      >
                        {step.label}
                      </div>
                    ))}
                  </div>
                  <div className="relative h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className="absolute left-0 top-0 bottom-0 bg-orange-500 rounded-full"
                      style={{
                        width: `${
                          ((currentProgress + 1) / steps.length) * 100
                        }%`,
                      }}
                    />
                  </div>
                  <div className="mt-4 text-sm text-slate-600">
                    Current Stage:{" "}
                    <strong>{steps[currentProgress]?.label}</strong> -{" "}
                    {steps[currentProgress]?.description}
                  </div>
                  {statusData?.message && (
                    <div className="mt-2 text-sm text-slate-500">
                      {statusData.message}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
