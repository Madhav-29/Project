import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  Database,
  FileSearch,
  Gauge,
  Layers,
  RefreshCw,
  Search,
  Send,
  ShieldCheck,
  UserRound
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const questions = [
  "What care gaps exist for this patient?",
  "Summarize documentation gaps and evidence.",
  "What revenue and quality risks need review?",
  "Build a patient timeline for clinical review."
];

const tabs = [
  "AI Answer",
  "Care Gaps",
  "Documentation",
  "Revenue & Quality",
  "Evidence",
  "Patient Timeline",
  "Audit Trail"
];

async function api(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch {
      detail = response.statusText || detail;
    }
    throw new Error(detail);
  }
  return response.json();
}

function statusClass(value) {
  return value ? "status ok" : "status warn";
}

function formatDate(value) {
  if (!value) return "Undated";
  return value;
}

function Card({ children, className = "" }) {
  return <section className={`card ${className}`}>{children}</section>;
}

function EmptyState({ title, text }) {
  return (
    <div className="empty-state">
      <FileSearch size={28} />
      <strong>{title}</strong>
      <span>{text}</span>
    </div>
  );
}

function GapCard({ gap, patientId, onReviewed }) {
  const [reviewing, setReviewing] = useState("");

  async function submitReview(status) {
    setReviewing(status);
    try {
      await api("/review/gap", {
        method: "POST",
        body: JSON.stringify({
          patient_id: patientId,
          gap_id: `${gap.type}:${gap.title}`,
          status,
          reviewer: "quality_reviewer",
          note: status === "accepted" ? "Accepted for follow-up queue." : "Marked for clinical review."
        })
      });
      onReviewed?.();
    } finally {
      setReviewing("");
    }
  }

  return (
    <article className="gap-card">
      <div className="gap-header">
        <div>
          <p className="eyebrow">{gap.type?.replaceAll("_", " ") || "gap"}</p>
          <h3>{gap.title}</h3>
        </div>
        <span className={`priority ${gap.priority}`}>{gap.priority}</span>
      </div>
      <p>{gap.reason}</p>
      <div className="impact">{gap.impact}</div>
      <div className="gap-meta">
        <span>{gap.time_window}</span>
        <span>Confidence: {gap.confidence}</span>
      </div>
      <div className="review-actions">
        <button type="button" onClick={() => submitReview("needs_review")} disabled={!!reviewing}>
          <ClipboardCheck size={15} /> {reviewing === "needs_review" ? "Saving" : "Review"}
        </button>
        <button type="button" onClick={() => submitReview("accepted")} disabled={!!reviewing}>
          <CheckCircle2 size={15} /> Accept
        </button>
      </div>
    </article>
  );
}

function EvidenceList({ evidence }) {
  if (!evidence?.length) {
    return <EmptyState title="No evidence returned" text="Run an analysis to retrieve patient-specific clinical context." />;
  }
  return (
    <div className="evidence-list">
      {evidence.map((item) => (
        <article className="evidence-row" key={item.id}>
          <div>
            <span className="source">{item.source_type}</span>
            <strong>{formatDate(item.date)}</strong>
          </div>
          <p>{item.text}</p>
          <small>{item.id}{item.score ? ` · score ${item.score.toFixed(2)}` : ""}</small>
        </article>
      ))}
    </div>
  );
}

