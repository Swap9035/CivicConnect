import React from "react";
import { Link } from "react-router-dom";
import { Shield } from "lucide-react";
import emblem from "../assets/emblem.svg";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

export default function Navbar() {
  const { user, logout } = useAuth() || {};
  const navigate = useNavigate();

  const handleLodgeClick = () => {
    if (user) navigate("/citizen");
    else navigate("/login", { state: { redirectTo: "/citizen" } });
  };

  const handleLogout = async () => {
    try {
      if (typeof logout === "function") await logout();
    } catch (e) {
      // ignore logout errors
    }
    try {
      localStorage.removeItem("authToken");
    } catch {}
    navigate("/login");
  };

  return (
    <nav className="bg-white/95 backdrop-blur-sm text-slate-900 border-b border-slate-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Logo Section */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="p-1 bg-slate-50 rounded-md border border-slate-100 group-hover:border-blue-200 transition-colors duration-200">
              <img
                src={emblem}
                alt="emblem"
                className="w-11 h-11 group-hover:scale-110 transition-transform duration-200"
              />
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-extrabold tracking-wide leading-none group-hover:text-blue-600 transition-colors">
                CivicConnect
              </span>
              <span className="text-xs text-slate-500 uppercase tracking-wider">
                Unified Grievance Portal
              </span>
            </div>
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
            <Link
              to="/"
              className="hover:text-blue-600 transition-colors duration-200 relative after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-0 after:bg-blue-600 after:transition-all after:duration-200 hover:after:w-full"
            >
              Home
            </Link>
            <Link
              to="/about"
              className="hover:text-blue-600 transition-colors duration-200 relative after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-0 after:bg-blue-600 after:transition-all after:duration-200 hover:after:w-full"
            >
              About
            </Link>
            <Link
              to="/citizen"
              className="hover:text-blue-600 transition-colors duration-200 relative after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-0 after:bg-blue-600 after:transition-all after:duration-200 hover:after:w-full"
            >
              Citizen Portal
            </Link>
            <Link
              to="/contact"
              className="hover:text-blue-600 transition-colors duration-200 relative after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-0 after:bg-blue-600 after:transition-all after:duration-200 hover:after:w-full"
            >
              Contact
            </Link>
          </div>

          {/* Action Button */}
          <div className="flex gap-3 items-center">
            <button
              type="button"
              onClick={handleLodgeClick}
              className="bg-gradient-to-r from-orange-600 to-orange-700 hover:from-orange-700 hover:to-orange-800 text-white px-5 py-2.5 rounded-lg text-sm font-semibold transition-all shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
              aria-label="Lodge Grievance"
            >
              Lodge Grievance
            </button>
            {!user ? (
              <Link
                to="/login"
                className="border-2 border-slate-200 hover:border-blue-300 hover:bg-blue-50 text-slate-700 hover:text-blue-600 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200"
              >
                Official Login
              </Link>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/citizen/profile"
                  className="px-3 py-2 rounded-md text-sm font-semibold bg-slate-50 border border-slate-100 text-slate-700"
                >
                  {user.full_name ? user.full_name.split(" ")[0] : "Account"}
                </Link>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 border-2 border-slate-200 hover:bg-red-50 text-red-600 rounded-lg text-sm font-semibold transition-all duration-200"
                  aria-label="Logout"
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
