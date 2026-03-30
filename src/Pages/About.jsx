import React from 'react';
import Navbar from '../components/Navbar';
import { Target, Shield, Users, Award } from 'lucide-react';
import emblem from '../assets/emblem.svg';

export default function About() {
  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900">
      <Navbar />
      
      {/* Hero Section */}
      <div className="bg-white py-16 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <img src={emblem} alt="emblem" className="mx-auto w-24 h-24 mb-4" />
          <h1 className="text-3xl font-bold mb-2 text-slate-900">About the Unified Grievance Portal</h1>
          <p className="text-slate-600 max-w-3xl mx-auto">
            This portal provides citizens a single point to lodge grievances, track their status, and receive verified responses from the municipal administration. The system is built to ensure transparency, accountability and fast redressal of civic issues.
          </p>
        </div>
      </div>

      {/* Mission & Capabilities */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-slate-800">Mission & Capabilities</h2>
            <p className="text-slate-600 leading-relaxed">We enable citizens to submit complaints with multimodal inputs (text, voice, images), automatically triage issues using AI-assisted tools, and provide an auditable response trail backed by geo-tagged evidence.</p>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-blue-50 rounded-xl border border-blue-100">
                <Target className="text-blue-600 mb-2" />
                <div className="font-bold text-slate-800">Transparent Tracking</div>
              </div>
              <div className="p-4 bg-orange-50 rounded-xl border border-orange-100">
                <Shield className="text-orange-600 mb-2" />
                <div className="font-bold text-slate-800">Verified Evidence</div>
              </div>
            </div>
          </div>
          <div className="bg-slate-50 p-6 rounded-xl border border-slate-100">
            <h3 className="font-bold mb-3">How it Works</h3>
            <ol className="list-decimal list-inside text-slate-600 text-sm">
              <li>Submit complaint via the portal or WhatsApp bot.</li>
              <li>AI extracts key details and suggests categorization.</li>
              <li>Officer reviews, validates evidence and issues directives.</li>
              <li>Citizen receives response and can confirm resolution with evidence.</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}