function App() {
  const [patients, setPatients] = useState([]);
  const [selectedId, setSelectedId] = useState("p001");
  const [query, setQuery] = useState("");
  const [condition, setCondition] = useState("");
  const [question, setQuestion] = useState(questions[0]);
  const [overview, setOverview] = useState(null);
  const [index, setIndex] = useState(null);
  const [result, setResult] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [activeTab, setActiveTab] = useState(tabs[0]);
  const [loading, setLoading] = useState(false);
  const [booting, setBooting] = useState(true);
  const [error, setError] = useState("");

  const selectedPatient = useMemo(
    () => patients.find((patient) => patient.id === selectedId) || patients[0],
    [patients, selectedId]
  );

  async function refreshPatients() {
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    if (condition) params.set("condition", condition);
    const items = await api(`/patients/search?${params.toString()}`);
    setPatients(items);
    if (items.length && !items.some((patient) => patient.id === selectedId)) {
      setSelectedId(items[0].id);
    }
  }

  async function refreshStatus() {
    const [overviewPayload, indexPayload] = await Promise.all([
      api("/live/overview"),
      api("/index/status")
    ]);
    setOverview(overviewPayload);
    setIndex(indexPayload);
  }

  async function refreshReviews(patientId = selectedId) {
    if (!patientId) return;
    const items = await api(`/patients/${patientId}/reviews`);
    setReviews(items);
  }

  useEffect(() => {
    let active = true;
    async function bootstrap() {
      setBooting(true);
      setError("");
      try {
        const [patientPayload, overviewPayload, indexPayload] = await Promise.all([
          api("/patients/search"),
          api("/live/overview"),
          api("/index/status")
        ]);
        if (!active) return;
        setPatients(patientPayload);
        setOverview(overviewPayload);
        setIndex(indexPayload);
        setSelectedId(patientPayload[0]?.id || "p001");
      } catch (err) {
        if (active) setError(`Unable to reach the Clinical AI Platform API. ${err.message}`);
      } finally {
        if (active) setBooting(false);
      }
    }
    bootstrap();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const timeout = setTimeout(() => {
      refreshPatients().catch((err) => setError(err.message));
    }, 250);
    return () => clearTimeout(timeout);
  }, [query, condition]);

  useEffect(() => {
    refreshReviews(selectedId).catch(() => setReviews([]));
  }, [selectedId]);

  async function analyze() {
    if (!selectedId || !question.trim()) return;
    setLoading(true);
    setError("");
    try {
      const payload = await api("/ask", {
        method: "POST",
        body: JSON.stringify({ patient_id: selectedId, question, data_source: "synthea" })
      });
      setResult(payload);
      setActiveTab("AI Answer");
      await Promise.all([refreshStatus(), refreshReviews(selectedId)]);
    } catch (err) {
      setError(`Analysis could not complete. ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  function clearWorkspace() {
    setQuestion("");
    setResult(null);
    setActiveTab("AI Answer");
    setError("");
  }

  const kpis = [
    { label: "Care Gaps", value: result?.care_gaps?.length ?? 0, icon: Activity },
    { label: "Documentation Gaps", value: result?.documentation_gaps?.length ?? 0, icon: FileSearch },
    { label: "Revenue & Quality Risks", value: result?.revenue_quality_risks?.length ?? 0, icon: Gauge },
    { label: "Evidence Chunks", value: result?.audit?.retrieved_chunks ?? index?.documents_indexed ?? 0, icon: Database }
  ];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">CA</div>
          <div>
            <strong>Clinical AI Platform</strong>
            <span>Clinical Gap Intelligence</span>
          </div>
        </div>

        <div className="search-panel">
          <label>Patient Search</label>
          <div className="input-icon">
            <Search size={16} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Name, ID, condition" />
          </div>
          <input value={condition} onChange={(event) => setCondition(event.target.value)} placeholder="Filter by condition" />
        </div>

        <div className="patient-list">
          {patients.length ? (
            patients.map((patient) => (
              <button
                type="button"
                className={patient.id === selectedId ? "patient active" : "patient"}
                key={patient.id}
                onClick={() => setSelectedId(patient.id)}
              >
                <UserRound size={18} />
                <span>
                  <strong>{patient.name}</strong>
                  <small>{patient.id} · {patient.age || "age unknown"} · {patient.gender || "unknown"}</small>
                </span>
              </button>
            ))
          ) : (
            <EmptyState title="No patients found" text="Adjust filters to find a synthetic patient record." />
          )}
        </div>

        {selectedPatient && (
          <Card className="demographics">
            <p className="eyebrow">Selected Patient</p>
            <h2>{selectedPatient.name}</h2>
            <dl>
              <div><dt>ID</dt><dd>{selectedPatient.id}</dd></div>
              <div><dt>Age</dt><dd>{selectedPatient.age || "Unknown"}</dd></div>
              <div><dt>Gender</dt><dd>{selectedPatient.gender || "Unknown"}</dd></div>
            </dl>
            <div className="condition-tags">
              {(selectedPatient.conditions || []).slice(0, 5).map((item) => <span key={item}>{item}</span>)}
            </div>
          </Card>
        )}
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">AI Assistant for Clinical Gap Intelligence</p>
            <h1>Care Gap Analysis Workspace</h1>
            <p className="subtitle">Evidence-backed review for care gaps, documentation integrity, revenue risk, and timeline context.</p>
          </div>
          <div className="system-status">
            <span className={statusClass(overview?.status === "live")}><ShieldCheck size={15} /> API {overview?.status || "checking"}</span>
            <span className={statusClass(index?.ready)}><Layers size={15} /> Index {index?.ready ? "ready" : "pending"}</span>
            <span className="status"><Database size={15} /> {overview?.data_source || "synthea"}</span>
          </div>
        </header>

        {error && (
          <div className="error-banner">
            <AlertTriangle size={18} />
            <span>{error}</span>
          </div>
        )}

        <Card className="question-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Clinical Question</p>
              <h2>Ask the assistant</h2>
            </div>
            <button type="button" onClick={refreshStatus}><RefreshCw size={16} /> Refresh Status</button>
          </div>
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask about care gaps, documentation, evidence, revenue risk, or timeline events."
          />
          <div className="suggestions">
            {questions.map((item) => (
              <button type="button" key={item} onClick={() => setQuestion(item)}>{item}</button>
            ))}
          </div>
          <div className="action-row">
            <button type="button" className="primary" onClick={analyze} disabled={loading || booting || !question.trim()}>
              <Send size={16} /> {loading ? "Analyzing evidence" : "Analyze"}
            </button>
            <button type="button" onClick={clearWorkspace}>Clear</button>
          </div>
        </Card>

        <div className="kpi-grid">
          {kpis.map(({ label, value, icon: Icon }) => (
            <Card className="metric-card" key={label}>
              <Icon size={20} />
              <span>{label}</span>
              <strong>{booting ? "..." : value}</strong>
            </Card>
          ))}
        </div>

        <div className="tabs" role="tablist" aria-label="Analysis sections">
          {tabs.map((tab) => (
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === tab}
              className={activeTab === tab ? "active" : ""}
              key={tab}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>

        <Card className="results-card">
          {loading && <EmptyState title="Analyzing patient record" text="Retrieving evidence, running rules, and preparing an auditable response." />}
          {!loading && !result && <EmptyState title="Ready for analysis" text="Select a patient and ask a clinical question to begin." />}

          {!loading && result && activeTab === "AI Answer" && (
            <div className="answer-layout">
              <div>
                <p className="eyebrow">AI Assistant</p>
                <h2>Evidence Summary</h2>
                <p className="answer">{result.answer}</p>
                <h3>Recommended Actions</h3>
                <ul className="action-list">
                  {result.recommended_actions?.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </div>
              <aside>
                <h3>Patient Summary</h3>
                <p>{result.patient_summary}</p>
                <h3>Timeline Summary</h3>
                <p>{result.timeline_summary}</p>
              </aside>
            </div>
          )}

          {!loading && result && activeTab === "Care Gaps" && (
            <div className="card-grid">
              {result.care_gaps?.length ? result.care_gaps.map((gap) => (
                <GapCard gap={gap} patientId={selectedId} key={gap.title} onReviewed={() => refreshReviews(selectedId)} />
              )) : <EmptyState title="No care gaps returned" text="The rules engine did not identify care gaps for this analysis." />}
            </div>
          )}

          {!loading && result && activeTab === "Documentation" && (
            <div className="card-grid">
              {result.documentation_gaps?.length ? result.documentation_gaps.map((gap) => (
                <GapCard gap={gap} patientId={selectedId} key={gap.title} onReviewed={() => refreshReviews(selectedId)} />
              )) : <EmptyState title="No documentation gaps returned" text="No documentation integrity issues were identified for this question." />}
            </div>
          )}

          {!loading && result && activeTab === "Revenue & Quality" && (
            <div className="card-grid">
              {result.revenue_quality_risks?.length ? result.revenue_quality_risks.map((gap) => (
                <GapCard gap={gap} patientId={selectedId} key={gap.title} onReviewed={() => refreshReviews(selectedId)} />
              )) : <EmptyState title="No revenue or quality risks returned" text="No risk signals were identified by the configured rule set." />}
            </div>
          )}

          {!loading && result && activeTab === "Evidence" && <EvidenceList evidence={result.supporting_evidence || result.retrieved_context} />}

          {!loading && result && activeTab === "Patient Timeline" && (
            <div className="timeline">
              {result.timeline_events?.length ? result.timeline_events.map((event, index) => (
                <article key={`${event.id || event.text}-${index}`}>
                  <time>{formatDate(event.date)}</time>
                  <div>
                    <span>{event.type || "event"}</span>
                    <p>{event.text || event.description}</p>
                  </div>
                </article>
              )) : <EmptyState title="No timeline events" text="The patient record does not contain timeline events for this analysis." />}
            </div>
          )}

          {!loading && result && activeTab === "Audit Trail" && (
            <div className="audit-grid">
              {Object.entries(result.audit || {}).map(([key, value]) => (
                <div key={key}>
                  <span>{key.replaceAll("_", " ")}</span>
                  <strong>{Array.isArray(value) ? value.join(", ") || "None" : String(value)}</strong>
                </div>
              ))}
              <div className="reviews">
                <span>Human Reviews</span>
                <strong>{reviews.length}</strong>
              </div>
            </div>
          )}
        </Card>

        <footer>For demonstration with synthetic data only.</footer>
      </main>
    </div>
  );
}

export default App;
