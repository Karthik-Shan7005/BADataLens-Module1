import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getProject, getProjects, queryProject, getHistory } from '../api';
import ChatWindow from '../components/ChatWindow';
import type { Message, Project, ProjectDetail } from '../types';

export default function ProjectView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const projectId = Number(id);

  const [projects, setProjects] = useState<Project[]>([]);
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getProjects().then(setProjects).catch(() => {});
  }, []);

  useEffect(() => {
    if (!projectId) return;
    setMessages([]);
    setError(null);
    setProject(null);

    getProject(projectId).then(setProject).catch(() => {
      setError('Could not load project. Check the backend is running.');
    });

    getHistory(projectId)
      .then(history => {
        const msgs: Message[] = [];
        [...history].reverse().forEach(h => {
          msgs.push({
            id: `h-user-${h.id}`,
            role: 'user',
            content: h.question,
            timestamp: new Date(h.created_at),
          });
          msgs.push({
            id: `h-ai-${h.id}`,
            role: 'assistant',
            content: h.response,
            chart: h.chart,
            timestamp: new Date(h.created_at),
          });
        });
        setMessages(msgs);
      })
      .catch(() => {});
  }, [projectId]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput('');
    setLoading(true);
    setError(null);

    setMessages(prev => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        role: 'user',
        content: question,
        timestamp: new Date(),
      },
    ]);

    try {
      const result = await queryProject(projectId, question);
      setMessages(prev => [
        ...prev,
        {
          id: `ai-${Date.now()}`,
          role: 'assistant',
          content: result.response,
          chart: result.chart,
          timestamp: new Date(),
        },
      ]);
    } catch (e: unknown) {
      let detail = 'Query failed. Please try again.';
      if (e && typeof e === 'object' && 'response' in e) {
        const err = e as { response?: { data?: { detail?: string } } };
        detail = err.response?.data?.detail ?? detail;
      }
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <img src="/BA_Logo_white_text.png" alt="Borderless Access" className="sidebar-company-logo" />
          <div className="sidebar-brand">
            <span className="logo-dot">◉</span>
            <span className="logo-text">DataLens</span>
          </div>
        </div>

        <div className="sidebar-section">
          <span className="sidebar-label">Projects</span>
          {projects.map(p => (
            <button
              key={p.id}
              className={`sidebar-project${p.id === projectId ? ' sidebar-project--active' : ''}`}
              onClick={() => navigate(`/project/${p.id}`)}
            >
              <span className="sidebar-project-icon">📊</span>
              {p.name}
            </button>
          ))}
        </div>

        {project && (
          <div className="sidebar-meta">
            <span className="sidebar-label">Dataset</span>
            <div className="meta-row">
              <span className="meta-key">Questions</span>
              <span className="meta-val">{project.questions.length}</span>
            </div>
            {project.weight_variable && (
              <div className="meta-row">
                <span className="meta-key">Weight var</span>
                <span className="meta-val meta-badge">{project.weight_variable}</span>
              </div>
            )}
            {project.wave_variable && (
              <div className="meta-row">
                <span className="meta-key">Wave var</span>
                <span className="meta-val meta-badge">{project.wave_variable}</span>
              </div>
            )}
            {!project.weight_variable && (
              <div className="meta-row">
                <span className="meta-key">Weighting</span>
                <span className="meta-val" style={{ color: '#94a3b8', fontSize: 11 }}>None</span>
              </div>
            )}
          </div>
        )}

        <div className="sidebar-footer">
          <span className="powered-by">Powered by Borderless Access</span>
        </div>
      </aside>

      {/* Main content */}
      <div className="chat-area">
        <header className="chat-header">
          <div className="chat-project-name">
            {project?.name ?? 'Loading…'}
          </div>
          <div className="chat-project-sub">
            {project
              ? `${project.questions.length} questions · AI-powered survey insights`
              : 'Connecting…'}
          </div>
        </header>

        {error && <div className="error-banner">⚠ {error}</div>}

        <ChatWindow
          messages={messages}
          loading={loading}
          input={input}
          onInputChange={setInput}
          onSend={handleSend}
        />
      </div>
    </div>
  );
}
