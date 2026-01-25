import React, { useState } from "react";
import { Routes, Route, useNavigate } from "react-router-dom";
import { AuthProvider } from "./components/AuthProvider";
import AuthPage from "./components/AuthPage";
import ViewManager from "./components/ViewManager";
import ViewPage from "./components/ViewPage";
import { View } from "./types";

function App() {
  const navigate = useNavigate();
  const [currentViewId, setCurrentViewId] = useState<string | undefined>();

  const handleViewSelect = (view: View) => {
    setCurrentViewId(view.id);
    navigate(`/view/${view.id}`);
  };

  return (
    <AuthProvider>
      <div className="app">
        <header className="app-header">
          <h1>Notion Relation View</h1>
        </header>
        <Routes>
          <Route path="/" element={<AuthPage />} />
          <Route
            path="/views"
            element={
              <ViewManager
                onViewSelect={handleViewSelect}
                currentViewId={currentViewId}
              />
            }
          />
          <Route path="/view/:viewId" element={<ViewPage />} />
        </Routes>
      </div>
    </AuthProvider>
  );
}

export default App;
