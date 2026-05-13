import { setBaseUrl } from "@workspace/api-client-react";

// All API calls use relative paths (/api/...).
// In development, Vite proxies /api → FastAPI on port 8000.
// In production, the Replit proxy routes /api → the API server.
// Passing null keeps all fetch calls relative to the current origin.
setBaseUrl(null);

export { setBaseUrl };
