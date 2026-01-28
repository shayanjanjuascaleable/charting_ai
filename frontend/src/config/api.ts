/**
 * API configuration for frontend
 * Uses NEXT_PUBLIC_API_BASE_URL for production, falls back to relative paths for same-origin
 */
const getApiBaseUrl = (): string => {
  // In production, use environment variable if set
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  
  // For Vite, also check NEXT_PUBLIC_API_BASE_URL (for compatibility)
  if (import.meta.env.NEXT_PUBLIC_API_BASE_URL) {
    return import.meta.env.NEXT_PUBLIC_API_BASE_URL;
  }
  
  // Default: use relative path (same origin) - works for production when frontend is served by Flask
  return '';
};

export const API_BASE_URL = getApiBaseUrl();

/**
 * Get full API URL for an endpoint
 */
export const getApiUrl = (endpoint: string): string => {
  // Remove leading slash if present to avoid double slashes
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  
  if (API_BASE_URL) {
    // Ensure no double slashes
    const base = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
    return `${base}/${cleanEndpoint}`;
  }
  
  // Relative path (same origin)
  return `/${cleanEndpoint}`;
};

