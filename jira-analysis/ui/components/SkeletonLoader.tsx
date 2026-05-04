import React from 'react';

interface SkeletonLoaderProps {
  type?: 'text' | 'card' | 'analysis';
  lines?: number;
}

export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  type = 'text',
  lines = 3
}) => {
  if (type === 'card') {
    return (
      <div className="skeleton-card">
        <div className="skeleton-header">
          <div className="skeleton skeleton-avatar" />
          <div className="skeleton-lines">
            <div className="skeleton skeleton-text large" style={{ width: '60%' }} />
            <div className="skeleton skeleton-text small" style={{ width: '40%' }} />
          </div>
        </div>
        <div className="skeleton skeleton-text" style={{ width: '100%' }} />
        <div className="skeleton skeleton-text" style={{ width: '90%' }} />
        <div className="skeleton skeleton-text" style={{ width: '75%' }} />
      </div>
    );
  }

  if (type === 'analysis') {
    return (
      <div className="analysis-result-card">
        <div className="skeleton-header">
          <div className="skeleton skeleton-avatar" />
          <div className="skeleton-lines">
            <div className="skeleton skeleton-text large" style={{ width: '50%' }} />
            <div className="skeleton skeleton-text small" style={{ width: '30%' }} />
          </div>
        </div>

        <div style={{ marginTop: 'var(--spacing-lg)' }}>
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="skeleton skeleton-text" style={{
              width: `${Math.random() * 30 + 70}%`,
              marginBottom: 'var(--spacing-sm)'
            }} />
          ))}
        </div>

        <div style={{ marginTop: 'var(--spacing-xl)' }}>
          <div className="skeleton skeleton-text large" style={{ width: '40%', marginBottom: 'var(--spacing-md)' }} />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 'var(--spacing-md)' }}>
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="skeleton" style={{ height: '120px' }} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Default: text lines
  return (
    <div>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="skeleton skeleton-text"
          style={{
            width: i === lines - 1 ? '60%' : '100%',
            marginBottom: 'var(--spacing-sm)'
          }}
        />
      ))}
    </div>
  );
};

export const TypingIndicator: React.FC = () => (
  <span className="typing-indicator">
    <span className="typing-dot" />
    <span className="typing-dot" />
    <span className="typing-dot" />
  </span>
);
