import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  Shield,
  User,
  Phone,
  Mail,
  MapPin,
  Globe,
  ArrowRight,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Signup() {
  const navigate = useNavigate();
  const { signup } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [formData, setFormData] = useState({
    full_name: "",
    mobile_number: "",
    email: "",
    password: "",
    residential_address: "",
    language_preference: "English",
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setError(""); // Clear error on input change
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const result = await signup(formData);

    if (result.success) {
      navigate("/citizen");
    } else {
      setError(result.error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 via-slate-900 to-slate-800 p-4 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-10 animate-blob"></div>
        <div className="absolute top-40 right-10 w-72 h-72 bg-orange-500 rounded-full mix-blend-multiply filter blur-xl opacity-10 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-green-500 rounded-full mix-blend-multiply filter blur-xl opacity-10 animate-blob animation-delay-4000"></div>
      </div>

      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden relative z-10 animate-fade-in-up">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-8 text-center relative overflow-hidden">
          <div className="absolute inset-0 bg-black opacity-5"></div>
          <div className="mx-auto bg-white w-16 h-16 rounded-full flex items-center justify-center mb-4 shadow-lg relative z-10 transform transition-transform hover:scale-110 duration-300">
            <Shield className="text-blue-600" size={28} />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2 relative z-10">
            Create Account
          </h1>
          <p className="text-blue-50 relative z-10">
            Join CivicConnect Grievance Portal
          </p>
        </div>

        {/* Signup Form */}
        <div className="p-8">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg text-red-700 text-sm animate-shake flex items-start gap-3">
              <div className="text-red-500 flex-shrink-0">⚠️</div>
              <div>
                {typeof error === "string" ? error : JSON.stringify(error)}
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Full Name */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-1">
                Full Name
              </label>
              <div className="relative">
                <div className="absolute left-3 top-3 text-slate-400">
                  <User size={18} />
                </div>
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  placeholder="John Doe"
                  required
                  className="w-full pl-10 p-3 bg-slate-50 border border-slate-200 rounded-lg font-medium focus:outline-blue-500"
                />
              </div>
            </div>

            {/* Mobile Number */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-1">
                Mobile Number
              </label>
              <div className="relative">
                <div className="absolute left-3 top-3 text-slate-400">
                  <Phone size={18} />
                </div>
                <input
                  type="tel"
                  name="mobile_number"
                  value={formData.mobile_number}
                  onChange={handleChange}
                  placeholder="+91 98765 43210"
                  required
                  className="w-full pl-10 p-3 bg-slate-50 border border-slate-200 rounded-lg font-medium focus:outline-blue-500"
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-1">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute left-3 top-3 text-slate-400">
                  <Mail size={18} />
                </div>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="john@example.com"
                  required
                  className="w-full pl-10 p-3 bg-slate-50 border border-slate-200 rounded-lg font-medium focus:outline-blue-500"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-1">
                Password
              </label>
              <div className="relative">
                <div className="absolute left-3 top-3 text-slate-400">
                  <Shield size={18} />
                </div>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="••••••••"
                  required
                  minLength="6"
                  className="w-full pl-10 p-3 bg-slate-50 border border-slate-200 rounded-lg font-medium focus:outline-blue-500"
                />
              </div>
            </div>

            {/* Residential Address */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-1">
                Residential Address
              </label>
              <div className="relative">
                <div className="absolute left-3 top-3 text-slate-400">
                  <MapPin size={18} />
                </div>
                <input
                  type="text"
                  name="residential_address"
                  value={formData.residential_address}
                  onChange={handleChange}
                  placeholder="123 Main St, Mumbai"
                  required
                  className="w-full pl-10 p-3 bg-slate-50 border border-slate-200 rounded-lg font-medium focus:outline-blue-500"
                />
              </div>
            </div>

            {/* Language Preference */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-1">
                Language Preference
              </label>
              <div className="relative">
                <div className="absolute left-3 top-3 text-slate-400">
                  <Globe size={18} />
                </div>
                <select
                  name="language_preference"
                  value={formData.language_preference}
                  onChange={handleChange}
                  className="w-full pl-10 p-3 bg-slate-50 border border-slate-200 rounded-lg font-medium focus:outline-blue-500"
                >
                  <option>English</option>
                  <option>Hindi</option>
                  <option>Marathi</option>
                  <option>Tamil</option>
                  <option>Telugu</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-bold py-3.5 rounded-lg flex items-center justify-center gap-2 transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                  Creating Account...
                </>
              ) : (
                <>
                  Create Account{" "}
                  <ArrowRight
                    size={18}
                    className="group-hover:translate-x-1 transition-transform"
                  />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-slate-600">
            Already have an account?{" "}
            <Link
              to="/login"
              className="text-blue-600 font-bold hover:text-blue-700 transition-colors duration-200 hover:underline"
            >
              Login here
            </Link>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-100 text-center text-xs text-slate-400">
            By signing up, you agree to our Terms of Service and Privacy Policy
          </div>
        </div>
      </div>
    </div>
  );
}
