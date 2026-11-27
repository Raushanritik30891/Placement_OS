import { FormEvent, ReactNode, useCallback, useEffect, useState } from "react";
import Editor from "@monaco-editor/react";
import { Activity, BookOpen, BrainCircuit, BriefcaseBusiness, CheckCircle2, ChevronRight, Code2, Database, Flame, GraduationCap, LayoutDashboard, LogOut, Play, Search, Send, ShieldCheck, Target, Terminal, Trophy, UserRound, Zap } from "lucide-react";

const API = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";
type User = { id: number; email: string; display_name: string; role: string };
type Overview = { published_problems: number; topics: number; assessment_questions: number; registered_users: number; features: Record<string, boolean> };
type Problem = { id: number; title: string; slug: string; statement: string; difficulty: string; topic_id: number | null; constraints: string; input_format: string; output_format: string; samples: { input: string; output: string; explanation: string }[]; starter_code: string; hints: string[]; secondary_topics: string[]; company_tags: string[] };
type Task = { id: number; title: string; category: string; due_date: string | null; is_completed: boolean };
type Category = { category: string; question_count: number };
type Question = { id: number; category: string; topic: string; prompt: string; options: string[]; difficulty: string };
type QueryResult = { columns: string[]; rows: (string | number | null)[][]; row_count: number; truncated: boolean; read_only: boolean };
type QuizResult = { score: number; total: number; percentage: number; results: { question_id: number; correct: boolean; correct_index: number; explanation: string }[] };
type ProgressSummary = { published_problems: number; solved_problems: number; attempted_problems: number; remaining_problems: number; submissions: number; accepted_submissions: number; accepted_rate: number | null; quiz_questions_answered: number; quiz_accuracy: number | null; readiness_score: number | null; readiness_note: string };

async function api<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (options.body) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", "Bearer " + token);
  const response = await fetch(API + path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Request failed (" + response.status + ")");
  return data as T;
}

const nav = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "practice", label: "DSA Practice", icon: Code2 },
  { id: "sql", label: "SQL Playground", icon: Database },
  { id: "assessments", label: "Assessments", icon: Activity },
  { id: "planner", label: "Study Planner", icon: Target },
  { id: "curriculum", label: "Learning Tracks", icon: BookOpen },
  { id: "admin", label: "Admin", icon: ShieldCheck },
];

const tracks = [
  { name: "Python Fundamentals", detail: "Syntax, collections, functions, OOP, exceptions and problem solving", scope: "Python", icon: Code2 },
  { name: "Python Libraries & Data", detail: "NumPy, Pandas, Requests, JSON, CSV and data cleaning", scope: "Libraries", icon: Database },
  { name: "Aptitude & Reasoning", detail: "Quantitative aptitude, logical reasoning and verbal ability", scope: "Aptitude", icon: Target },
  { name: "Core Computer Science", detail: "OOP, DBMS, operating systems, networks and Git", scope: "Core CS", icon: BrainCircuit },
  { name: "Company Preparation", detail: "Research-backed preparation paths for employer assessments", scope: "Companies", icon: BriefcaseBusiness },
  { name: "Data Engineering", detail: "SQL, ETL, Spark, Kafka, Airflow, AWS and data modelling", scope: "Data Engineering", icon: Database },
  { name: "AI / ML", detail: "Statistics, preprocessing, supervised learning and model evaluation", scope: "AI / ML", icon: BrainCircuit },
];

function AuthPanel({ onSuccess }: { onSuccess: (token: string, user: User) => void }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault(); setError(""); setBusy(true);
    try {
      const path = mode === "login" ? "/auth/login" : "/auth/register";
      const body = { email, password, ...(mode === "register" ? { display_name: name } : {}) };
      const result = await api<{ access_token: string; user: User }>(path, { method: "POST", body: JSON.stringify(body) });
      onSuccess(result.access_token, result.user);
    } catch (err) { setError(err instanceof Error ? err.message : "Authentication failed"); }
    finally { setBusy(false); }
  }
  return <div className="auth-wrap"><form className="auth-card" onSubmit={submit}>
    <div className="brand large"><span className="brand-mark">P</span><span>Placement<span className="brand-muted">OS</span></span></div>
    <div className="eyebrow">YOUR PERSONAL PLACEMENT WORKSPACE</div>
    <h1>{mode === "login" ? "Welcome back." : "Create your account."}</h1>
    <p className="muted">Save your practice progress, assessments and study plan across sessions.</p>
    {mode === "register" && <label>Display name<input value={name} onChange={e => setName(e.target.value)} minLength={2} maxLength={80} required /></label>}
    <label>Email<input type="email" value={email} onChange={e => setEmail(e.target.value)} required /></label>
    <label>Password<input type="password" value={password} onChange={e => setPassword(e.target.value)} minLength={mode === "register" ? 10 : 1} required /></label>
    {error && <div className="notice error">{error}</div>}
    <button className="primary wide" disabled={busy}>{busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}</button>
    <button type="button" className="link-button" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}>{mode === "login" ? "New to PlacementOS? Create an account" : "Already have an account? Sign in"}</button>
  </form></div>;
}

