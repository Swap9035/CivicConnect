import React, { useState } from 'react';
import Navbar from '../components/Navbar';

export default function Contact() {
  const [sent, setSent] = useState(false);
  const [form, setForm] = useState({name:'', email:'', message:''});

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <div className="max-w-3xl mx-auto p-6">
        <h1 className="text-2xl font-bold mb-4">Contact & Helpdesk</h1>
        <p className="text-slate-600 mb-6">For assistance, reach out to the helpdesk or use the grievance portal to lodge an issue.</p>

        {!sent ? (
          <form onSubmit={(e)=>{e.preventDefault(); setSent(true);}} className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
            <div className="grid grid-cols-1 gap-4">
              <input placeholder="Full name" value={form.name} onChange={e=>setForm({...form,name:e.target.value})} className="p-3 border rounded" />
              <input placeholder="Email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})} className="p-3 border rounded" />
              <textarea placeholder="Message" value={form.message} onChange={e=>setForm({...form,message:e.target.value})} className="p-3 border rounded h-32" />
              <div className="flex justify-end">
                <button className="bg-orange-600 text-white px-4 py-2 rounded-md">Send</button>
              </div>
            </div>
          </form>
        ) : (
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 text-center">
            <h3 className="font-bold text-lg">Message Sent</h3>
            <p className="text-slate-600 mt-2">Our helpdesk will contact you soon.</p>
            <button onClick={()=>{setSent(false); setForm({name:'',email:'',message:''})}} className="mt-4 text-blue-600 font-semibold">Send another</button>
          </div>
        )}
      </div>
    </div>
  );
}
