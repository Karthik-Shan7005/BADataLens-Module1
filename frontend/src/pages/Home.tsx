import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProjects } from '../api';
import type { Project } from '../types';

export default function Home() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    getProjects()
      .then(data => {
        setProjects(data);
        if (data.length === 1) {
          navigate(`/project/${data[0].id}`, { replace: true });
        }
      })
      .catch(() =>
        setError(
          'Could not connect to the DataLens API. Make sure the backend is running on port 8000.',
        ),
      )
      .finally(() => setLoading(false));
  }, [navigate]);

  return (
    <div className="home-layout">
      <header className="app-header">
        <div className="header-left">
          <img src="/BA_Logo_white_text.png" alt="Borderless Access" className="header-company-logo" />
          <div className="header-logo">
            <span className="logo-dot">◉</span>
            <span className="logo-text">DataLens</span>
          </div>
        </div>
        <div className="header-right">
          <span className="header-subtitle">AI Survey Insights Platform</span>
          <span className="header-powered">Powered by Borderless Access</span>
        </div>
      </header>

      <main className="home-main">
        <div className="home-hero">
          <h1>Survey Insights, Powered by AI</h1>
          <p>
            Ask natural language questions about your survey data and get instant insights
            with weighted statistics and auto-generated charts.
          </p>
        </div>

        {loading && <div className="loading-state">Connecting to API…</div>}
        {error && <div className="error-state">{error}</div>}

        {!loading && !error && projects.length === 0 && (
          <div className="empty-state">
            No projects found. Upload an SPSS file and datamap via POST /projects/ to get started.
          </div>
        )}

        {!loading && !error && projects.length > 1 && (
          <div className="project-grid">
            {projects.map(p => (
              <button
                key={p.id}
                className="project-card"
                onClick={() => navigate(`/project/${p.id}`)}
              >
                <div className="project-card-icon">📊</div>
                <div className="project-card-name">{p.name}</div>
                <div className="project-card-meta">
                  Access: {p.expiry_months} months
                </div>
              </button>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
