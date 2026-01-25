import React, { useState } from "react";
import LoginForm from "./LoginForm";
import RegisterForm from "./RegisterForm";

interface AuthPageProps {
  onSuccess: () => void;
}

type AuthMode = "login" | "register";

const AuthPage: React.FC<AuthPageProps> = ({ onSuccess }) => {
  const [mode, setMode] = useState<AuthMode>("login");

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <h1>Notion Relation View</h1>
          <p>Visualize your Notion page relationships</p>
        </div>

        {mode === "login" ? (
          <LoginForm
            onSuccess={onSuccess}
            onSwitchToRegister={() => setMode("register")}
          />
        ) : (
          <RegisterForm
            onSuccess={onSuccess}
            onSwitchToLogin={() => setMode("login")}
          />
        )}
      </div>
    </div>
  );
};

export default AuthPage;
