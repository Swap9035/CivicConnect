import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import Login from "./Pages/Login";
import Signup from "./Pages/Signup";
import Home from "./Pages/Home";
import About from "./Pages/About";
import CitizenPortal from "./Pages/CitizenPortal";
import CitizenProfile from "./Pages/CitizenProfile";
import CitizenCurrent from "./Pages/CitizenCurrent";
import CitizenPrevious from "./Pages/CitizenPrevious";
import CitizenStatus from "./Pages/CitizenStatus";
import OfficerDashboard from "./Pages/OfficerDashboard";
import AdminDashboard from "./Pages/AdminDashboard";
import Contact from "./Pages/Contact";

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-slate-50 font-sans text-slate-900">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/about" element={<About />} />
            <Route path="/citizen" element={<CitizenPortal />} />
            <Route path="/citizen/profile" element={<CitizenProfile />} />
            <Route path="/citizen/current" element={<CitizenCurrent />} />
            <Route path="/citizen/previous" element={<CitizenPrevious />} />
            <Route path="/citizen/status" element={<CitizenStatus />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/officer" element={<OfficerDashboard />} />
            <Route path="/admin" element={<AdminDashboard />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
