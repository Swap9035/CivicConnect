import React from "react";
import { Link } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  ArrowRight,
  CheckCircle2,
  BarChart3,
  Users,
  Clock,
} from "lucide-react";
import Navbar from "../components/Navbar";
import heroIll from "../assets/hero2.svg";

export default function Home() {
  const navigate = useNavigate();
  const { user } = useAuth() || {};
  const handleLodge = () => {
    if (user) navigate("/citizen");
    else navigate("/login", { state: { redirectTo: "/citizen" } });
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900">
      <Navbar />

      {/* HERO SECTION */}
      <div className="bg-gradient-to-b from-white to-slate-50">
        <div className="max-w-7xl mx-auto px-4 py-20 sm:px-6 lg:px-8 grid md:grid-cols-2 gap-12 items-center">
          <div className="space-y-6 animate-fade-in-up">
            <div className="inline-block px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-bold mb-4">
              🏛️ Government Initiative
            </div>
            <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight leading-tight text-slate-900 bg-clip-text">
              Unified Grievance Redressal Portal
            </h1>
            <p className="text-lg text-slate-600 max-w-xl leading-relaxed">
              A government-grade citizen grievance platform — submit complaints
              via text, images or voice, track progress, and view official
              responses transparently.
            </p>
            <div className="flex flex-wrap gap-4 pt-4">
              <button
                type="button"
                onClick={handleLodge}
                className="bg-gradient-to-r from-orange-600 to-orange-700 hover:from-orange-700 hover:to-orange-800 text-white px-6 py-3.5 rounded-lg font-semibold shadow-lg hover:shadow-xl flex items-center gap-2 transform hover:-translate-y-0.5 transition-all duration-200"
                aria-label="Lodge Complaint"
              >
                Lodge Complaint{" "}
                <ArrowRight
                  size={18}
                  className="group-hover:translate-x-1 transition-transform"
                />
              </button>

              <Link
                to="/contact"
                className="bg-white border-2 border-slate-200 hover:border-blue-300 hover:bg-blue-50 px-6 py-3 rounded-lg font-semibold text-slate-800 hover:text-blue-600 transition-all duration-200"
              >
                Contact Helpdesk
              </Link>
            </div>
            <div className="mt-6 p-4 bg-blue-50 border-l-4 border-blue-500 rounded-lg text-sm text-slate-700">
              <strong>Note:</strong> This portal is maintained by the municipal
              administration. All complaints are tracked with unique IDs and
              SLAs.
            </div>
          </div>
          <div className="flex items-center justify-center animate-slide-in-right">
            <div className="w-full max-w-lg shadow-2xl rounded-2xl overflow-hidden border border-slate-100 transform hover:scale-105 transition-transform duration-300">
              <img
                src={heroIll}
                alt="hero professional"
                className="w-full h-64 object-cover"
              />
            </div>
          </div>
        </div>
      </div>

      {/* STATS STRIP */}
      <div className="bg-white border-y border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-10 grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { label: "Total Grievances", val: "1.2M+", icon: BarChart3 },
            {
              label: "Resolved Cases",
              val: "98%",
              icon: CheckCircle2,
              color: "text-green-600",
            },
            { label: "Avg Response Time", val: "4 Hrs", icon: Clock },
            { label: "Active Officers", val: "15k+", icon: Users },
          ].map((stat, idx) => (
            <div
              key={idx}
              className="flex items-center gap-4 group hover:scale-105 transition-transform duration-200"
            >
              <div
                className={`p-4 rounded-xl bg-gradient-to-br from-slate-50 to-slate-100 group-hover:shadow-md transition-shadow ${
                  stat.color || "text-slate-600"
                }`}
              >
                <stat.icon size={28} />
              </div>
              <div>
                <div className="text-3xl font-bold text-slate-900">
                  {stat.val}
                </div>
                <div className="text-xs font-bold text-slate-500 uppercase tracking-wide">
                  {stat.label}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* FEATURES SECTION */}
      <div className="py-20 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900">
              Why choose CivicConnect?
            </h2>
            <p className="text-slate-500 mt-2">
              Next-generation governance powered by Agentic AI
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Card 1 */}
            <div className="bg-white p-8 rounded-2xl shadow-md border border-slate-200 hover:shadow-2xl hover:border-blue-300 transition-all duration-300 transform hover:-translate-y-2 group">
              <div className="w-14 h-14 bg-gradient-to-br from-blue-100 to-blue-200 rounded-xl flex items-center justify-center text-blue-600 mb-6 group-hover:scale-110 transition-transform duration-200">
                <Users size={26} />
              </div>
              <h3 className="text-xl font-bold text-slate-800 mb-3 group-hover:text-blue-600 transition-colors">
                AI-Powered Sorting
              </h3>
              <p className="text-slate-600 leading-relaxed">
                Our Triage Agent automatically categorizes complaints and
                assigns severity scores, ensuring critical issues get handled
                first.
              </p>
            </div>

            {/* Card 2 */}
            <div className="bg-white p-8 rounded-2xl shadow-md border border-slate-200 hover:shadow-2xl hover:border-orange-300 transition-all duration-300 transform hover:-translate-y-2 group">
              <div className="w-14 h-14 bg-gradient-to-br from-orange-100 to-orange-200 rounded-xl flex items-center justify-center text-orange-600 mb-6 group-hover:scale-110 transition-transform duration-200">
                <Clock size={26} />
              </div>
              <h3 className="text-xl font-bold text-slate-800 mb-3 group-hover:text-orange-600 transition-colors">
                Instant Drafting
              </h3>
              <p className="text-slate-600 leading-relaxed">
                Officers receive pre-drafted legal notices generated by AI,
                reducing paperwork time by 90% and speeding up resolutions.
              </p>
            </div>

            {/* Card 3 */}
            <div className="bg-white p-8 rounded-2xl shadow-md border border-slate-200 hover:shadow-2xl hover:border-green-300 transition-all duration-300 transform hover:-translate-y-2 group">
              <div className="w-14 h-14 bg-gradient-to-br from-green-100 to-green-200 rounded-xl flex items-center justify-center text-green-600 mb-6 group-hover:scale-110 transition-transform duration-200">
                <CheckCircle2 size={26} />
              </div>
              <h3 className="text-xl font-bold text-slate-800 mb-3 group-hover:text-green-600 transition-colors">
                Visual Verification
              </h3>
              <p className="text-slate-600 leading-relaxed">
                Computer Vision compares "Before" and "After" photos to prevent
                fake closures and ensure 100% accountability.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ROLE CARDS - align with Excalidraw roles */}
      <div className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4">
          <h3 className="text-center text-2xl font-bold mb-8">
            Choose your access
          </h3>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="p-6 rounded-2xl border border-slate-100 shadow-sm text-center">
              <div className="w-16 h-16 rounded-full bg-blue-50 mx-auto flex items-center justify-center text-blue-600 font-bold mb-4">
                C
              </div>
              <h4 className="font-bold">Citizen</h4>
              <p className="text-sm text-slate-500 mt-2">
                Login, lodge complaints via voice/photo, track status, provide
                feedback.
              </p>
              <button
                onClick={handleLodge}
                className="inline-block mt-4 text-sm font-semibold text-orange-600"
              >
                Open Portal →
              </button>
            </div>

            <div className="p-6 rounded-2xl border border-slate-100 shadow-sm text-center">
              <div className="w-16 h-16 rounded-full bg-green-50 mx-auto flex items-center justify-center text-green-600 font-bold mb-4">
                O
              </div>
              <h4 className="font-bold">Officer</h4>
              <p className="text-sm text-slate-500 mt-2">
                Assigned cases, AI drafting, upload evidence, close with photos.
              </p>
              <Link
                to="/officer"
                className="inline-block mt-4 text-sm font-semibold text-orange-600"
              >
                Officer Login →
              </Link>
            </div>

            <div className="p-6 rounded-2xl border border-slate-100 shadow-sm text-center">
              <div className="w-16 h-16 rounded-full bg-orange-50 mx-auto flex items-center justify-center text-orange-600 font-bold mb-4">
                A
              </div>
              <h4 className="font-bold">Admin</h4>
              <p className="text-sm text-slate-500 mt-2">
                Manage departments, employees, escalation rules and feedback.
              </p>
              <Link
                to="/admin"
                className="inline-block mt-4 text-sm font-semibold text-orange-600"
              >
                Admin Console →
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* FOOTER */}
      <footer className="bg-slate-900 text-slate-400 py-12 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 grid md:grid-cols-4 gap-8 text-sm">
          <div>
            <h4 className="text-white font-bold mb-4">CivicConnect</h4>
            <p>
              Empowering citizens through transparent and efficient governance
              technology.
            </p>
          </div>
          <div>
            <h4 className="text-white font-bold mb-4">Quick Links</h4>
            <ul className="space-y-2">
              <li>
                <a href="#" className="hover:text-white">
                  Home
                </a>
              </li>
              <li>
                <button
                  onClick={handleLodge}
                  className="hover:text-white text-left"
                >
                  Lodge Grievance
                </button>
              </li>
              <li>
                <a href="#" className="hover:text-white">
                  Track Status
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-bold mb-4">Legal</h4>
            <ul className="space-y-2">
              <li>
                <a href="#" className="hover:text-white">
                  Privacy Policy
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white">
                  Terms of Service
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-bold mb-4">Contact</h4>
            <p>Helpline: 1800-11-2233</p>
            <p>Email: support@civicconnect.gov.in</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
