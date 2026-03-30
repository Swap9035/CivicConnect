// API utility functions for backend integration

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000';

/**
 * User Signup
 * @param {Object} userData - User registration data
 * @param {string} userData.full_name - Full name
 * @param {string} userData.email - Email address
 * @param {string} userData.mobile_number - Mobile number
 * @param {string} userData.password - Password
 * @param {string} userData.residential_address - Residential address
 * @param {string} userData.language_preference - Language preference
 * @returns {Promise<Object>} Response data
 */
export async function signupUser(userData) {
  try {
    const response = await fetch(`${API_BASE_URL}/users/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        full_name: userData.full_name,
        mobile_number: userData.mobile_number,
        password: userData.password,
        residential_address: userData.residential_address,
        email: userData.email,
        language_preference: userData.language_preference
      })
    });

    const data = await response.json();

    if (!response.ok) {
      // Handle 422 validation errors
      if (response.status === 422) {
        const errorMsg = data.detail?.map(err => err.msg).join(', ') || 'Validation error. Please check your inputs.';
        throw new Error(errorMsg);
      }
      throw new Error(data.message || 'Signup failed');
    }

    return data;
  } catch (error) {
    console.error('Signup error:', error);
    throw error;
  }
}

/**
 * User Login
 * @param {Object} credentials - Login credentials
 * @param {string} credentials.mobile_number - Mobile number
 * @param {string} credentials.password - Password
 * @returns {Promise<Object>} Response data with access_token
 */
export async function loginUser(credentials) {
  try {
    const response = await fetch(`${API_BASE_URL}/users/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        mobile_number: credentials.mobile_number,
        password: credentials.password
      })
    });

    const data = await response.json();

    if (!response.ok) {
      if (response.status === 422) {
        const errorMsg = data.detail?.map(err => err.msg).join(', ') || 'Invalid credentials';
        throw new Error(errorMsg);
      }
      if (response.status === 401) {
        throw new Error('Invalid mobile number or password');
      }
      throw new Error(data.message || 'Login failed');
    }

    // Store access token
    if (data.access_token) {
      localStorage.setItem('authToken', data.access_token);
      localStorage.setItem('tokenType', data.token_type);
    }

    return data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}

/**
 * Get Current User
 * @returns {Promise<Object>} Current user data
 */
export async function getCurrentUser() {
  const token = localStorage.getItem('authToken');
  const tokenType = localStorage.getItem('tokenType') || 'bearer';

  if (!token) {
    throw new Error('No authentication token found');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/users/me`, {
      method: 'GET',
      headers: {
        'Authorization': `${tokenType} ${token}`
      }
    });

    const data = await response.json();

    if (!response.ok) {
      if (response.status === 401) {
        // Token expired or invalid
        logoutUser();
        throw new Error('Session expired. Please login again.');
      }
      throw new Error(data.message || 'Failed to fetch user data');
    }

    return data;
  } catch (error) {
    console.error('Get current user error:', error);
    throw error;
  }
}

/**
 * Submit a new grievance
 * @param {Object} grievanceData - Grievance details
 * @returns {Promise<Object>} Created grievance data
 */
export async function submitGrievance(grievanceData) {
  const token = localStorage.getItem('authToken');
  const tokenType = localStorage.getItem('tokenType') || 'bearer';
  
  try {
    const response = await fetch(`${API_BASE_URL}/grievances`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `${tokenType} ${token}`
      },
      body: JSON.stringify(grievanceData)
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Failed to submit grievance');
    }

    return data;
  } catch (error) {
    console.error('Submit grievance error:', error);
    throw error;
  }
}

/**
 * Get user's grievances
 * @param {string} status - Filter by status (optional)
 * @returns {Promise<Array>} List of grievances
 */
export async function getGrievances(status = null) {
  const token = localStorage.getItem('authToken');
  const tokenType = localStorage.getItem('tokenType') || 'bearer';
  
  const url = status 
    ? `${API_BASE_URL}/grievances?status=${status}`
    : `${API_BASE_URL}/grievances`;

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `${tokenType} ${token}`
      }
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Failed to fetch grievances');
    }

    return data;
  } catch (error) {
    console.error('Fetch grievances error:', error);
    throw error;
  }
}

/**
 * Get specific grievance details
 * @param {string} grievanceId - Grievance ID
 * @returns {Promise<Object>} Grievance details
 */
export async function getGrievanceById(grievanceId) {
  const token = localStorage.getItem('authToken');
  const tokenType = localStorage.getItem('tokenType') || 'bearer';

  try {
    const response = await fetch(`${API_BASE_URL}/grievances/${grievanceId}`, {
      method: 'GET',
      headers: {
        'Authorization': `${tokenType} ${token}`
      }
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Failed to fetch grievance details');
    }

    return data;
  } catch (error) {
    console.error('Fetch grievance error:', error);
    throw error;
  }
}

/**
 * Logout user
 */
export function logoutUser() {
  localStorage.removeItem('authToken');
  localStorage.removeItem('tokenType');
}

/**
 * Check if user is authenticated
 * @returns {boolean}
 */
export function isAuthenticated() {
  return !!localStorage.getItem('authToken');
}

/**
 * Get authentication token
 * @returns {string|null}
 */
export function getAuthToken() {
  return localStorage.getItem('authToken');
}
