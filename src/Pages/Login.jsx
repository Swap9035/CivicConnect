import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Shield, Smartphone, Mail, ArrowRight } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [role, setRole] = useState("citizen"); // citizen, officer, admin
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [formData, setFormData] = useState({
    mobile_number: "",
    password: "",
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setError("");
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    // Determine if user is staff (admin/officer) or citizen
    const isStaff = role === "admin" || role === "officer";

    // Use real API authentication for all roles
    const result = await login(
      formData.mobile_number,
      formData.password,
      isStaff
    );

    if (result.success) {
      // Navigate based on role selection
      if (role === "citizen") navigate("/citizen");
      else if (role === "officer") navigate("/officer");
      else if (role === "admin") navigate("/admin");
    } else {
      setError(result.error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 via-slate-900 to-slate-800 p-4 relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-10 animate-blob"></div>
        <div className="absolute top-40 right-10 w-72 h-72 bg-orange-500 rounded-full mix-blend-multiply filter blur-xl opacity-10 animate-blob animation-delay-2000"></div>
      </div>

      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden relative z-10 animate-fade-in-up">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-8 text-center relative overflow-hidden">
          <div className="absolute inset-0 bg-black opacity-5"></div>
          <div className="mx-auto bg-white w-16 h-16 rounded-full flex items-center justify-center mb-4 shadow-lg relative z-10 transform transition-transform hover:scale-110 duration-300">
            <Shield className="text-blue-600" size={28} />
          </div>
          <h1 className="text-3xl font-bold text-white relative z-10">
            CivicConnect AI
          </h1>
          <p className="text-blue-50 relative z-10">
            Grievance Redressal System
          </p>
        </div>

        {/* Login Form */}
        <div className="p-8">
          {/* Error Message */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg text-red-700 text-sm animate-shake flex items-start gap-3">
              <div className="text-red-500 flex-shrink-0">⚠️</div>
              <div>{error}</div>
            </div>
          )}

          {/* Role Selector (For Hackathon Demo Speed) */}
          <div className="flex bg-slate-100 p-1 rounded-lg mb-6">
            {["citizen", "officer", "admin"].map((r) => (
              <button
                key={r}
                onClick={() => setRole(r)}
                className={`flex-1 py-2 text-sm font-bold capitalize rounded-md transition-all ${
                  role === r
                    ? "bg-white shadow text-blue-600"
                    : "text-slate-500 hover:text-slate-700"
                }`}
              >
                {r}
              </button>
            ))}
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-1">
                {role === "citizen" ? "Mobile Number / Email" : "Official ID"}
              </label>
              <div className="relative">
                <div className="absolute left-3 top-3 text-slate-400">
                  {role === "citizen" ? (
                    <Smartphone size={18} />
                  ) : (
                    <Shield size={18} />
                  )}
                </div>
                <input
                  type="text"
                  name="mobile_number"
                  value={formData.mobile_number}
                  onChange={handleChange}
                  placeholder={
                    role === "citizen" ? "+91 98765 43210" : "EMP-ID-2024"
                  }
                  required
                  className="w-full pl-10 p-3 bg-slate-50 border border-slate-200 rounded-lg font-medium focus:outline-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-1">
                Password / OTP
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="••••••"
                required
                className="w-full p-3 bg-slate-50 border border-slate-200 rounded-lg font-medium focus:outline-blue-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-bold py-3.5 rounded-lg flex items-center justify-center gap-2 transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                  Logging in...
                </>
              ) : (
                <>
                  Login as {role} <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>

          {role === "citizen" && (
            <>
              <div className="mt-4 text-center text-xs text-slate-400">
                Or login via{" "}
                <span className="text-green-600 font-bold cursor-pointer">
                  WhatsApp
                </span>
              </div>
              <div className="mt-4 text-center text-sm text-slate-600">
                Don't have an account?{" "}
                <Link
                  to="/signup"
                  className="text-blue-600 font-bold hover:text-blue-700 transition-colors duration-200 hover:underline"
                >
                  Sign up here
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
