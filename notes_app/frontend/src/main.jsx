import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./index.css";
import { NavigationProvider } from "./provider/NavigationContext.jsx";
import { AuthProvider } from "./provider/AuthContext.jsx";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <NavigationProvider>
      <AuthProvider>
        <App />
      </AuthProvider>
    </NavigationProvider>
  </React.StrictMode>
);
