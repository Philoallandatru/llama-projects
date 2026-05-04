import React from 'react';

interface ErrorMessageProps {
  title?: string;
  message: string;
  details?: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  title = 'Analysis Failed',
  message,
  details,
  onRetry,
  onDismiss
}) => {
  return (
    <div className="error-container">
      <div className="error-header">
        <span className="error-icon">⚠️</span>
        <h3 className="error-title">{title}</h3>
      </div>

      <p className="error-message">{message}</p>

      {details && (
        <div className="error-details">
          <strong>Details:</strong>
          <pre style={{ margin: '0.5rem 0 0 0', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {details}
          </pre>
        </div>
      )}

      <div className="error-actions">
        {onRetry && (
          <button className="error-button primary" onClick={onRetry}>
            🔄 Retry Analysis
          </button>
        )}
        {onDismiss && (
          <button className="error-button secondary" onClick={onDismiss}>
            Dismiss
          </button>
        )}
      </div>
    </div>
  );
};

interface SuccessMessageProps {
  title?: string;
  message?: string;
  children?: React.ReactNode;
}

export const SuccessMessage: React.FC<SuccessMessageProps> = ({
  title = 'Analysis Complete',
  message,
  children
}) => {
  return (
    <div className="success-container">
      <div className="success-header">
        <span className="success-icon">✅</span>
        <h3 className="success-title">{title}</h3>
      </div>
      {message && <p style={{ marginTop: 'var(--spacing-md)', color: 'var(--slate-700)' }}>{message}</p>}
      {children}
    </div>
  );
};

interface WarningMessageProps {
  title?: string;
  message: string;
}

export const WarningMessage: React.FC<WarningMessageProps> = ({
  title = 'Warning',
  message
}) => {
  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.05) 0%, rgba(245, 158, 11, 0.1) 100%)',
      border: '2px solid var(--warning)',
      borderRadius: 'var(--radius-xl)',
      padding: 'var(--spacing-xl)',
      marginBottom: 'var(--spacing-lg)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)' }}>
        <span style={{ fontSize: '2rem' }}>⚡</span>
        <div>
          <h3 style={{ margin: 0, color: 'var(--warning)', fontSize: '1.25rem', fontWeight: 700 }}>
            {title}
          </h3>
          <p style={{ margin: '0.5rem 0 0 0', color: 'var(--slate-700)' }}>{message}</p>
        </div>
      </div>
    </div>
  );
};
