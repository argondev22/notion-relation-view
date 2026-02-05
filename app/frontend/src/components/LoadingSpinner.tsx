import React from "react";

interface LoadingSpinnerProps {
  message?: string;
  progress?: number;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = "Loading...",
  progress,
}) => {
  return (
    <div className="loading-spinner-container">
      <div className="spinner"></div>
      <p className="loading-message">{message}</p>
      {progress !== undefined && progress >= 0 && progress <= 1 && (
        <div className="progress-bar-container">
          <div
            className="progress-bar"
            style={{ width: `${progress * 100}%` }}
            role="progressbar"
            aria-valuenow={Math.round(progress * 100)}
            aria-valuemin={0}
            aria-valuemax={100}
          />
          <span className="progress-text">{Math.round(progress * 100)}%</span>
        </div>
      )}
    </div>
  );
};

export default LoadingSpinner;
