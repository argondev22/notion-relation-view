import { useState, useEffect } from "react";
import { Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./components/AuthProvider";
import AuthPage from "./components/AuthPage";
import ViewManager from "./components/ViewManager";
import ViewPage from "./components/ViewPage";
import { View } from "./types";

function AppContent() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, loading } = useAuth();
  const [currentViewId, setCurrentViewId] = useState<string | undefined>();

  // Redirect to auth page if not logged in
  useEffect(() => {
    if (!loading && !user && location.pathname !== "/") {
      navigate("/");
    }
  }, [user, loading, location.pathname, navigate]);

  const handleViewSelect = (view: View) => {
    setCurrentViewId(view.id);
    navigate(`/view/${view.id}`);
  };

  const handleAuthSuccess = () => {
    navigate("/views");
  };

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="app">
        <div className="loading-container">
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Notion Relation View</h1>
        {user && (
          <div className="user-info">
            <span>{user.email}</span>
          </div>
        )}
      </header>
      <Routes>
        <Route path="/" element={<AuthPage onSuccess={handleAuthSuccess} />} />
        <Route
          path="/views"
          element={
            user ? (
              <ViewManager
                onViewSelect={handleViewSelect}
                currentViewId={currentViewId}
              />
            ) : (
              <div>Please log in</div>
            )
          }
        />
        <Route
          path="/view/:viewId"
          element={user ? <ViewPage /> : <div>Please log in</div>}
        />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
