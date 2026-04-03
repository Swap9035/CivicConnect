import React, { createContext, useContext, useState, useEffect } from "react";
import { authAPI } from "../services/api";

const AuthContext = createContext(null);

// ──────────────────────────────────────────────
// DUMMY TEST CREDENTIALS (bypass backend entirely)
// ──────────────────────────────────────────────
const DUMMY_ACCOUNTS = {
  // Citizen — use mobile_number to login
  citizen: {
    identifier: "9876543210",
    password: "Password@123",
    token: "dummy-citizen-token-xyz",
    userType: "citizen",
    profile: {
      id: "c_dummy_001",
      full_name: "Citizen Test",
      mobile_number: "9876543210",
      residential_address: "123 Main St, Nagpur",
      email: "citizen.test@example.com",
      language_preference: "English",
    },
  },
  // Admin — use email to login
  admin: {
    identifier: "superadmin@gov.in",
    password: "TempAdmin@123",
    token: "dummy-admin-token-xyz",
    userType: "staff",
    profile: {
      staff_id: "SUPER_ADMIN_001",
      full_name: "System SuperAdmin",
      employee_id: "SUPER_ADMIN_001",
      email: "superadmin@gov.in",
      phone_number: "+911234567890",
      role: "SUPER_ADMIN",
      metadata: {
        dept: "ELECTRICITY",
        ward: "System",
        designation: "System Administrator",
      },
      account_status: { is_active: true, is_first_login: false },
    },
  },
  // Officer — use email to login
  officer: {
    identifier: "rahul.sharma@gov.in",
    password: "Officer@123",
    token: "dummy-officer-token-xyz",
    userType: "staff",
    profile: {
      staff_id: "STF_OFF_001",
      full_name: "Rahul Sharma",
      employee_id: "ELEC_OFF_001",
      email: "rahul.sharma@gov.in",
      phone_number: "+911234567892",
      role: "NODAL_OFFICER",
      metadata: {
        dept: "ELECTRICITY",
        ward: "Shanti Nagar",
        designation: "Junior Engineer",
      },
      account_status: { is_active: true, is_first_login: false },
    },
  },
};

/** Check if a login attempt matches any dummy account */
function matchDummy(identifier, password, isStaff) {
  for (const account of Object.values(DUMMY_ACCOUNTS)) {
    if (
      account.identifier === identifier &&
      account.password === password &&
      (isStaff ? account.userType === "staff" : account.userType === "citizen")
    ) {
      return account;
    }
  }
  return null;
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem("access_token"));
  const [userType, setUserType] = useState(
    localStorage.getItem("user_type") || "citizen"
  ); // citizen or staff

  // Check if user is logged in on mount
  useEffect(() => {
    const checkAuth = async () => {
      const savedToken = localStorage.getItem("access_token");
      const savedUserType = localStorage.getItem("user_type") || "citizen";
      if (savedToken) {
        // If the token is one of our dummy tokens, restore from DUMMY_ACCOUNTS
        const dummyMatch = Object.values(DUMMY_ACCOUNTS).find(
          (a) => a.token === savedToken
        );
        if (dummyMatch) {
          setUser(dummyMatch.profile);
          setUserType(dummyMatch.userType);
          setLoading(false);
          return;
        }

        try {
          let response;
          if (savedUserType === "staff") {
            response = await authAPI.getAdminProfile();
          } else {
            response = await authAPI.getCurrentUser();
          }
          setUser(response.data);
          setUserType(savedUserType);
        } catch (error) {
          console.error("Auth check failed:", error);
          localStorage.removeItem("access_token");
          localStorage.removeItem("user_type");
          setToken(null);
          setUserType("citizen");
        }
      }
      setLoading(false);
    };
    checkAuth();
  }, []);

  const login = async (identifier, password, isStaff = false) => {
    // ── Try dummy credentials first ──
    const dummy = matchDummy(identifier, password, isStaff);
    if (dummy) {
      localStorage.setItem("access_token", dummy.token);
      localStorage.setItem("user_type", dummy.userType);
      setToken(dummy.token);
      setUser(dummy.profile);
      setUserType(dummy.userType);
      return { success: true };
    }

    // ── Fall back to real API ──
    try {
      let response;

      if (isStaff) {
        // For staff/admin, use the superuser auth endpoint
        response = await authAPI.adminLogin({ email: identifier, password });

        // Admin login returns user data in response, not a separate call needed
        const { access_token, user } = response.data;
        localStorage.setItem("access_token", access_token);
        localStorage.setItem("user_type", "staff");
        setToken(access_token);
        setUser(user);
        setUserType("staff");
      } else {
        // For citizens, use mobile_number
        response = await authAPI.login({ mobile_number: identifier, password });
        const { access_token } = response.data;

        localStorage.setItem("access_token", access_token);
        localStorage.setItem("user_type", "citizen");
        setToken(access_token);
        setUserType("citizen");

        // Fetch user data for citizens
        const userResponse = await authAPI.getCurrentUser();
        setUser(userResponse.data);
      }

      return { success: true };
    } catch (error) {
      console.error("Login failed:", error);

      // Extract error message properly
      let errorMessage = "Invalid credentials";
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        // Handle array of validation errors
        if (Array.isArray(detail)) {
          errorMessage = detail.map((err) => err.msg || err.message).join(", ");
        } else if (typeof detail === "string") {
          errorMessage = detail;
        } else if (detail.msg) {
          errorMessage = detail.msg;
        }
      }

      return {
        success: false,
        error: errorMessage,
      };
    }
  };

  const signup = async (userData) => {
    try {
      await authAPI.signup(userData);
      // After signup, automatically login
      return await login(userData.mobile_number, userData.password);
    } catch (error) {
      console.error("Signup failed:", error);
      return {
        success: false,
        error: error.response?.data?.detail || "Signup failed",
      };
    }
  };

  const logout = async () => {
    try {
      // Call backend logout if user is staff
      if (userType === "staff") {
        await authAPI.adminLogout();
      }
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user_type");
      setToken(null);
      setUser(null);
      setUserType("citizen");
    }
  };

  const changePassword = async (currentPassword, newPassword) => {
    try {
      if (userType === "staff") {
        await authAPI.changeAdminPassword({
          current_password: currentPassword,
          new_password: newPassword,
        });
        return { success: true, message: "Password changed successfully" };
      } else {
        return {
          success: false,
          error: "Password change not available for citizens yet",
        };
      }
    } catch (error) {
      console.error("Change password failed:", error);
      let errorMessage = "Failed to change password";
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        if (Array.isArray(detail)) {
          errorMessage = detail.map((err) => err.msg || err.message).join(", ");
        } else if (typeof detail === "string") {
          errorMessage = detail;
        }
      }
      return { success: false, error: errorMessage };
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        userType,
        login,
        signup,
        logout,
        changePassword,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};
