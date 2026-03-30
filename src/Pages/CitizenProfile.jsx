import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  User,
  Phone,
  Mail,
  MapPin,
  Globe,
  Hash,
  Edit2,
  Camera,
} from "lucide-react";
import Navbar from "../components/Navbar";
import CitizenNav from "../components/CitizenNav";
import { useAuth } from "../context/AuthContext";

export default function CitizenProfile() {
  const { user, loading: authLoading } = useAuth();
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (!authLoading) {
      if (!user) {
        navigate("/login");
      } else {
        setLoading(false);
      }
    }
  }, [user, authLoading, navigate]);

  if (loading || authLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
        <Navbar />
        <div className="max-w-6xl mx-auto px-4 py-8">
          <div className="bg-white/80 backdrop-blur-sm p-8 rounded-2xl border border-slate-200 shadow-xl text-center animate-pulse">
            <div className="w-20 h-20 bg-gradient-to-br from-orange-100 to-blue-100 rounded-full mx-auto mb-4"></div>
            <p className="text-slate-500 font-medium">
              Loading your profile...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
      <Navbar />
      <div className="max-w-6xl mx-auto px-4 py-8">
        <CitizenNav />

        {/* Profile Header Card */}
        <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl shadow-2xl p-8 mb-6 relative overflow-hidden animate-fade-in-up">
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -mr-32 -mt-32"></div>
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/10 rounded-full -ml-24 -mb-24"></div>

          <div className="relative flex flex-col md:flex-row items-center gap-6">
            <div className="relative group">
              <div className="w-32 h-32 bg-white rounded-full flex items-center justify-center shadow-xl ring-4 ring-white/30 group-hover:ring-white/50 transition-all duration-300">
                <User size={64} className="text-orange-600" />
              </div>
              <button className="absolute bottom-0 right-0 bg-white text-orange-600 p-2.5 rounded-full shadow-lg hover:bg-orange-50 transition-all duration-200 hover:scale-110">
                <Camera size={18} />
              </button>
            </div>

            <div className="text-center md:text-left flex-1">
              <h1 className="text-3xl font-bold text-white mb-2">
                {user?.full_name || "User"}
              </h1>
              <p className="text-orange-100 text-lg mb-4">Citizen Account</p>
              <div className="flex flex-wrap gap-3 justify-center md:justify-start">
                <span className="px-4 py-1.5 bg-white/20 backdrop-blur-sm text-white rounded-full text-sm font-medium border border-white/30">
                  ✓ Verified User
                </span>
                <span className="px-4 py-1.5 bg-white/20 backdrop-blur-sm text-white rounded-full text-sm font-medium border border-white/30">
                  {user?.language_preference || "English"}
                </span>
              </div>
            </div>

            <button className="px-6 py-3 bg-white text-orange-600 rounded-xl font-semibold shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200 flex items-center gap-2">
              <Edit2 size={18} />
              Edit Profile
            </button>
          </div>
        </div>

        {/* Profile Details Grid */}
        <div
          className="grid md:grid-cols-2 gap-6 animate-fade-in-up"
          style={{ animationDelay: "0.1s" }}
        >
          {/* Personal Information Card */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-slate-200 shadow-xl p-6 hover:shadow-2xl transition-all duration-300">
            <h2 className="text-xl font-bold text-slate-800 mb-6 flex items-center gap-2">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                <User size={20} className="text-white" />
              </div>
              Personal Information
            </h2>

            <div className="space-y-5">
              <div className="group">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-slate-100 rounded-lg group-hover:bg-blue-50 transition-colors">
                    <User
                      size={18}
                      className="text-slate-600 group-hover:text-blue-600 transition-colors"
                    />
                  </div>
                  <span className="text-sm font-medium text-slate-500 uppercase tracking-wide">
                    Full Name
                  </span>
                </div>
                <p className="font-semibold text-slate-800 text-lg ml-12">
                  {user?.full_name || "N/A"}
                </p>
              </div>

              <div className="h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent"></div>

              <div className="group">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-slate-100 rounded-lg group-hover:bg-blue-50 transition-colors">
                    <Hash
                      size={18}
                      className="text-slate-600 group-hover:text-blue-600 transition-colors"
                    />
                  </div>
                  <span className="text-sm font-medium text-slate-500 uppercase tracking-wide">
                    User ID
                  </span>
                </div>
                <p className="font-mono text-sm text-slate-700 ml-12 bg-slate-50 px-3 py-2 rounded-lg inline-block">
                  {user?.id || "N/A"}
                </p>
              </div>

              <div className="h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent"></div>

              <div className="group">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-slate-100 rounded-lg group-hover:bg-blue-50 transition-colors">
                    <Globe
                      size={18}
                      className="text-slate-600 group-hover:text-blue-600 transition-colors"
                    />
                  </div>
                  <span className="text-sm font-medium text-slate-500 uppercase tracking-wide">
                    Language
                  </span>
                </div>
                <p className="font-semibold text-slate-800 ml-12">
                  {user?.language_preference || "N/A"}
                </p>
              </div>
            </div>
          </div>

          {/* Contact Information Card */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-slate-200 shadow-xl p-6 hover:shadow-2xl transition-all duration-300">
            <h2 className="text-xl font-bold text-slate-800 mb-6 flex items-center gap-2">
              <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center">
                <Phone size={20} className="text-white" />
              </div>
              Contact Details
            </h2>

            <div className="space-y-5">
              <div className="group">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-slate-100 rounded-lg group-hover:bg-green-50 transition-colors">
                    <Phone
                      size={18}
                      className="text-slate-600 group-hover:text-green-600 transition-colors"
                    />
                  </div>
                  <span className="text-sm font-medium text-slate-500 uppercase tracking-wide">
                    Mobile Number
                  </span>
                </div>
                <p className="font-semibold text-slate-800 text-lg ml-12">
                  {user?.mobile_number || "N/A"}
                </p>
              </div>

              <div className="h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent"></div>

              <div className="group">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-slate-100 rounded-lg group-hover:bg-green-50 transition-colors">
                    <Mail
                      size={18}
                      className="text-slate-600 group-hover:text-green-600 transition-colors"
                    />
                  </div>
                  <span className="text-sm font-medium text-slate-500 uppercase tracking-wide">
                    Email Address
                  </span>
                </div>
                <p className="font-semibold text-slate-800 ml-12 break-all">
                  {user?.email || "N/A"}
                </p>
              </div>

              <div className="h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent"></div>

              <div className="group">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-slate-100 rounded-lg group-hover:bg-green-50 transition-colors">
                    <MapPin
                      size={18}
                      className="text-slate-600 group-hover:text-green-600 transition-colors"
                    />
                  </div>
                  <span className="text-sm font-medium text-slate-500 uppercase tracking-wide">
                    Address
                  </span>
                </div>
                <p className="font-semibold text-slate-800 ml-12 leading-relaxed">
                  {user?.residential_address || "N/A"}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div
          className="mt-6 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl shadow-xl p-6 animate-fade-in-up"
          style={{ animationDelay: "0.2s" }}
        >
          <h3 className="text-white font-bold text-lg mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button className="bg-white/20 backdrop-blur-sm hover:bg-white/30 text-white px-4 py-3 rounded-xl font-medium transition-all duration-200 hover:scale-105 border border-white/30">
              Change Password
            </button>
            <button className="bg-white/20 backdrop-blur-sm hover:bg-white/30 text-white px-4 py-3 rounded-xl font-medium transition-all duration-200 hover:scale-105 border border-white/30">
              Update Address
            </button>
            <button className="bg-white/20 backdrop-blur-sm hover:bg-white/30 text-white px-4 py-3 rounded-xl font-medium transition-all duration-200 hover:scale-105 border border-white/30">
              Download Data
            </button>
            <button className="bg-white/20 backdrop-blur-sm hover:bg-white/30 text-white px-4 py-3 rounded-xl font-medium transition-all duration-200 hover:scale-105 border border-white/30">
              Privacy Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
