import React from 'react';
import { NavLink } from 'react-router-dom';

export default function CitizenNav(){
  const items = [
    {to:'/citizen/profile', label:'Profile'},
    {to:'/citizen/current', label:'Current Grievances'},
    {to:'/citizen/previous', label:'Previous Grievances'},
    {to:'/citizen/status', label:'Status Tracker'},
  ];
  return (
    <nav className="bg-white p-3 rounded-md border border-slate-100 mb-4">
      <div className="flex gap-3">
        {items.map(i=> (
          <NavLink key={i.to} to={i.to} className={({isActive})=>`px-3 py-2 rounded-md text-sm font-medium ${isActive? 'bg-orange-50 text-orange-600 border border-orange-100':'text-slate-700 hover:bg-slate-50'}`}>
            {i.label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
