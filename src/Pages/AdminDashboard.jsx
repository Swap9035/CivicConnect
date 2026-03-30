import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom";
import {
  ShieldAlert,
  Users,
  Plus,
  Settings,
  TrendingUp,
  Building2,
  UserPlus,
  X,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  Eye,
  Edit2,
  MapPin,
  Phone,
  Mail,
  Briefcase,
  RefreshCw,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import { adminAPI, feedbackAPI } from "../services/api";
import api from "../services/api"; // add this import
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

// Constants
const DEPARTMENTS = [
  "Electricity",
  "Water",
  "Sanitation",
  "Roads",
  "Health",
  "Education",
];
const ROLES = ["SUPER_ADMIN", "DEPT_ADMIN", "NODAL_OFFICER"];

export default function AdminDashboard() {
  const { logout, user } = useAuth() || {};
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      if (typeof logout === "function") await logout();
    } catch {}
    try {
      localStorage.removeItem("authToken");
    } catch {}
    navigate("/login");
  };

  // State for users list
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);

  // Filters
  const [filters, setFilters] = useState({
    dept: "",
    ward: "",
    role: "",
  });

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [showJurisdictionModal, setShowJurisdictionModal] = useState(false);
  const [showConflictsModal, setShowConflictsModal] = useState(false);
  const [showFeedbacksModal, setShowFeedbacksModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);

  // Create user form
  const [createForm, setCreateForm] = useState({
    full_name: "",
    employee_id: "",
    email: "",
    phone_number: "",
    role: "NODAL_OFFICER",
    dept: "Electricity",
    ward: "",
    designation: "",
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState("");
  const [createSuccess, setCreateSuccess] = useState("");

  // Jurisdiction update form
  const [jurisdictionForm, setJurisdictionForm] = useState({
    staff_id: "",
    new_ward: "",
    new_dept: "",
  });
  const [jurisdictionLoading, setJurisdictionLoading] = useState(false);
  const [jurisdictionError, setJurisdictionError] = useState("");

  // Conflicts state
  const [conflicts, setConflicts] = useState([]);
  const [conflictsLoading, setConflictsLoading] = useState(false);
  const [conflictsTotal, setConflictsTotal] = useState(0);

  // Feedbacks state
  const [feedbacks, setFeedbacks] = useState([]);
  const [feedbacksLoading, setFeedbacksLoading] = useState(false);
  const [feedbacksTotal, setFeedbacksTotal] = useState(0);

  // Feedback detail modal state
  const [feedbackDetail, setFeedbackDetail] = useState(null);
  const [feedbackDetailLoading, setFeedbackDetailLoading] = useState(false);
  const [showFeedbackDetailModal, setShowFeedbackDetailModal] = useState(false);

  // Fetch users function
  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await adminAPI.getUsers({
        ...filters,
        page,
        page_size: pageSize,
      });
      setUsers(response.data.users || []);
      setTotalCount(response.data.total_count || 0);
    } catch (error) {
      console.error("Failed to fetch users:", error);
      setUsers([]);
    }
    setLoading(false);
  };

  // Fetch conflicts function
  const fetchConflicts = async (skip = 0, limit = 20) => {
    setConflictsLoading(true);
    try {
      const res = await feedbackAPI.getConflicts(skip, limit);
      setConflicts(res.data.conflicts || []);
      setConflictsTotal(res.data.total || 0);
    } catch (err) {
      console.error("Failed to load conflicts", err);
      setConflicts([]);
    }
    setConflictsLoading(false);
  };

  // Fetch feedbacks function
  const fetchFeedbacks = async (skip = 0, limit = 50) => {
    setFeedbacksLoading(true);
    try {
      const res = await feedbackAPI.getFeedbacks(skip, limit);
      setFeedbacks(res.data.feedbacks || []);
      setFeedbacksTotal(res.data.total || 0);
    } catch (err) {
      console.error("Failed to load feedbacks", err);
      setFeedbacks([]);
    }
    setFeedbacksLoading(false);
  };

  // Fetch users on mount and when filters/page change
  useEffect(() => {
    fetchUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, filters.dept, filters.ward, filters.role]);

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setCreateLoading(true);
    setCreateError("");
    setCreateSuccess("");

    try {
      await adminAPI.createUser(createForm);
      setCreateSuccess("User created successfully!");
      setCreateForm({
        full_name: "",
        employee_id: "",
        email: "",
        phone_number: "",
        role: "NODAL_OFFICER",
        dept: "Electricity",
        ward: "",
        designation: "",
      });
      fetchUsers();
      setTimeout(() => {
        setShowCreateModal(false);
        setCreateSuccess("");
      }, 2000);
    } catch (error) {
      setCreateError(error.response?.data?.detail || "Failed to create user");
    }
    setCreateLoading(false);
  };

  const handleViewDetails = async (staffId) => {
    try {
      const response = await adminAPI.getUserDetails(staffId);
      setSelectedUser(response.data);
      setShowDetailsModal(true);
    } catch (error) {
      console.error("Failed to fetch user details:", error);
    }
  };

  const openJurisdictionModal = (user) => {
    setJurisdictionForm({
      staff_id: user.staff_id,
      new_ward: user.metadata?.ward || "",
      new_dept: user.metadata?.dept || "",
    });
    setSelectedUser(user);
    setShowJurisdictionModal(true);
    setJurisdictionError("");
  };

  const handleUpdateJurisdiction = async (e) => {
    e.preventDefault();
    setJurisdictionLoading(true);
    setJurisdictionError("");

    try {
      await adminAPI.updateJurisdiction(jurisdictionForm);
      fetchUsers();
      setShowJurisdictionModal(false);
    } catch (error) {
      setJurisdictionError(
        error.response?.data?.detail || "Failed to update jurisdiction"
      );
    }
    setJurisdictionLoading(false);
  };

  const buildImageUrl = (p) => {
    if (!p) return null;
    if (typeof p !== "string") return null;
    if (p.startsWith("http")) return p;
    const cleaned = p.replace(/^\.\/?/, "").replace(/\\/g, "/");
    return `${api.defaults.baseURL.replace(/\/$/, "")}/${cleaned}`;
  };

  const viewFeedbackDetail = async (feedbackId) => {
    if (!feedbackId) return;
    setFeedbackDetailLoading(true);
    setFeedbackDetail(null);
    setShowFeedbackDetailModal(true);
    try {
      const res = await feedbackAPI.getFeedback(feedbackId);
      setFeedbackDetail(res.data || res);
    } catch (err) {
      console.error("Failed to fetch feedback detail", err);
      setFeedbackDetail({
        error: err?.response?.data?.detail || "Failed to load feedback",
      });
    } finally {
      setFeedbackDetailLoading(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize)) || 1;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200 font-sans">
      {/* Admin Navbar */}
      <nav className="bg-gradient-to-r from-slate-900 to-slate-800 text-white p-4 sticky top-0 z-50 shadow-xl">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg flex items-center justify-center">
              <ShieldAlert size={22} />
            </div>
            <span className="font-bold text-xl tracking-wide">
              ADMIN CONTROL PANEL
            </span>
          </div>
          <div className="flex gap-4 text-sm items-center">
            <button
              onClick={() => {
                fetchConflicts();
                setShowConflictsModal(true);
              }}
              className="px-3 py-2 bg-yellow-500 hover:bg-yellow-600 rounded text-white font-semibold"
              title="View Conflicts"
            >
              View Conflicts
            </button>

            <button
              onClick={() => {
                fetchFeedbacks();
                setShowFeedbacksModal(true);
              }}
              className="px-3 py-2 bg-slate-100 hover:bg-white rounded text-slate-800 font-semibold"
              title="All Feedbacks"
            >
              All Feedbacks
            </button>

            <button
              onClick={fetchUsers}
              className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
              title="Refresh"
            >
              <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
            </button>
            {user ? (
              <button
                onClick={handleLogout}
                className="px-3 py-1 border border-red-600 text-red-600 rounded hover:bg-red-50 transition-colors"
                title="Logout"
              >
                Logout
              </button>
            ) : null}
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto p-8">
        {/* Header */}
        <header className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-slate-800">
              User Management
            </h1>
            <p className="text-slate-500 mt-1">
              Manage staff users, roles and jurisdictions
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white px-5 py-3 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-0.5"
          >
            <Plus size={20} /> Add New User
          </button>
        </header>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-2xl shadow-md border border-slate-200 hover:shadow-lg transition-shadow">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-100 to-blue-200 rounded-xl flex items-center justify-center text-blue-600">
                <Users size={24} />
              </div>
              <div>
                <div className="text-3xl font-bold text-slate-800">
                  {totalCount}
                </div>
                <div className="text-sm text-slate-500">Total Users</div>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-2xl shadow-md border border-slate-200 hover:shadow-lg transition-shadow">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-green-100 to-green-200 rounded-xl flex items-center justify-center text-green-600">
                <CheckCircle size={24} />
              </div>
              <div>
                <div className="text-3xl font-bold text-slate-800">
                  {users.filter((u) => u.account_status?.is_active).length}
                </div>
                <div className="text-sm text-slate-500">Active Users</div>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-2xl shadow-md border border-slate-200 hover:shadow-lg transition-shadow">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-orange-100 to-orange-200 rounded-xl flex items-center justify-center text-orange-600">
                <Building2 size={24} />
              </div>
              <div>
                <div className="text-3xl font-bold text-slate-800">
                  {DEPARTMENTS.length}
                </div>
                <div className="text-sm text-slate-500">Departments</div>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-2xl shadow-md border border-slate-200 hover:shadow-lg transition-shadow">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-100 to-purple-200 rounded-xl flex items-center justify-center text-purple-600">
                <ShieldAlert size={24} />
              </div>
              <div>
                <div className="text-3xl font-bold text-slate-800">
                  {ROLES.length}
                </div>
                <div className="text-sm text-slate-500">Role Types</div>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white p-6 rounded-2xl shadow-md border border-slate-200 mb-6">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2 text-slate-600">
              <Filter size={18} />
              <span className="font-semibold">Filters:</span>
            </div>

            <select
              value={filters.dept}
              onChange={(e) => setFilters({ ...filters, dept: e.target.value })}
              className="px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50"
            >
              <option value="">All Departments</option>
              {DEPARTMENTS.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>

            <select
              value={filters.role}
              onChange={(e) => setFilters({ ...filters, role: e.target.value })}
              className="px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50"
            >
              <option value="">All Roles</option>
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r.replace("_", " ")}
                </option>
              ))}
            </select>

            <input
              type="text"
              placeholder="Filter by Ward..."
              value={filters.ward}
              onChange={(e) => setFilters({ ...filters, ward: e.target.value })}
              className="px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50"
            />

            <button
              onClick={() => setFilters({ dept: "", ward: "", role: "" })}
              className="px-4 py-2 text-slate-600 hover:text-red-600 transition-colors"
            >
              Clear Filters
            </button>
          </div>
        </div>

        {/* Users Table */}
        <div className="bg-white rounded-2xl shadow-md border border-slate-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-gradient-to-r from-slate-50 to-slate-100 border-b border-slate-200">
                <tr>
                  <th className="p-4 text-xs font-bold text-slate-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="p-4 text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Employee ID
                  </th>
                  <th className="p-4 text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="p-4 text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Department
                  </th>
                  <th className="p-4 text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Ward
                  </th>
                  <th className="p-4 text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="p-4 text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {loading ? (
                  <tr>
                    <td colSpan="7" className="p-8 text-center">
                      <div className="flex items-center justify-center gap-3">
                        <div className="animate-spin rounded-full h-6 w-6 border-2 border-blue-600 border-t-transparent"></div>
                        <span className="text-slate-500">Loading users...</span>
                      </div>
                    </td>
                  </tr>
                ) : users.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="p-8 text-center text-slate-500">
                      No users found. Try adjusting filters or create a new
                      user.
                    </td>
                  </tr>
                ) : (
                  users.map((user) => (
                    <tr
                      key={user.staff_id}
                      className="hover:bg-blue-50 transition-colors"
                    >
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white font-bold">
                            {user.full_name?.charAt(0) || "?"}
                          </div>
                          <div>
                            <div className="font-semibold text-slate-800">
                              {user.full_name}
                            </div>
                            <div className="text-xs text-slate-500">
                              {user.email}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="p-4 font-mono text-sm text-slate-600">
                        {user.employee_id}
                      </td>
                      <td className="p-4">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-bold ${
                            user.role === "SUPER_ADMIN"
                              ? "bg-purple-100 text-purple-700"
                              : user.role === "DEPT_ADMIN"
                              ? "bg-blue-100 text-blue-700"
                              : "bg-green-100 text-green-700"
                          }`}
                        >
                          {user.role?.replace("_", " ")}
                        </span>
                      </td>
                      <td className="p-4">
                        <span className="px-3 py-1 bg-slate-100 text-slate-700 rounded-lg text-sm font-medium">
                          {user.metadata?.dept || "-"}
                        </span>
                      </td>
                      <td className="p-4 text-sm text-slate-600">
                        {user.metadata?.ward || "-"}
                      </td>
                      <td className="p-4">
                        <span
                          className={`flex items-center gap-1 text-xs font-bold ${
                            user.account_status?.is_active
                              ? "text-green-600"
                              : "text-red-600"
                          }`}
                        >
                          <span
                            className={`w-2 h-2 rounded-full ${
                              user.account_status?.is_active
                                ? "bg-green-500"
                                : "bg-red-500"
                            }`}
                          ></span>
                          {user.account_status?.is_active
                            ? "Active"
                            : "Inactive"}
                        </span>
                      </td>
                      <td className="p-4">
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleViewDetails(user.staff_id)}
                            className="p-2 text-blue-600 hover:bg-blue-100 rounded-lg transition-colors"
                            title="View Details"
                          >
                            <Eye size={18} />
                          </button>
                          <button
                            onClick={() => openJurisdictionModal(user)}
                            className="p-2 text-orange-600 hover:bg-orange-100 rounded-lg transition-colors"
                            title="Update Jurisdiction"
                          >
                            <MapPin size={18} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between p-4 border-t border-slate-200 bg-slate-50">
              <div className="text-sm text-slate-600">
                Showing {(page - 1) * pageSize + 1} to{" "}
                {Math.min(page * pageSize, totalCount)} of {totalCount} users
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-2 border border-slate-200 rounded-lg hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft size={18} />
                </button>
                <span className="px-4 py-2 bg-white border border-slate-200 rounded-lg font-medium">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="p-2 border border-slate-200 rounded-lg hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronRight size={18} />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* CREATE USER MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in-up">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden">
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6 flex justify-between items-center">
              <h3 className="font-bold text-xl flex items-center gap-3">
                <UserPlus size={24} /> Create New Staff User
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="hover:bg-white/20 p-2 rounded-lg transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleCreateUser} className="p-6 space-y-6">
              {createError && (
                <div className="p-4 bg-red-50 border-l-4 border-red-500 rounded-lg text-red-700 flex items-start gap-3 animate-shake">
                  <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
                  <div>{createError}</div>
                </div>
              )}

              {createSuccess && (
                <div className="p-4 bg-green-50 border-l-4 border-green-500 rounded-lg text-green-700 flex items-center gap-3">
                  <CheckCircle size={20} />
                  <div>{createSuccess}</div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">
                    Full Name *
                  </label>
                  <input
                    type="text"
                    value={createForm.full_name}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        full_name: e.target.value,
                      })
                    }
                    placeholder="John Doe"
                    required
                    className="w-full p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">
                    Employee ID *
                  </label>
                  <input
                    type="text"
                    value={createForm.employee_id}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        employee_id: e.target.value,
                      })
                    }
                    placeholder="EMP-2024-001"
                    required
                    className="w-full p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">
                    Email *
                  </label>
                  <input
                    type="email"
                    value={createForm.email}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, email: e.target.value })
                    }
                    placeholder="john@govt.in"
                    required
                    className="w-full p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">
                    Phone Number *
                  </label>
                  <input
                    type="tel"
                    value={createForm.phone_number}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        phone_number: e.target.value,
                      })
                    }
                    placeholder="+91 9876543210"
                    required
                    className="w-full p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">
                    Role *
                  </label>
                  <select
                    value={createForm.role}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, role: e.target.value })
                    }
                    className="w-full p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50"
                  >
                    {ROLES.map((r) => (
                      <option key={r} value={r}>
                        {r.replace("_", " ")}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">
                    Department *
                  </label>
                  <select
                    value={createForm.dept}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, dept: e.target.value })
                    }
                    className="w-full p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50"
                  >
                    {DEPARTMENTS.map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">
                    Ward
                  </label>
                  <input
                    type="text"
                    value={createForm.ward}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, ward: e.target.value })
                    }
                    placeholder="Ward 12"
                    className="w-full p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">
                    Designation
                  </label>
                  <input
                    type="text"
                    value={createForm.designation}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        designation: e.target.value,
                      })
                    }
                    placeholder="Junior Engineer"
                    className="w-full p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50"
                  />
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  disabled={createLoading}
                  className="flex-1 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white py-3 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {createLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                      Creating...
                    </>
                  ) : (
                    <>
                      <UserPlus size={20} /> Create User
                    </>
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-6 py-3 border-2 border-slate-200 text-slate-700 rounded-xl font-bold hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* USER DETAILS MODAL */}
      {showDetailsModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in-up">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">
            <div className="bg-gradient-to-r from-slate-800 to-slate-900 text-white p-6 flex justify-between items-center">
              <h3 className="font-bold text-xl flex items-center gap-3">
                <Eye size={24} /> User Details
              </h3>
              <button
                onClick={() => setShowDetailsModal(false)}
                className="hover:bg-white/20 p-2 rounded-lg transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            <div className="p-6">
              <div className="flex items-center gap-4 mb-6 pb-6 border-b border-slate-200">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                  {selectedUser.full_name?.charAt(0) || "?"}
                </div>
                <div>
                  <h4 className="text-xl font-bold text-slate-800">
                    {selectedUser.full_name}
                  </h4>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-bold ${
                      selectedUser.role === "SUPER_ADMIN"
                        ? "bg-purple-100 text-purple-700"
                        : selectedUser.role === "DEPT_ADMIN"
                        ? "bg-blue-100 text-blue-700"
                        : "bg-green-100 text-green-700"
                    }`}
                  >
                    {selectedUser.role?.replace("_", " ")}
                  </span>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                  <Mail className="text-slate-400" size={20} />
                  <div>
                    <div className="text-xs text-slate-500 uppercase font-bold">
                      Email
                    </div>
                    <div className="text-slate-800">{selectedUser.email}</div>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                  <Phone className="text-slate-400" size={20} />
                  <div>
                    <div className="text-xs text-slate-500 uppercase font-bold">
                      Phone
                    </div>
                    <div className="text-slate-800">
                      {selectedUser.phone_number}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                  <Briefcase className="text-slate-400" size={20} />
                  <div>
                    <div className="text-xs text-slate-500 uppercase font-bold">
                      Employee ID
                    </div>
                    <div className="text-slate-800 font-mono">
                      {selectedUser.employee_id}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <div className="text-xs text-slate-500 uppercase font-bold">
                      Department
                    </div>
                    <div className="text-slate-800">
                      {selectedUser.metadata?.dept || "-"}
                    </div>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <div className="text-xs text-slate-500 uppercase font-bold">
                      Ward
                    </div>
                    <div className="text-slate-800">
                      {selectedUser.metadata?.ward || "-"}
                    </div>
                  </div>
                </div>

                <div className="p-3 bg-slate-50 rounded-lg">
                  <div className="text-xs text-slate-500 uppercase font-bold">
                    Designation
                  </div>
                  <div className="text-slate-800">
                    {selectedUser.metadata?.designation || "-"}
                  </div>
                </div>

                <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div>
                    <div className="text-xs text-slate-500 uppercase font-bold">
                      Account Status
                    </div>
                    <div
                      className={`font-bold ${
                        selectedUser.account_status?.is_active
                          ? "text-green-600"
                          : "text-red-600"
                      }`}
                    >
                      {selectedUser.account_status?.is_active
                        ? "Active"
                        : "Inactive"}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-slate-500 uppercase font-bold">
                      Created
                    </div>
                    <div className="text-slate-600 text-sm">
                      {selectedUser.created_at
                        ? new Date(selectedUser.created_at).toLocaleDateString()
                        : "-"}
                    </div>
                  </div>
                </div>
              </div>

              <button
                onClick={() => setShowDetailsModal(false)}
                className="w-full mt-6 py-3 bg-slate-800 hover:bg-slate-900 text-white rounded-xl font-bold transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* UPDATE JURISDICTION MODAL */}
      {showJurisdictionModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in-up">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
            <div className="bg-gradient-to-r from-orange-600 to-orange-700 text-white p-6 flex justify-between items-center">
              <h3 className="font-bold text-xl flex items-center gap-3">
                <MapPin size={24} /> Update Jurisdiction
              </h3>
              <button
                onClick={() => setShowJurisdictionModal(false)}
                className="hover:bg-white/20 p-2 rounded-lg transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleUpdateJurisdiction} className="p-6 space-y-6">
              {jurisdictionError && (
                <div className="p-4 bg-red-50 border-l-4 border-red-500 rounded-lg text-red-700 flex items-start gap-3 animate-shake">
                  <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
                  <div>{jurisdictionError}</div>
                </div>
              )}

              <div className="p-4 bg-slate-50 rounded-lg">
                <div className="text-sm text-slate-500">
                  Updating jurisdiction for:
                </div>
                <div className="font-bold text-slate-800">
                  {selectedUser.full_name}
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  Staff ID: {selectedUser.staff_id}
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-2">
                  New Ward *
                </label>
                <input
                  type="text"
                  value={jurisdictionForm.new_ward}
                  onChange={(e) =>
                    setJurisdictionForm({
                      ...jurisdictionForm,
                      new_ward: e.target.value,
                    })
                  }
                  placeholder="Ward 15"
                  required
                  className="w-full p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 bg-slate-50"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-2">
                  New Department (Optional)
                </label>
                <select
                  value={jurisdictionForm.new_dept}
                  onChange={(e) =>
                    setJurisdictionForm({
                      ...jurisdictionForm,
                      new_dept: e.target.value,
                    })
                  }
                  className="w-full p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 bg-slate-50"
                >
                  <option value="">Keep Current Department</option>
                  {DEPARTMENTS.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={jurisdictionLoading}
                  className="flex-1 bg-gradient-to-r from-orange-600 to-orange-700 hover:from-orange-700 hover:to-orange-800 text-white py-3 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {jurisdictionLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                      Updating...
                    </>
                  ) : (
                    <>
                      <MapPin size={20} /> Update Jurisdiction
                    </>
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => setShowJurisdictionModal(false)}
                  className="px-6 py-3 border-2 border-slate-200 text-slate-700 rounded-xl font-bold hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CONFLICTS MODAL */}
      {showConflictsModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-3xl bg-white rounded-2xl shadow-xl p-4 overflow-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold">
                Conflicts ({conflictsTotal})
              </h3>
              <button
                onClick={() => setShowConflictsModal(false)}
                className="text-slate-600"
              >
                Close
              </button>
            </div>

            {conflictsLoading ? (
              <div className="p-6 text-center">Loading conflicts...</div>
            ) : conflicts.length === 0 ? (
              <div className="p-6 text-center text-slate-500">
                No conflicts found.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="text-xs text-slate-500 uppercase">
                    <tr>
                      <th className="p-2">Feedback ID</th>
                      <th className="p-2">Form ID</th>
                      <th className="p-2">Citizen</th>
                      <th className="p-2">Officer</th>
                      <th className="p-2">Escalated</th>
                      <th className="p-2">Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {conflicts.map((c) => (
                      <tr key={c.feedback_id || c._id} className="border-t">
                        <td className="p-2 text-sm">{c.feedback_id}</td>
                        <td className="p-2 text-sm">{c.form_id}</td>
                        <td className="p-2 text-sm">{c.citizen_id}</td>
                        <td className="p-2 text-sm">{c.officer_id}</td>
                        <td className="p-2 text-sm">
                          {c.escalated ? "Yes" : "No"}
                        </td>
                        <td className="p-2 text-sm">
                          {c.created_at
                            ? new Date(c.created_at).toLocaleString()
                            : "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* FEEDBACKS MODAL */}
      {showFeedbacksModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-4xl bg-white rounded-2xl shadow-xl p-4 overflow-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold">
                All Feedbacks ({feedbacksTotal})
              </h3>
              <button
                onClick={() => setShowFeedbacksModal(false)}
                className="text-slate-600"
              >
                Close
              </button>
            </div>

            {feedbacksLoading ? (
              <div className="p-6 text-center">Loading feedbacks...</div>
            ) : feedbacks.length === 0 ? (
              <div className="p-6 text-center text-slate-500">
                No feedbacks available.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="text-xs text-slate-500 uppercase">
                    <tr>
                      <th className="p-2">Feedback ID</th>
                      <th className="p-2">Form ID</th>
                      <th className="p-2">Citizen</th>
                      <th className="p-2">Officer</th>
                      <th className="p-2">Conflict</th>
                      <th className="p-2">Escalated</th>
                      <th className="p-2">Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {feedbacks.map((f) => (
                      <tr key={f.feedback_id || f._id} className="border-t">
                        <td className="p-2 text-sm">{f.feedback_id}</td>
                        <td className="p-2 text-sm">{f.form_id}</td>
                        <td className="p-2 text-sm">{f.citizen_id}</td>
                        <td className="p-2 text-sm">{f.officer_id}</td>
                        <td className="p-2 text-sm">
                          {f.conflict_detected ? "Yes" : "No"}
                        </td>
                        <td className="p-2 text-sm">
                          {f.escalated ? "Yes" : "No"}
                        </td>
                        <td className="p-2 text-sm">
                          {f.created_at
                            ? new Date(f.created_at).toLocaleString()
                            : "-"}
                        </td>
                        <td className="p-2 text-sm">
                          <button
                            onClick={() =>
                              viewFeedbackDetail(f.feedback_id || f._id)
                            }
                            className="px-3 py-1 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                          >
                            View
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* FEEDBACK DETAIL MODAL (portal to body so it always appears on top) */}
      {showFeedbackDetailModal &&
        ReactDOM.createPortal(
          <div className="fixed inset-0 bg-black/50 z-[9999] flex items-center justify-center p-4">
            <div className="w-full max-w-2xl bg-white rounded-2xl shadow-xl p-6 overflow-auto z-[10000]">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold">Feedback Details</h3>
                  <div className="text-sm text-slate-500">
                    {feedbackDetail?.feedback_id || "Loading..."}
                  </div>
                </div>
                <button
                  onClick={() => {
                    setShowFeedbackDetailModal(false);
                    setFeedbackDetail(null);
                  }}
                  className="text-slate-600"
                >
                  Close
                </button>
              </div>

              {feedbackDetailLoading ? (
                <div className="p-6 text-center">Loading...</div>
              ) : feedbackDetail?.error ? (
                <div className="p-4 text-red-600">{feedbackDetail.error}</div>
              ) : feedbackDetail ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    <div className="text-sm">Overall:</div>
                    <div className="font-semibold">
                      {feedbackDetail.ratings?.overall || "-"}
                      /5
                    </div>
                    <div className="ml-4 text-sm">Speed:</div>
                    <div className="font-semibold">
                      {feedbackDetail.ratings?.speed || "-"}
                      /5
                    </div>
                    <div className="ml-4 text-sm">Quality:</div>
                    <div className="font-semibold">
                      {feedbackDetail.ratings?.quality || "-"}
                      /5
                    </div>

                    {/* Sentiment display */}
                    <div className="ml-6 text-sm">Sentiment:</div>
                    <div className="font-semibold text-slate-800">
                      {feedbackDetail.sentiment?.label
                        ? feedbackDetail.sentiment.label
                            .charAt(0)
                            .toUpperCase() +
                          feedbackDetail.sentiment.label.slice(1)
                        : "-"}
                      {feedbackDetail.sentiment?.score != null && (
                        <span className="ml-2 text-xs text-slate-500">
                          (
                          {Math.round(
                            (feedbackDetail.sentiment.score || 0) * 100
                          )}
                          % negative)
                        </span>
                      )}
                    </div>
                  </div>

                  {/* show explanation if present */}
                  {feedbackDetail.sentiment?.explanation && (
                    <div>
                      <div className="text-xs text-slate-500 uppercase">
                        Sentiment Note
                      </div>
                      <div className="text-slate-800">
                        {feedbackDetail.sentiment.explanation}
                      </div>
                    </div>
                  )}

                  <div>
                    <div className="text-xs text-slate-500 uppercase">
                      Comment
                    </div>
                    <div className="text-slate-800">
                      {feedbackDetail.user_comment || "—"}
                    </div>
                  </div>
                  <div className="flex gap-4">
                    <div>
                      <div className="text-xs text-slate-500 uppercase">
                        Conflict
                      </div>
                      <div className="font-semibold">
                        {feedbackDetail.conflict_detected ? "Yes" : "No"}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500 uppercase">
                        Escalated
                      </div>
                      <div className="font-semibold">
                        {feedbackDetail.escalated ? "Yes" : "No"}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500 uppercase">
                        Created
                      </div>
                      <div className="font-semibold">
                        {feedbackDetail.created_at
                          ? new Date(feedbackDetail.created_at).toLocaleString()
                          : "-"}
                      </div>
                    </div>
                  </div>
                  {feedbackDetail.citizen_evidence_path && (
                    <div>
                      <div className="text-xs text-slate-500 uppercase mb-2">
                        Evidence
                      </div>
                      <a
                        href={buildImageUrl(
                          feedbackDetail.citizen_evidence_path
                        )}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <img
                          src={buildImageUrl(
                            feedbackDetail.citizen_evidence_path
                          )}
                          alt="evidence"
                          className="w-48 h-32 object-cover rounded-md border"
                        />
                      </a>
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          </div>,
          document.body
        )}
    </div>
  );
}