export default function App() {
  const [token, setToken] = useState<string | null>(() => sessionStorage.getItem("placementos_token"));
  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState<boolean>(() => Boolean(sessionStorage.getItem("placementos_token")));
  const [page, setPage] = useState("overview");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [progress, setProgress] = useState<ProgressSummary | null>(null);
  const [notice, setNotice] = useState("");
  const [adminTopicName, setAdminTopicName] = useState("");
  const [adminTopicSlug, setAdminTopicSlug] = useState("");
  const [adminProblemTitle, setAdminProblemTitle] = useState("");
  const [adminProblemSlug, setAdminProblemSlug] = useState("");
  const [adminProblemStatement, setAdminProblemStatement] = useState("");
  const [adminProblemDifficulty, setAdminProblemDifficulty] = useState("easy");
  const [adminProblemTopicId, setAdminProblemTopicId] = useState("");
  const [adminSampleInput, setAdminSampleInput] = useState("");
  const [adminSampleOutput, setAdminSampleOutput] = useState("");
  const [adminProblemId, setAdminProblemId] = useState("");
  const [adminTestInput, setAdminTestInput] = useState("");
  const [adminTestOutput, setAdminTestOutput] = useState("");
  const [adminTestIsSample, setAdminTestIsSample] = useState(false);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [problems, setProblems] = useState<Problem[]>([]);
  const [search, setSearch] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [selected, setSelected] = useState<Problem | null>(null);
  const [code, setCode] = useState("");
  const [customInput, setCustomInput] = useState("");
  const [sampleResults, setSampleResults] = useState<{ expected: string; actual: string; passed: boolean }[]>([]);
  const [runResult, setRunResult] = useState<{ status: string; stdout: string; stderr: string; execution_time: string | null } | null>(null);
  const [busy, setBusy] = useState(false);
  const [sql, setSql] = useState("SELECT c.name, c.city, SUM(o.amount) AS total_spend\nFROM customers c\nJOIN orders o ON o.customer_id = c.customer_id\nWHERE o.status = 'delivered'\nGROUP BY c.customer_id, c.name, c.city\nORDER BY total_spend DESC;");
  const [sqlResult, setSqlResult] = useState<QueryResult | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [quizCategory, setQuizCategory] = useState("");
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [quizResult, setQuizResult] = useState<QuizResult | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskTitle, setTaskTitle] = useState("");
  const [taskCategory, setTaskCategory] = useState("DSA");

  const refreshOverview = useCallback(async () => {
    try { const data = await api<Overview>("/overview"); setOverview(data); setApiOnline(true); }
    catch { setApiOnline(false); }
  }, []);
  useEffect(() => { refreshOverview(); }, [refreshOverview]);
  useEffect(() => {
    if (page === "overview" && token) api<ProgressSummary>("/progress/summary", {}, token).then(setProgress).catch(err => setNotice(err.message));
  }, [page, token]);
  useEffect(() => {
    if (!token) { setUser(null); setAuthLoading(false); return; }
    setAuthLoading(true);
    api<User>("/auth/me", {}, token).then(setUser).catch(() => {
      sessionStorage.removeItem("placementos_token"); setToken(null); setUser(null);
      setNotice("Your session expired. Please sign in again.");
    }).finally(() => setAuthLoading(false));
  }, [token]);
  useEffect(() => {
    if (page !== "practice") return;
    const params = new URLSearchParams();
    if (search.trim()) params.set("q", search.trim());
    if (difficulty) params.set("difficulty", difficulty);
    api<Problem[]>("/problems?" + params.toString()).then(setProblems).catch(err => setNotice(err.message));
  }, [page, search, difficulty]);
  useEffect(() => {
    if (page === "assessments") api<Category[]>("/assessments").then(setCategories).catch(err => setNotice(err.message));
  }, [page]);
  useEffect(() => {
    if (page === "planner" && token) api<Task[]>("/study-plan", {}, token).then(setTasks).catch(err => setNotice(err.message));
  }, [page, token]);

  function loginSuccess(newToken: string, newUser: User) {
    sessionStorage.setItem("placementos_token", newToken); setUser(newUser); setToken(newToken); setNotice("Signed in successfully.");
  }
  function logout() {
    sessionStorage.removeItem("placementos_token"); setToken(null); setUser(null);
    setSelected(null); setPage("overview"); setNotice("You have been signed out.");
  }
  async function chooseProblem(problem: Problem) {
    try {
      const detail = await api<Problem>("/problems/" + problem.id);
      setSelected(detail); setCode(detail.starter_code || "def solve():\n    pass");
      setCustomInput(detail.samples[0]?.input || ""); setSampleResults([]); setRunResult(null);
    } catch (err) { setNotice(err instanceof Error ? err.message : "Unable to load problem"); }
  }
  async function runCode(stdin: string) {
    if (!token) { setNotice("Sign in to run code."); return null; }
    return api<{ status: string; stdout: string; stderr: string; execution_time: string | null; memory: number | null }>(
      "/code/run", { method: "POST", body: JSON.stringify({ source_code: code, stdin }) }, token,
    );
  }
  async function runSamples() {
    if (!selected || !selected.samples.length) return;
    setBusy(true); setNotice(""); setSampleResults([]);
    try {
      const results = [];
      for (const sample of selected.samples) {
        const result = await runCode(sample.input);
        if (!result) break;
        const actual = result.stdout;
        results.push({ expected: sample.output, actual: result.status === "Accepted" ? actual : (result.stderr || result.status), passed: result.status === "Accepted" && actual.trim() === sample.output.trim() });
      }
      setSampleResults(results);
    } catch (err) { setNotice(err instanceof Error ? err.message : "Code execution failed"); }
    finally { setBusy(false); }
  }
  async function runCustom() {
    setBusy(true); setNotice("");
    try { const result = await runCode(customInput); if (result) setRunResult({ status: result.status, stdout: result.stdout, stderr: result.stderr, execution_time: result.execution_time }); }
    catch (err) { setNotice(err instanceof Error ? err.message : "Code execution failed"); }
    finally { setBusy(false); }
  }
  async function submitSolution() {
    if (!token || !selected) { setNotice("Sign in to submit a solution."); return; }
    setBusy(true); setNotice("");
    try {
      const result = await api<{ verdict: string; passed_tests: number; total_tests: number; execution_time_ms: number | null }>(
        "/submissions", { method: "POST", body: JSON.stringify({ problem_id: selected.id, language: "python", source_code: code }) }, token,
      );
      setNotice(result.verdict + ": " + result.passed_tests + "/" + result.total_tests + " tests passed.");
      await refreshOverview();
      api<ProgressSummary>("/progress/summary", {}, token).then(setProgress).catch(() => undefined);
    } catch (err) { setNotice(err instanceof Error ? err.message : "Submission failed"); }
    finally { setBusy(false); }
  }
  async function executeSql() {
    setBusy(true); setNotice("");
    try { setSqlResult(await api<QueryResult>("/sql/execute", { method: "POST", body: JSON.stringify({ query: sql }) })); }
    catch (err) { setSqlResult(null); setNotice(err instanceof Error ? err.message : "SQL execution failed"); }
    finally { setBusy(false); }
  }
  async function loadQuiz(category: string) {
    setQuizCategory(category); setAnswers({}); setQuizResult(null);
    try { setQuestions(await api<Question[]>("/assessments/" + encodeURIComponent(category))); }
    catch (err) { setNotice(err instanceof Error ? err.message : "Unable to load assessment"); }
  }
  async function submitQuiz() {
    if (!token) { setNotice("Sign in to save your assessment results."); return; }
    const payload = { category: quizCategory, answers: questions.filter(q => answers[q.id] !== undefined).map(q => ({ question_id: q.id, selected_index: answers[q.id] })) };
    if (payload.answers.length !== questions.length) { setNotice("Answer every question before submitting."); return; }
    try {
      setQuizResult(await api<QuizResult>("/assessments/submit", { method: "POST", body: JSON.stringify(payload) }, token));
      setNotice("Assessment submitted. Your score is saved to your account.");
    } catch (err) { setNotice(err instanceof Error ? err.message : "Assessment submission failed"); }
  }
  async function addTask(event: FormEvent) {
    event.preventDefault();
    if (!token || !taskTitle.trim()) return;
    try {
      const task = await api<Task>("/study-plan", { method: "POST", body: JSON.stringify({ title: taskTitle, category: taskCategory }) }, token);
      setTasks(current => [task, ...current]); setTaskTitle("");
    } catch (err) { setNotice(err instanceof Error ? err.message : "Unable to add task"); }
  }
  async function toggleTask(task: Task) {
    if (!token) return;
    try {
      const updated = await api<{ id: number; is_completed: boolean }>("/study-plan/" + task.id, { method: "PATCH", body: JSON.stringify({ is_completed: !task.is_completed }) }, token);
      setTasks(current => current.map(item => item.id === updated.id ? { ...item, is_completed: updated.is_completed } : item));
    } catch (err) { setNotice(err instanceof Error ? err.message : "Unable to update task"); }
  }
  async function adminCreateTopic(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    try {
      await api("/admin/topics", { method: "POST", body: JSON.stringify({ name: adminTopicName, slug: adminTopicSlug }) }, token);
      setNotice("Topic created."); setAdminTopicName(""); setAdminTopicSlug(""); await refreshOverview();
    } catch (err) { setNotice(err instanceof Error ? err.message : "Topic creation failed"); }
  }
  async function adminCreateProblem(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    try {
      const result = await api<{ id: number; slug: string; is_published: boolean }>("/admin/problems", {
        method: "POST",
        body: JSON.stringify({
          title: adminProblemTitle, slug: adminProblemSlug, statement: adminProblemStatement,
          difficulty: adminProblemDifficulty, topic_id: adminProblemTopicId ? Number(adminProblemTopicId) : null,
          samples: [{ input: adminSampleInput, output: adminSampleOutput, explanation: "" }],
          starter_code: "import json\\n\\ndef solve():\\n    data = json.loads(input())\\n    # Write your solution\\n    print()\\n\\nsolve()",
          hints: [], is_published: false
        })
      }, token);
      setNotice("Draft problem created with ID " + result.id + ". Add its test cases below before publishing.");
      setAdminProblemId(String(result.id)); setAdminProblemTitle(""); setAdminProblemSlug(""); setAdminProblemStatement("");
      setAdminSampleInput(""); setAdminSampleOutput("");
    } catch (err) { setNotice(err instanceof Error ? err.message : "Problem creation failed"); }
  }
  async function adminAddTestCase(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    try {
      await api("/admin/problems/" + adminProblemId + "/test-cases", {
        method: "POST", body: JSON.stringify({ stdin: adminTestInput, expected_output: adminTestOutput, is_sample: adminTestIsSample })
      }, token);
      setNotice(adminTestIsSample ? "Public sample test added." : "Hidden test case added."); setAdminTestInput(""); setAdminTestOutput("");
    } catch (err) { setNotice(err instanceof Error ? err.message : "Test-case creation failed"); }
  }
  async function adminPublish(problemId: string, is_published: boolean) {
    if (!token || !problemId) return;
    try {
      await api("/admin/problems/" + problemId + "/publish", { method: "PATCH", body: JSON.stringify({ is_published }) }, token);
      setNotice(is_published ? "Problem published." : "Problem unpublished."); await refreshOverview();
    } catch (err) { setNotice(err instanceof Error ? err.message : "Publish update failed"); }
  }

  if (!user && authLoading) return <div className="auth-wrap"><div className="auth-card"><div className="brand large"><span className="brand-mark">P</span><span>Placement<span className="brand-muted">OS</span></span></div><p className="muted">Restoring your session…</p></div></div>;
  if (!user) return <AuthPanel onSuccess={loginSuccess}/>;

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">P</span><span>Placement<span className="brand-muted">OS</span></span></div>
      <div className="side-label">WORKSPACE</div>
      <nav>{nav.filter(item => item.id !== "admin" || user.role === "admin").map(item => { const Icon = item.icon; return <button key={item.id} className={page === item.id ? "nav-item active" : "nav-item"} onClick={() => { setPage(item.id); setNotice(""); }}>
        <Icon size={18}/><span>{item.label}</span>{page === item.id && <span className="nav-dot"/>}
      </button>; })}</nav>
      <div className="sidebar-bottom">
        <div className="goal-card"><div className="goal-icon"><GraduationCap size={18}/></div><b>2027 placement goal</b><p>Practise, measure and improve.</p><div className="goal-line"><span style={{width:"0%"}}/></div><small>Progress comes from real results</small></div>
        <div className="profile"><div className="avatar">{user.display_name.slice(0,2).toUpperCase()}</div><div><b>{user.display_name}</b><small>{user.role}</small></div><button className="icon-button logout" title="Sign out" onClick={logout}><LogOut size={15}/></button></div>
      </div>
    </aside>

    <main className="main">
      <header className="topbar"><div><span className="crumb">Workspace</span><ChevronRight size={14}/><b>{nav.find(item => item.id === page)?.label || "Learning"}</b></div>
        <div className="top-actions"><span className={apiOnline ? "status online" : "status offline"}><i/>{apiOnline ? "API connected" : "API unavailable"}</span><span className="role-pill"><UserRound size={13}/>{user.display_name}</span></div>
      </header>
      {notice && <div className="notice"><span>{notice}</span><button onClick={() => setNotice("")}>×</button></div>}

      {page === "overview" && <section className="page-content">
        <section className="welcome"><div><div className="eyebrow"><Zap size={14}/> YOUR PLACEMENT WORKSPACE</div><h1>Build skills. <em>Prove them.</em></h1><p>Learn deliberately, practise independently and measure what you can actually solve.</p></div><div className="welcome-orbit"><div className="orbit-ring ring-one"/><div className="orbit-ring ring-two"/><div className="orbit-core"><GraduationCap size={33}/></div><span className="orbit-chip chip-one"><Code2 size={15}/> DSA</span><span className="orbit-chip chip-two"><Database size={15}/> SQL</span><span className="orbit-chip chip-three"><BrainCircuit size={15}/> Python</span></div></section>
        <section className="metric-grid">
          <Metric title="Published DSA problems" value={overview?.published_problems ?? "—"} note="Actual published catalogue" icon={<Code2 size={17}/>}/>
          <Metric title="Problems solved" value={progress?.solved_problems ?? "—"} note={progress ? progress.remaining_problems + " remaining" : "Sign in to load your progress"} icon={<CheckCircle2 size={17}/>}/>
          <Metric title="Assessment accuracy" value={progress?.quiz_accuracy === null || progress?.quiz_accuracy === undefined ? "—" : progress.quiz_accuracy + "%"} note={progress ? progress.quiz_questions_answered + " questions answered" : "Saved assessment history"} icon={<Target size={17}/>}/>
          <Metric title="Accepted submissions" value={progress?.accepted_submissions ?? "—"} note={progress ? progress.submissions + " total submissions" : "Verified judge results only"} icon={<Trophy size={17}/>}/>
        </section>
        <div className="section-head"><div><div className="eyebrow">YOUR WORKSPACE</div><h2>Pick up where you want to grow</h2><p>Choose an active tool. Planned curriculum is shown separately from working features.</p></div></div>
        <div className="quick-grid">
          <Quick title="DSA problem bank" detail="Search problems, open statements and submit solutions." icon={<Code2/>} onClick={() => setPage("practice")}/>
          <Quick title="SQL playground" detail="Run SELECT queries in an isolated read-only learning database." icon={<Database/>} onClick={() => setPage("sql")}/>
          <Quick title="Timed assessments" detail="Take Python, SQL, aptitude and Core CS quizzes." icon={<Activity/>} onClick={() => setPage("assessments")}/>
          <Quick title="Study planner" detail="Create personal tasks and track completion." icon={<Target/>} onClick={() => setPage("planner")}/>
        </div>
        <section className="status-panel"><div><ShieldCheck size={18}/><b>Execution security</b></div><p>{overview?.features.secure_code_execution ? "The configured Judge0 execution service is enabled." : "Code execution is intentionally disabled until a hardened Judge0 service is deployed and explicitly confirmed. SQL exercises run in a separate read-only in-memory database."}</p></section>
      </section>}

      {page === "practice" && <section className="page-content">
        {!selected ? <>
          <div className="section-head"><div><div className="eyebrow">DSA CATALOGUE</div><h2>Practice problem solving</h2><p>{problems.length} published problems currently available. This is the starter bank, not the 200-question target.</p></div></div>
          <div className="filter-row"><label className="search"><Search size={16}/><input placeholder="Search problems" value={search} onChange={e => setSearch(e.target.value)}/></label><select value={difficulty} onChange={e => setDifficulty(e.target.value)}><option value="">All difficulty levels</option><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></div>
          <div className="problem-list">{problems.map(problem => <button key={problem.id} className="problem-row" onClick={() => chooseProblem(problem)}><span className="problem-id">#{String(problem.id).padStart(3,"0")}</span><span className="problem-name">{problem.title}<small>{problem.secondary_topics?.join(" · ") || problem.slug}</small></span><span className={"difficulty " + problem.difficulty}>{problem.difficulty}</span><ChevronRight size={17}/></button>)}
            {!problems.length && <div className="empty-state">No published problems match this filter. Run python -m app.seed in the backend folder to load the starter catalogue.</div>}
          </div>
        </> : <div className="workspace-layout">
          <div className="problem-description">
            <button className="back-link" onClick={() => setSelected(null)}>← Back to problems</button>
            <div className="problem-title"><span className="problem-id">#{selected.id}</span><span className={"difficulty " + selected.difficulty}>{selected.difficulty}</span></div>
            <h2>{selected.title}</h2><p>{selected.statement}</p>
            <h3>Input format</h3><p>{selected.input_format || "See the sample input."}</p>
            <h3>Output format</h3><p>{selected.output_format || "See the sample output."}</p>
            {selected.constraints && <><h3>Constraints</h3><p>{selected.constraints}</p></>}
            {selected.explanation && <><h3>Approach</h3><p>{selected.explanation}</p></>}
            {(selected.time_complexity || selected.space_complexity) && <><h3>Complexity</h3><p>Time: {selected.time_complexity || "—"} · Space: {selected.space_complexity || "—"}</p></>}
            <h3>Examples</h3>{selected.samples.map((sample,index)=><div className="sample" key={index}><b>Example {index+1}</b><pre>{"Input: " + sample.input + "\nOutput: " + sample.output}</pre><small>{sample.explanation}</small></div>)}
            {selected.hints.length>0 && <details className="hints"><summary>Progressive hints</summary>{selected.hints.map((hint,i)=><p key={i}>{i+1}. {hint}</p>)}</details>}
            {selected.secondary_topics?.length>0 && <div className="tag-row">{selected.secondary_topics.map(tag=><span key={tag}>{tag}</span>)}</div>}
          </div>
          <div className="code-panel">
            <div className="editor-head"><div><Terminal size={15}/> Python 3</div><span>Monaco Editor</span></div>
            <Editor height="380px" language="python" theme="vs-dark" value={code} onChange={value => setCode(value ?? "")} options={{fontSize:14,minimap:{enabled:false},automaticLayout:true,tabSize:4,wordWrap:"on",scrollBeyondLastLine:false}}/>
            <div className="input-label">CUSTOM INPUT</div><textarea className="input-area" value={customInput} onChange={e => setCustomInput(e.target.value)} placeholder="Enter stdin here…"/>
            <div className="editor-actions"><button className="secondary" onClick={runSamples} disabled={busy}><Play size={14}/> Run sample tests</button><button className="secondary" onClick={runCustom} disabled={busy}>Run custom input</button><button className="primary" onClick={submitSolution} disabled={busy}><Send size={14}/> Submit</button></div>
            {sampleResults.map((result,i)=><div className="test-result" key={i}><b>Sample {i+1}</b><span className={result.passed?"passed":"failed"}>{result.passed?"Passed":"Failed"}</span><small>Expected: {result.expected} · Actual: {result.actual}</small></div>)}
            {runResult && <div className="console"><div className="console-head">Execution result <span>{runResult.status}</span></div><pre>{runResult.stdout || runResult.stderr || "No output"}</pre><small>Execution time: {runResult.execution_time ?? "not reported"}</small></div>}
          </div>
        </div>}
      </section>}

      {page === "sql" && <section className="page-content">
        <div className="section-head"><div><div className="eyebrow">SQL PLAYGROUND</div><h2>Query a practice database</h2><p>Each request uses a new in-memory SQLite database. Only read-only SELECT / CTE queries are allowed.</p></div></div>
        <div className="sql-layout"><div className="schema-panel"><h3>Available tables</h3><SchemaTable name="customers" columns="customer_id · name · city"/><SchemaTable name="orders" columns="order_id · customer_id · order_date · amount · status"/><SchemaTable name="employees" columns="employee_id · name · department_id · salary · joining_date"/><SchemaTable name="departments" columns="department_id · department_name"/></div>
          <div className="sql-editor-panel"><div className="editor-head"><div><Database size={15}/> SQL (SQLite)</div><span>Read-only session</span></div><Editor height="280px" language="sql" theme="vs-dark" value={sql} onChange={value=>setSql(value??"")} options={{fontSize:14,minimap:{enabled:false},automaticLayout:true,wordWrap:"on"}}/><div className="editor-actions"><button className="primary" onClick={executeSql} disabled={busy}><Play size={14}/> Run query</button><button className="secondary" onClick={()=>{setSql("SELECT * FROM customers;");setSqlResult(null);}}>Reset query</button></div>
          </div></div>
        {sqlResult && <div className="result-panel"><div className="result-head"><b>Query result</b><span>{sqlResult.row_count} rows returned{sqlResult.truncated?" · result truncated":""}</span></div><div className="table-scroll"><table><thead><tr>{sqlResult.columns.map(col=><th key={col}>{col}</th>)}</tr></thead><tbody>{sqlResult.rows.map((row,i)=><tr key={i}>{row.map((value,j)=><td key={j}>{value===null?"NULL":String(value)}</td>)}</tr>)}</tbody></table></div></div>}
      </section>}

      {page === "assessments" && <section className="page-content">
        <div className="section-head"><div><div className="eyebrow">ASSESSMENT ENGINE</div><h2>Test what you know</h2><p>Quizzes are graded server-side. Sign in to save results to your account.</p></div></div>
        {!quizCategory ? <div className="category-grid">{categories.map(category=><button className="category-card" key={category.category} onClick={()=>loadQuiz(category.category)}><div className="track-icon mint"><BookOpen size={20}/></div><h3>{category.category.toUpperCase()}</h3><p>{category.question_count} published questions</p><span>Start assessment <ChevronRight size={15}/></span></button>)}
          {!categories.length && <div className="empty-state">No assessment questions have been published. Run the backend seeder to load starter quizzes.</div>}</div>
        : <div className="quiz-panel"><div className="quiz-top"><button className="back-link" onClick={()=>{setQuizCategory("");setQuestions([]);setQuizResult(null);}}>← All assessments</button><span>{quizCategory.toUpperCase()} · {questions.length} questions</span></div>
          {questions.map((question,index)=><article className="question-card" key={question.id}><div className="question-meta">QUESTION {index+1} · {question.topic} · {question.difficulty}</div><h3>{question.prompt}</h3><div className="option-list">{question.options.map((option,optionIndex)=><label className={answers[question.id]===optionIndex?"option selected":"option"} key={optionIndex}><input type="radio" name={String(question.id)} checked={answers[question.id]===optionIndex} onChange={()=>setAnswers(current=>({...current,[question.id]:optionIndex}))}/><span>{String.fromCharCode(65+optionIndex)}.</span>{option}</label>)}</div>
            {quizResult && <div className={quizResult.results.find(r=>r.question_id===question.id)?.correct?"explanation good":"explanation bad"}>{quizResult.results.find(r=>r.question_id===question.id)?.correct?"Correct":"Review"} — {quizResult.results.find(r=>r.question_id===question.id)?.explanation}</div>}</article>)}
          {quizResult ? <div className="score-card"><Trophy size={23}/><b>{quizResult.score} / {quizResult.total}</b><span>{quizResult.percentage}% score</span></div> : <button className="primary" onClick={submitQuiz} disabled={!questions.length}>Submit assessment</button>}
        </div>}
      </section>}

      {page === "planner" && <section className="page-content">
        <div className="section-head"><div><div className="eyebrow">STUDY MANAGEMENT</div><h2>Your study plan</h2><p>Create tasks and mark them complete. Tasks are saved to your account.</p></div></div>
        <form className="task-form" onSubmit={addTask}><input value={taskTitle} onChange={e=>setTaskTitle(e.target.value)} placeholder="Add a study task…" minLength={2} required/><select value={taskCategory} onChange={e=>setTaskCategory(e.target.value)}><option>DSA</option><option>Python</option><option>SQL</option><option>Aptitude</option><option>Core CS</option><option>Data Engineering</option><option>AI / ML</option></select><button className="primary">Add task</button></form>
        <div className="task-list">{tasks.map(task=><label key={task.id} className={task.is_completed?"task completed":"task"}><input type="checkbox" checked={task.is_completed} onChange={()=>toggleTask(task)}/><span>{task.title}<small>{task.category}{task.due_date ? " · Due " + task.due_date : ""}</small></span><CheckCircle2 size={17}/></label>)}
          {!tasks.length && <div className="empty-state">No study tasks yet. Add your first task above.</div>}</div>
      </section>}

      {page === "curriculum" && <section className="page-content">
        <div className="section-head"><div><div className="eyebrow">LEARNING ROADMAP</div><h2>Placement preparation tracks</h2><p>Curriculum scopes from your brief. Active tools are separate from lessons still to be built.</p></div></div>
        <div className="track-grid">{tracks.map(track=>{const Icon=track.icon;return <article className="track-card" key={track.scope}><div className="track-icon mint"><Icon size={21}/></div><h3>{track.name}</h3><p>{track.detail}</p><div className="track-footer"><span>Curriculum outline · content build pending</span><button onClick={()=>setNotice(track.name + ": lessons are planned but not fully published.")} aria-label={"Details for " + track.name}><ChevronRight size={18}/></button></div></article>;})}</div>
        <div className="notice info">Company-specific exam formats remain research-pending. Practice items are not labelled as actual company interview questions.</div>
      </section>}

      {page === "admin" && user.role === "admin" && <section className="page-content">
        <div className="section-head"><div><div className="eyebrow">CONTENT MANAGEMENT</div><h2>Admin workspace</h2><p>Create curriculum topics, draft problems, add hidden test cases and publish reviewed content.</p></div></div>
        <div className="admin-grid">
          <form className="admin-form" onSubmit={adminCreateTopic}><h3>Create topic</h3><label>Topic name<input value={adminTopicName} onChange={e=>setAdminTopicName(e.target.value)} required/></label><label>URL slug<input value={adminTopicSlug} onChange={e=>setAdminTopicSlug(e.target.value)} placeholder="arrays-basics" required/></label><button className="primary">Create topic</button></form>
          <form className="admin-form" onSubmit={adminCreateProblem}><h3>Create problem draft</h3><label>Title<input value={adminProblemTitle} onChange={e=>setAdminProblemTitle(e.target.value)} required/></label><label>Slug<input value={adminProblemSlug} onChange={e=>setAdminProblemSlug(e.target.value)} placeholder="my-practice-problem" required/></label><label>Difficulty<select value={adminProblemDifficulty} onChange={e=>setAdminProblemDifficulty(e.target.value)}><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label><label>Topic ID (optional)<input type="number" min="1" value={adminProblemTopicId} onChange={e=>setAdminProblemTopicId(e.target.value)}/></label><label>Problem statement<textarea value={adminProblemStatement} onChange={e=>setAdminProblemStatement(e.target.value)} required/></label><label>Public sample input<textarea value={adminSampleInput} onChange={e=>setAdminSampleInput(e.target.value)} required/></label><label>Public sample expected output<textarea value={adminSampleOutput} onChange={e=>setAdminSampleOutput(e.target.value)} required/></label><button className="primary">Create draft</button></form>
          <form className="admin-form" onSubmit={adminAddTestCase}><h3>Add hidden test case</h3><label>Problem ID<input type="number" min="1" value={adminProblemId} onChange={e=>setAdminProblemId(e.target.value)} required/></label><label>Standard input<textarea value={adminTestInput} onChange={e=>setAdminTestInput(e.target.value)} required/></label><label>Expected output<textarea value={adminTestOutput} onChange={e=>setAdminTestOutput(e.target.value)} required/></label><label className="check-label"><input type="checkbox" checked={adminTestIsSample} onChange={e=>setAdminTestIsSample(e.target.checked)}/> Mark as public sample (leave unchecked for hidden test)</label><button className="primary">Add test case</button></form>
          <form className="admin-form" onSubmit={e=>{e.preventDefault();adminPublish(adminProblemId,true);}}><h3>Publish reviewed problem</h3><label>Problem ID<input type="number" min="1" value={adminProblemId} onChange={e=>setAdminProblemId(e.target.value)} required/></label><p className="muted">Only publish after validating the statement, public samples and server-side test cases.</p><button className="primary">Publish problem</button><button type="button" className="secondary" onClick={()=>adminPublish(adminProblemId,false)}>Unpublish</button></form>
        </div>
        <div className="notice info">Admin access is never self-selected at registration. Promote a trusted account manually in the database after verifying its email; see docs/ADMIN_SETUP.md.</div>
      </section>}
      {user.role === "admin" && page !== "admin" && <div className="admin-shortcut"><ShieldCheck size={15}/> Admin role detected. <button className="link-button" onClick={()=>setPage("admin")}>Open admin workspace</button></div>}
      <footer><span>PlacementOS <b>•</b> Foundation release</span><span>Counts reflect stored data, not roadmap targets.</span></footer>
    </main>
  </div>;
}

function Metric({title,value,note,icon}:{title:string;value:string|number;note:string;icon:ReactNode}) {
  return <article className="metric"><div className="metric-top"><span>{title}</span>{icon}</div><strong>{value}</strong><small>{note}</small></article>;
}
function Quick({title,detail,icon,onClick}:{title:string;detail:string;icon:ReactNode;onClick:()=>void}) {
  return <button className="quick-card" onClick={onClick}><div className="quick-icon">{icon}</div><h3>{title}</h3><p>{detail}</p><span>Open workspace <ChevronRight size={15}/></span></button>;
}
function SchemaTable({name,columns}:{name:string;columns:string}) {
  return <div className="schema-table"><b>{name}</b><small>{columns}</small></div>;
}
