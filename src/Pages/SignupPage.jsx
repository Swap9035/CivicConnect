import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  Shield,
  User,
  Mail,
  Phone,
  MapPin,
  Globe,
  ArrowRight,
  AlertCircle,
} from "lucide-react";
import { signupUser } from "../utils/api";

export default function SignupPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    mobile: "",
    password: "",
    address: "",
    language: "English",
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      await signupUser({
        full_name: formData.fullName,
        email: formData.email,
        mobile_number: formData.mobile,
        password: formData.password,
        residential_address: formData.address,
        language_preference: formData.language,
      });

      // Success - redirect to login
      navigate("/login");
    } catch (err) {
      setError(err.message || "Signup failed. Please try again.");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl overflow-hidden">
        {/* Header */}
        <div className="bg-blue-600 p-6 text-center">
          <div className="mx-auto bg-white w-14 h-14 rounded-full flex items-center justify-center mb-3">
            <Shield className="text-blue-600" size={28} />
          </div>
          <h1 className="text-2xl font-bold text-white">Create Your Account</h1>
          <p className="text-blue-100 text-sm mt-1">
            Join CivicConnect - Unified Grievance Portal
          </p>
        </div>

        {/* Signup Form */}
        <div className="p-8">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle
                className="text-red-500 flex-shrink-0 mt-0.5"
                size={20}
              />
              <div className="text-sm text-red-700">{error}</div>
            </div>
          )}

          <form onSubmit={handleSignup} className="space-y-5">
            {/* 2-Column Grid Layout for Larger Screens */}
            <div className="grid md:grid-cols-2 gap-5">
              {/* Full Name */}
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-2">
                  Full Name *
                </label>
                <div className="relative">
                  <div className="absolute left-3 top-3 text-slate-400">
                    <User size={18} />
                  </div>
                  <input
                    type="text"
                    name="fullName"
                    value={formData.fullName}
                    onChange={handleChange}
                    placeholder="John Doe"
                    required
                    className="w-full pl-10 p-3 bg-slate-50 border border-slate-200 rounded-lg font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Email */}
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-2">
                  Email Address *
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
                    placeholder="john.doe@example.com"
                    required
                    className="w-full pl-10 p-3 bg-slate-50 border border-slate-200 rounded-lg font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Mobile Number */}
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-2">
                  Mobile Number *
                </label>
                <div className="relative">
                  <div className="absolute left-3 top-3 text-slate-400">
                    <Phone size={18} />
                  </div>
                  <input
                    type="tel"
                    name="mobile"
                    value={formData.mobile}
                    onChange={handleChange}
                    placeholder="+91 98765 43210"
                    required
                    className="w-full pl-10 p-3 bg-slate-50 border border-slate-200 rounded-lg font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-2">
                  Password *
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
                    className="w-full pl-10 p-3 bg-slate-50 border border-slate-200 rounded-lg font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>

            {/* Residential Address - Full Width */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-2">
                Residential Address *
              </label>
              <div className="relative">
                <div className="absolute left-3 top-3 text-slate-400">
                  <MapPin size={18} />
                </div>
                <textarea
                  name="address"
                  value={formData.address}
                  onChange={handleChange}
                  placeholder="Enter your complete residential address"
                  required
                  rows="3"
                  className="w-full pl-10 p-3 bg-slate-50 border border-slate-200 rounded-lg font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                />
              </div>
            </div>

            {/* Language Preference */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-2">
                Language Preference *
              </label>
              <div className="relative">
                <div className="absolute left-3 top-3 text-slate-400">
                  <Globe size={18} />
                </div>
                <select
                  name="language"
                  value={formData.language}
                  onChange={handleChange}
                  className="w-full pl-10 p-3 bg-slate-50 border border-slate-200 rounded-lg font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none cursor-pointer"
                >
                  <option value="English">English</option>
                  <option value="Hindi">हिंदी (Hindi)</option>
                  <option value="Marathi">मराठी (Marathi)</option>
                  <option value="Tamil">தமிழ் (Tamil)</option>
                  <option value="Telugu">తెలుగు (Telugu)</option>
                  <option value="Bengali">বাংলা (Bengali)</option>
                  <option value="Gujarati">ગુજરાતી (Gujarati)</option>
                  <option value="Kannada">ಕನ್ನಡ (Kannada)</option>
                  <option value="Malayalam">മലയാളം (Malayalam)</option>
                  <option value="Punjabi">ਪੰਜਾਬੀ (Punjabi)</option>
                  <option value="Spanish">Español (Spanish)</option>
                </select>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-bold py-3 rounded-lg flex items-center justify-center gap-2 transition-all shadow-md active:scale-95 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Creating Account...
                </>
              ) : (
                <>
                  Sign Up <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>

          {/* Login Link */}
          <div className="mt-6 text-center text-sm text-slate-600">
            Already have an account?{" "}
            <Link
              to="/login"
              className="text-blue-600 font-bold hover:text-blue-700 hover:underline"
            >
              Login here
            </Link>
          </div>

          {/* Terms Notice */}
          <div className="mt-4 text-center text-xs text-slate-400">
            By signing up, you agree to our Terms of Service and Privacy Policy
          </div>
        </div>
      </div>
    </div>
  );
}
