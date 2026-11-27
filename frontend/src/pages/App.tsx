import { FormEvent, ReactNode, useCallback, useEffect, useRef, useState } from "react";
import Editor from "@monaco-editor/react";
import ReactMarkdown from "react-markdown";
import { Activity, BookOpen, BrainCircuit, BriefcaseBusiness, CheckCircle2, ChevronRight, Code2, Database, Flame, GraduationCap, LayoutDashboard, LogOut, Play, Search, Send, ShieldCheck, Target, Terminal, Trophy, UserRound, Zap } from "lucide-react";

const API = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";
type User = { id: number; email: string; display_name: string; role: string };
type Overview = { published_problems: number; topics: number; assessment_questions: number; registered_users: number; features: Record<string, boolean> };
type Problem = { id: number; title: string; slug: string; statement: string; difficulty: string; topic_id: number | null; constraints: string; input_format: string; output_format: string; samples: { input: string; output: string; explanation: string }[]; starter_code: string; hints: string[]; explanation: string; time_complexity: string; space_complexity: string; secondary_topics: string[]; company_tags: string[] };
type Task = { id: number; title: string; category: string; due_date: string | null; is_completed: boolean; plan_id?: number | null; day_number?: number | null; description?: string; estimated_minutes?: number };
type ActivePlan = { id: number; title: string; duration_days: number; target_role: string; target_company: string; daily_hours: number; skill_level: string; start_date: string; tasks: Task[] };
type Category = { category: string; question_count: number };
type Question = { id: number; category: string; topic: string; prompt: string; options: string[]; difficulty: string };
type QueryResult = { columns: string[]; rows: (string | number | null)[][]; row_count: number; truncated: boolean; read_only: boolean };
type SQLProblem = { id: number; title: string; slug: string; prompt: string; topic: string; difficulty: string };
type SQLChallengeResult = { verdict: string; submission_id?: number; row_count?: number; columns?: string[]; rows?: (string | number | null)[][]; explanation?: string; error?: string };
type SQLProgress = { total_submissions: number; accepted_submissions: number; solved_challenges: number; acceptance_rate: number | null };
type QuizResult = { score: number; total: number; percentage: number; results: { question_id: number; correct: boolean; correct_index: number; explanation: string }[] };
type ProgressSummary = { published_problems: number; solved_problems: number; attempted_problems: number; remaining_problems: number; submissions: number; accepted_submissions: number; accepted_rate: number | null; quiz_attempts: number; quiz_questions_answered: number; quiz_accuracy: number | null; dsa_coverage: number | null; readiness_score: number | null; readiness_note: string; current_streak_days: number; longest_streak_days: number; last_active_date: string | null };
type Course = { id: number; title: string; slug: string; category: string; description: string; difficulty: string; lesson_count: number };
type Lesson = { id: number; title: string; slug: string; content: string; estimated_minutes: number; display_order: number };
type CourseDetail = Omit<Course, "lesson_count"> & { lessons: Lesson[] };
type LearningProgress = { course_id: number; course_title: string; completed_lessons: number; total_lessons: number; percentage: number };
type CompanyProfile = { id: number; name: string; slug: string; category: string; career_url: string; description: string; hiring_tracks: string[]; research_status: string; last_verified_at: string | null };
type CompanyResearchSource = { id: number; title: string; url: string; evidence_type: string; claim: string; confidence: string; checked_at: string };
type CompanyDetail = CompanyProfile & { research_sources: CompanyResearchSource[] };

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
  { id: "companies", label: "Company Prep", icon: BriefcaseBusiness },
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
  const [adminCompanyId, setAdminCompanyId] = useState("");
  const [adminCompanySourceTitle, setAdminCompanySourceTitle] = useState("");
  const [adminCompanySourceUrl, setAdminCompanySourceUrl] = useState("");
  const [adminCompanySourceType, setAdminCompanySourceType] = useState("official");
  const [adminCompanySourceClaim, setAdminCompanySourceClaim] = useState("");
  const [adminCompanySourceConfidence, setAdminCompanySourceConfidence] = useState("medium");
  const [adminMapCompanySlug, setAdminMapCompanySlug] = useState("");
  const [adminMapProblemId, setAdminMapProblemId] = useState("");
  const [adminSqlTitle, setAdminSqlTitle] = useState("");
  const [adminSqlSlug, setAdminSqlSlug] = useState("");
  const [adminSqlPrompt, setAdminSqlPrompt] = useState("");
  const [adminSqlTopic, setAdminSqlTopic] = useState("SQL");
  const [adminSqlDifficulty, setAdminSqlDifficulty] = useState("easy");
  const [adminSqlReference, setAdminSqlReference] = useState("");
  const [adminSqlExplanation, setAdminSqlExplanation] = useState("");
  const [adminQuizCategory, setAdminQuizCategory] = useState("python");
  const [adminQuizTopic, setAdminQuizTopic] = useState("");
  const [adminQuizPrompt, setAdminQuizPrompt] = useState("");
  const [adminQuizOptions, setAdminQuizOptions] = useState("");
  const [adminQuizCorrectIndex, setAdminQuizCorrectIndex] = useState("0");
  const [adminQuizExplanation, setAdminQuizExplanation] = useState("");
  const [adminQuizDifficulty, setAdminQuizDifficulty] = useState("easy");
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
  const [sqlMode, setSqlMode] = useState<"playground" | "challenges">("playground");
  const [sqlChallenges, setSqlChallenges] = useState<SQLProblem[]>([]);
  const [sqlProgress, setSqlProgress] = useState<SQLProgress | null>(null);
  const [selectedSqlChallenge, setSelectedSqlChallenge] = useState<SQLProblem | null>(null);
  const [sqlChallengeResult, setSqlChallengeResult] = useState<SQLChallengeResult | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [quizCategory, setQuizCategory] = useState("");
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [quizResult, setQuizResult] = useState<QuizResult | null>(null);
  const [quizSessionId, setQuizSessionId] = useState<number | null>(null);
  const [quizEndsAt, setQuizEndsAt] = useState<string | null>(null);
  const [quizRemaining, setQuizRemaining] = useState<number | null>(null);
  const quizSubmitLock = useRef(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activePlan, setActivePlan] = useState<ActivePlan | null>(null);
  const [planDuration, setPlanDuration] = useState("30");
  const [planRole, setPlanRole] = useState("general");
  const [planCompany, setPlanCompany] = useState("");
  const [planHours, setPlanHours] = useState("3");
  const [planLevel, setPlanLevel] = useState("beginner");
  const [planStartDate, setPlanStartDate] = useState(() => new Date().toISOString().slice(0,10));
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<CourseDetail | null>(null);
  const [selectedLesson, setSelectedLesson] = useState<Lesson | null>(null);
  const [learningProgress, setLearningProgress] = useState<LearningProgress[]>([]);
  const [companies, setCompanies] = useState<CompanyProfile[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<CompanyDetail | null>(null);
  const [companyProblems, setCompanyProblems] = useState<Problem[]>([]);
  const [companySearch, setCompanySearch] = useState("");
  const [companyCategory, setCompanyCategory] = useState("");
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
    if (page !== "planner" || !token) return;
    api<Task[]>("/study-plan", {}, token).then(setTasks).catch(err => setNotice(err.message));
    api<ActivePlan | null>("/study-plan/active", {}, token).then(setActivePlan).catch(err => setNotice(err.message));
  }, [page, token]);
  useEffect(() => {
    if (page !== "curriculum") return;
    api<Course[]>("/courses").then(setCourses).catch(err => setNotice(err.message));
    if (token) api<LearningProgress[]>("/learning-progress", {}, token).then(setLearningProgress).catch(err => setNotice(err.message));
  }, [page, token]);
  useEffect(() => {
    if (page === "admin") api<CompanyProfile[]>("/companies").then(setCompanies).catch(err => setNotice(err.message));
    if (page !== "companies") return;
    const params = new URLSearchParams();
    if (companySearch.trim()) params.set("q", companySearch.trim());
    if (companyCategory) params.set("category", companyCategory);
    api<CompanyProfile[]>("/companies?" + params.toString()).then(setCompanies).catch(err => setNotice(err.message));
  }, [page, companySearch, companyCategory]);

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
  async function submitSqlChallenge() {
    if (!token || !selectedSqlChallenge) { setNotice("Sign in and select a SQL challenge before submitting."); return; }
    setBusy(true); setNotice(""); setSqlChallengeResult(null);
    try {
      const result = await api<SQLChallengeResult>(
        "/sql/problems/" + selectedSqlChallenge.id + "/submit",
        { method: "POST", body: JSON.stringify({ query: sql }) },
        token,
      );
      setSqlChallengeResult(result);
      setNotice(result.verdict === "Accepted" ? "SQL challenge accepted." : "SQL challenge result: " + result.verdict);
      const updatedProgress = await api<SQLProgress>("/sql/progress", {}, token);
      setSqlProgress(updatedProgress);
    } catch (err) { setNotice(err instanceof Error ? err.message : "SQL challenge submission failed"); }
    finally { setBusy(false); }
  }
  async function loadQuiz(category: string) {
    if (!token) { setNotice("Sign in to start a timed assessment."); return; }
    setQuizCategory(category); setAnswers({}); setQuizResult(null); setQuizSessionId(null); setQuizEndsAt(null); setQuizRemaining(null); quizSubmitLock.current = false;
    try {
      const session = await api<{session_id:number;ends_at:string;questions:Question[]}>(
        "/assessments/start",
        { method:"POST", body:JSON.stringify({category,duration_minutes:20,question_limit:20}) },
        token,
      );
      setQuestions(session.questions); setQuizSessionId(session.session_id); setQuizEndsAt(session.ends_at);
    } catch (err) { setQuizCategory(""); setNotice(err instanceof Error ? err.message : "Unable to start assessment"); }
  }
  const submitQuiz = useCallback(async (automatic = false) => {
    if (!token || !quizSessionId || quizSubmitLock.current) return;
    const submittedAnswers = questions
      .filter(q => answers[q.id] !== undefined)
      .map(q => ({ question_id:q.id, selected_index:answers[q.id] }));
    if (!automatic && submittedAnswers.length !== questions.length) {
      setNotice("Answer every question before submitting.");
      return;
    }
    quizSubmitLock.current = true;
    setBusy(true);
    try {
      const result = await api<QuizResult>(
        "/assessments/sessions/" + quizSessionId + "/submit",
        { method:"POST", body:JSON.stringify({answers:submittedAnswers}) },
        token,
      );
      setQuizResult(result); setQuizSessionId(null); setQuizEndsAt(null); setQuizRemaining(null);
      setNotice(automatic ? "Time expired. Your assessment was automatically submitted." : "Assessment submitted. Your score is saved.");
      const latest = await api<ProgressSummary>("/progress/summary", {}, token).catch(() => null);
      if (latest) setProgress(latest);
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "Assessment submission failed");
      if (automatic) { setQuizSessionId(null); setQuizEndsAt(null); setQuizRemaining(0); }
      else quizSubmitLock.current = false;
    } finally { setBusy(false); }
  }, [token, quizSessionId, questions, answers]);
  useEffect(() => {
    if (!quizSessionId || !quizEndsAt || quizResult) return;
    const updateTimer = () => {
      const seconds = Math.max(0, Math.ceil((Date.parse(quizEndsAt) - Date.now()) / 1000));
      setQuizRemaining(seconds);
      if (seconds <= 0) void submitQuiz(true);
    };
    updateTimer();
    const interval = window.setInterval(updateTimer, 1000);
    return () => window.clearInterval(interval);
  }, [quizSessionId, quizEndsAt, quizResult, submitQuiz]);
  async function openCompany(company: CompanyProfile) {
    try {
      const [detail, mappedProblems] = await Promise.all([
        api<CompanyDetail>("/companies/" + company.slug),
        api<Problem[]>("/companies/" + company.slug + "/problems"),
      ]);
      setSelectedCompany(detail);
      setCompanyProblems(mappedProblems);
    } catch (err) { setNotice(err instanceof Error ? err.message : "Unable to load company profile"); }
  }
  async function openCourse(course: Course) {
    try {
      const detail = await api<CourseDetail>("/courses/" + course.slug);
      setSelectedCourse(detail); setSelectedLesson(null);
    } catch (err) { setNotice(err instanceof Error ? err.message : "Unable to load course"); }
  }
  function backToCompanies() {
    setSelectedCompany(null);
    setCompanyProblems([]);
  }
  async function completeLesson() {
    if (!token || !selectedLesson) { setNotice("Sign in to save lesson completion."); return; }
    try {
      await api("/lessons/" + selectedLesson.id + "/complete", { method: "POST" }, token);
      const updated = await api<LearningProgress[]>("/learning-progress", {}, token);
      setLearningProgress(updated); setNotice("Lesson marked complete and saved to your profile.");
    } catch (err) { setNotice(err instanceof Error ? err.message : "Unable to save lesson progress"); }
  }

  async function generateStudyPlan(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setBusy(true); setNotice("");
    try {
      const generated = await api<{ id:number; title:string; task_count:number }>("/study-plan/generate", {
        method: "POST",
        body: JSON.stringify({
          duration_days: Number(planDuration),
          target_role: planRole,
          target_company: planCompany,
          daily_hours: Number(planHours),
          skill_level: planLevel,
          start_date: planStartDate,
        }),
      }, token);
      const [plan, allTasks] = await Promise.all([
        api<ActivePlan>("/study-plan/active", {}, token),
        api<Task[]>("/study-plan", {}, token),
      ]);
      setActivePlan(plan); setTasks(allTasks);
      setNotice("Created your " + planDuration + "-day plan with " + generated.task_count + " study tasks.");
    } catch (err) { setNotice(err instanceof Error ? err.message : "Unable to generate study plan"); }
    finally { setBusy(false); }
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
      setActivePlan(current => current ? {
        ...current,
        tasks: current.tasks.map(item => item.id === updated.id ? { ...item, is_completed: updated.is_completed } : item),
      } : current);
    } catch (err) { setNotice(err instanceof Error ? err.message : "Unable to update task"); }
  }
  async function adminAddCompanySource(event: FormEvent) {
    event.preventDefault();
    if (!token || !adminCompanyId) return;
    try {
      await api("/admin/companies/" + adminCompanyId + "/sources", {
        method: "POST",
        body: JSON.stringify({
          title: adminCompanySourceTitle,
          url: adminCompanySourceUrl,
          evidence_type: adminCompanySourceType,
          claim: adminCompanySourceClaim,
          confidence: adminCompanySourceConfidence,
        }),
      }, token);
      setNotice("Research source added. Review its claim and date before marking the employer profile verified.");
      setAdminCompanySourceTitle(""); setAdminCompanySourceUrl(""); setAdminCompanySourceClaim("");
      await api<CompanyProfile[]>("/companies").then(setCompanies);
    } catch (err) { setNotice(err instanceof Error ? err.message : "Unable to add research source"); }
  }
  async function adminReviewCompany(research_status: "pending" | "reviewed") {
    if (!token || !adminCompanyId) return;
    try {
      await api("/admin/companies/" + adminCompanyId + "/research-status", {
        method: "PATCH", body: JSON.stringify({ research_status }),
      }, token);
      setNotice(research_status === "reviewed" ? "Employer research marked reviewed with a verification timestamp." : "Employer research returned to pending.");
      await api<CompanyProfile[]>("/companies").then(setCompanies);
    } catch (err) { setNotice(err instanceof Error ? err.message : "Unable to update research status"); }
  }
  async function adminMapCompanyProblem(event: FormEvent) {
    event.preventDefault();
    if (!token || !adminMapCompanySlug || !adminMapProblemId) return;
    try {
      await api("/admin/companies/" + adminMapCompanySlug + "/problems/" + adminMapProblemId, { method: "POST" }, token);
      setNotice("Practice problem mapped to employer. This indicates curriculum relevance, not an interview-question attribution.");
      setAdminMapProblemId("");
    } catch (err) { setNotice(err instanceof Error ? err.message : "Unable to map practice problem"); }
  }
  async function adminCreateSqlChallenge(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    try {
      await api("/admin/sql/problems", {
        method: "POST",
        body: JSON.stringify({
          title: adminSqlTitle,
          slug: adminSqlSlug,
          prompt: adminSqlPrompt,
          topic: adminSqlTopic,
          difficulty: adminSqlDifficulty,
          reference_query: adminSqlReference,
          explanation: adminSqlExplanation,
          is_published: true,
        }),
      }, token);
      setNotice("SQL challenge created. Its reference query remains private to the server.");
      setAdminSqlTitle(""); setAdminSqlSlug(""); setAdminSqlPrompt(""); setAdminSqlReference(""); setAdminSqlExplanation("");
    } catch (err) { setNotice(err instanceof Error ? err.message : "Unable to create SQL challenge"); }
  }
  async function adminCreateQuizQuestion(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    const options = adminQuizOptions.split("\\n").map(option=>option.trim()).filter(Boolean);
    try {
      await api("/admin/quiz-questions", {
        method: "POST",
        body: JSON.stringify({
          category: adminQuizCategory,
          topic: adminQuizTopic,
          prompt: adminQuizPrompt,
          options,
          correct_index: Number(adminQuizCorrectIndex),
          explanation: adminQuizExplanation,
          difficulty: adminQuizDifficulty,
          is_published: true,
        }),
      }, token);
      setNotice("Assessment question created and answer key hidden from student APIs.");
      setAdminQuizPrompt(""); setAdminQuizOptions(""); setAdminQuizExplanation("");
    } catch (err) { setNotice(err instanceof Error ? err.message : "Unable to create assessment question"); }
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
          <Metric title="Current study streak" value={progress?.current_streak_days ?? "—"} note={progress ? "Best streak: " + progress.longest_streak_days + " days" : "Complete a lesson, quiz or task"} icon={<Flame size={17}/>}/>
        </section>
        <div className="section-head"><div><div className="eyebrow">YOUR WORKSPACE</div><h2>Pick up where you want to grow</h2><p>Choose an active tool. Planned curriculum is shown separately from working features.</p></div></div>
        <div className="quick-grid">
          <Quick title="DSA problem bank" detail="Search problems, open statements and submit solutions." icon={<Code2/>} onClick={() => setPage("practice")}/>
          <Quick title="SQL playground" detail="Run SELECT queries in an isolated read-only learning database." icon={<Database/>} onClick={() => setPage("sql")}/>
          <Quick title="Timed assessments" detail="Take Python, SQL, aptitude and Core CS quizzes." icon={<Activity/>} onClick={() => setPage("assessments")}/>
          <Quick title="Study planner" detail="Create personal tasks and track completion." icon={<Target/>} onClick={() => setPage("planner")}/>
        </div>
        <section className="readiness-panel"><div className="readiness-head"><div><div className="eyebrow">MEASURED PREPARATION</div><h3>Placement readiness index</h3></div><strong>{progress?.readiness_score === null || progress?.readiness_score === undefined ? "Building evidence" : progress.readiness_score + "/100"}</strong></div><p>{progress?.readiness_note || "Sign in to calculate progress from stored practice results."}</p>{progress?.readiness_score !== null && progress?.readiness_score !== undefined && <div className="readiness-track"><span style={{width:progress.readiness_score+"%"}}/></div>}</section>
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
        <div className="section-head"><div><div className="eyebrow">SQL WORKSPACE</div><h2>Practise relational queries</h2><p>Use the read-only sample database for exploration, or solve a challenge with server-side result checking.</p></div></div>
        {sqlProgress && <div className="sql-progress-strip"><b>{sqlProgress.solved_challenges}</b> solved <span>·</span> {sqlProgress.accepted_submissions} accepted submissions <span>·</span> {sqlProgress.total_submissions} attempts <span>·</span> {sqlProgress.acceptance_rate === null ? "No acceptance rate yet" : sqlProgress.acceptance_rate + "% accepted"}</div>}
        <div className="mode-tabs"><button className={sqlMode==="playground"?"mode-tab active":"mode-tab"} onClick={()=>setSqlMode("playground")}>SQL Playground</button><button className={sqlMode==="challenges"?"mode-tab active":"mode-tab"} onClick={()=>setSqlMode("challenges")}>SQL Challenges <span>{sqlChallenges.length}</span></button></div>
        {sqlMode === "playground" ? <>
          <div className="sql-layout"><div className="schema-panel"><h3>Available tables</h3><SchemaTable name="customers" columns="customer_id · name · city"/><SchemaTable name="orders" columns="order_id · customer_id · order_date · amount · status"/><SchemaTable name="employees" columns="employee_id · name · department_id · salary · joining_date"/><SchemaTable name="departments" columns="department_id · department_name"/></div>
            <div className="sql-editor-panel"><div className="editor-head"><div><Database size={15}/> SQL (SQLite)</div><span>Read-only session</span></div><Editor height="300px" language="sql" theme="vs-dark" value={sql} onChange={value=>setSql(value??"")} options={{fontSize:14,minimap:{enabled:false},automaticLayout:true,wordWrap:"on"}}/><div className="editor-actions"><button className="primary" onClick={executeSql} disabled={busy}><Play size={14}/> Run query</button><button className="secondary" onClick={()=>{setSql("SELECT * FROM customers;");setSqlResult(null);}}>Reset query</button></div></div>
          </div>
          {sqlResult && <div className="result-panel"><div className="result-head"><b>Query result</b><span>{sqlResult.row_count} rows returned{sqlResult.truncated?" · result truncated":""}</span></div><div className="table-scroll"><table><thead><tr>{sqlResult.columns.map(col=><th key={col}>{col}</th>)}</tr></thead><tbody>{sqlResult.rows.map((row,i)=><tr key={i}>{row.map((value,j)=><td key={j}>{value===null?"NULL":String(value)}</td>)}</tr>)}</tbody></table></div></div>}
        </> : <div className="sql-challenges-layout">
          <div className="sql-challenge-list">
            <div className="challenge-list-head"><b>Challenge bank</b><span>{sqlChallenges.length} tasks</span></div>
            {sqlChallenges.map(problem=><button key={problem.id} className={selectedSqlChallenge?.id===problem.id?"sql-challenge-row active":"sql-challenge-row"} onClick={()=>{setSelectedSqlChallenge(problem);setSqlChallengeResult(null);}}><span className="challenge-id">#{String(problem.id).padStart(2,"0")}</span><span className="challenge-title">{problem.title}<small>{problem.topic}</small></span><span className={"difficulty "+problem.difficulty}>{problem.difficulty}</span></button>)}
            {!sqlChallenges.length && <div className="empty-state">No SQL challenges loaded. Run python -m app.sql_seed in the backend folder.</div>}
          </div>
          <div className="sql-challenge-workspace">
            {selectedSqlChallenge ? <>
              <div className="sql-challenge-prompt"><div className="problem-title"><span className={"difficulty "+selectedSqlChallenge.difficulty}>{selectedSqlChallenge.difficulty}</span><span className="challenge-topic">{selectedSqlChallenge.topic}</span></div><h3>{selectedSqlChallenge.title}</h3><p>{selectedSqlChallenge.prompt}</p></div>
              <div className="schema-mini"><b>Available tables:</b> customers, orders, employees, departments</div>
              <div className="sql-editor-panel"><div className="editor-head"><div><Database size={15}/> SQL challenge editor</div><span>Reference query is server-side</span></div><Editor height="280px" language="sql" theme="vs-dark" value={sql} onChange={value=>setSql(value??"")} options={{fontSize:14,minimap:{enabled:false},automaticLayout:true,wordWrap:"on"}}/><div className="editor-actions"><button className="primary" onClick={submitSqlChallenge} disabled={busy}><Send size={14}/> Submit query</button><button className="secondary" onClick={()=>setSql("SELECT * FROM customers;")}>Reset editor</button></div></div>
              {sqlChallengeResult && <div className="result-panel"><div className="result-head"><b>Submission result</b><span className={sqlChallengeResult.verdict==="Accepted"?"passed":"failed"}>{sqlChallengeResult.verdict}</span></div>{sqlChallengeResult.error && <p className="sql-error">{sqlChallengeResult.error}</p>}{sqlChallengeResult.rows && <div className="table-scroll"><table><thead><tr>{sqlChallengeResult.columns?.map(col=><th key={col}>{col}</th>)}</tr></thead><tbody>{sqlChallengeResult.rows.map((row,i)=><tr key={i}>{row.map((value,j)=><td key={j}>{value===null?"NULL":String(value)}</td>)}</tr>)}</tbody></table></div>}{sqlChallengeResult.explanation && <p className="sql-explanation">{sqlChallengeResult.explanation}</p>}</div>}
            </> : <div className="empty-state">Choose a SQL challenge from the list to read its task.</div>}
          </div>
        </div>}
      </section>}

      {page === "assessments" && <section className="page-content">
        <div className="section-head"><div><div className="eyebrow">ASSESSMENT ENGINE</div><h2>Test what you know</h2><p>Quizzes are graded server-side. Sign in to save results to your account.</p></div></div>
        {!quizCategory ? <div className="category-grid">{categories.map(category=><button className="category-card" key={category.category} onClick={()=>loadQuiz(category.category)}><div className="track-icon mint"><BookOpen size={20}/></div><h3>{category.category.toUpperCase()}</h3><p>{category.question_count} published questions</p><span>Start assessment <ChevronRight size={15}/></span></button>)}
          {!categories.length && <div className="empty-state">No assessment questions have been published. Run the backend seeder to load starter quizzes.</div>}</div>
        : <div className="quiz-panel"><div className="quiz-top"><button className="back-link" onClick={()=>{setQuizCategory("");setQuestions([]);setQuizResult(null);setQuizSessionId(null);setQuizEndsAt(null);setQuizRemaining(null);}}>← All assessments</button><span>{quizCategory.toUpperCase()} · {questions.length} questions{quizSessionId !== null ? " · " + Math.floor((quizRemaining ?? 0)/60).toString().padStart(2,"0") + ":" + ((quizRemaining ?? 0)%60).toString().padStart(2,"0") + " remaining" : ""}</span></div>
          {questions.map((question,index)=><article className="question-card" key={question.id}><div className="question-meta">QUESTION {index+1} · {question.topic} · {question.difficulty}</div><h3>{question.prompt}</h3><div className="option-list">{question.options.map((option,optionIndex)=><label className={answers[question.id]===optionIndex?"option selected":"option"} key={optionIndex}><input type="radio" name={String(question.id)} checked={answers[question.id]===optionIndex} onChange={()=>setAnswers(current=>({...current,[question.id]:optionIndex}))}/><span>{String.fromCharCode(65+optionIndex)}.</span>{option}</label>)}</div>
            {quizResult && <div className={quizResult.results.find(r=>r.question_id===question.id)?.correct?"explanation good":"explanation bad"}>{quizResult.results.find(r=>r.question_id===question.id)?.correct?"Correct":"Review"} — {quizResult.results.find(r=>r.question_id===question.id)?.explanation}</div>}</article>)}
          {quizResult ? <div className="score-card"><Trophy size={23}/><b>{quizResult.score} / {quizResult.total}</b><span>{quizResult.percentage}% score</span></div> : <button className="primary" onClick={() => submitQuiz(false)} disabled={!questions.length || busy || quizSessionId === null}>Submit assessment</button>}
        </div>}
      </section>}

      {page === "planner" && <section className="page-content">
        <div className="section-head"><div><div className="eyebrow">PERSONALIZED PREPARATION</div><h2>Build your placement plan</h2><p>Generate an adaptable 30, 45 or 60-day plan using your target role, daily availability and current level. You can still add your own tasks.</p></div></div>
        <form className="plan-generator" onSubmit={generateStudyPlan}>
          <label>Plan duration<select value={planDuration} onChange={e=>setPlanDuration(e.target.value)}><option value="30">30 days</option><option value="45">45 days</option><option value="60">60 days</option></select></label>
          <label>Target role<select value={planRole} onChange={e=>setPlanRole(e.target.value)}><option value="general">General fresher placements</option><option value="software_engineer">Software Engineer</option><option value="data_engineer">Data Engineer</option><option value="ai_ml">AI / ML Engineer</option></select></label>
          <label>Target company (optional)<input value={planCompany} onChange={e=>setPlanCompany(e.target.value)} placeholder="e.g. TCS, Accenture, Amazon"/></label>
          <label>Hours per day<select value={planHours} onChange={e=>setPlanHours(e.target.value)}>{[1,2,3,4,5,6,8,10,12].map(value=><option key={value} value={value}>{value} hours</option>)}</select></label>
          <label>Current level<select value={planLevel} onChange={e=>setPlanLevel(e.target.value)}><option value="beginner">Beginner</option><option value="intermediate">Intermediate</option></select></label>
          <label>Start date<input type="date" value={planStartDate} onChange={e=>setPlanStartDate(e.target.value)} required/></label>
          <button className="primary plan-submit" disabled={busy}>Generate my study plan</button>
        </form>
        {activePlan && <section className="active-plan">
          <div className="active-plan-head"><div><div className="eyebrow">ACTIVE PLAN</div><h3>{activePlan.title}</h3><p>{activePlan.duration_days} days · {activePlan.daily_hours} hours/day · {activePlan.skill_level} · Starts {activePlan.start_date}{activePlan.target_company ? " · " + activePlan.target_company : ""}</p></div><span className="plan-count">{activePlan.tasks.filter(task=>task.is_completed).length}/{activePlan.tasks.length} complete</span></div>
          <div className="plan-progress"><span style={{width:(activePlan.tasks.length ? activePlan.tasks.filter(task=>task.is_completed).length/activePlan.tasks.length*100 : 0)+"%"}}/></div>
          <div className="plan-task-list">{activePlan.tasks.map(task=><label key={task.id} className={task.is_completed?"plan-task completed":"plan-task"}>
            <input type="checkbox" checked={task.is_completed} onChange={()=>toggleTask(task)}/>
            <span className="plan-day">DAY {task.day_number}</span>
            <span className="plan-task-content"><b>{task.title.replace(/^Day \\d+: /,"")}</b><small>{task.category} · {task.due_date || ""} · {task.estimated_minutes || 30} min</small>{task.description && <small>{task.description}</small>}</span>
            <CheckCircle2 size={17}/>
          </label>)}</div>
        </section>}
        <div className="manual-task-heading"><div><h3>Additional personal tasks</h3><p>Add revision, applications or interview-preparation work.</p></div></div>
        <form className="task-form" onSubmit={addTask}><input value={taskTitle} onChange={e=>setTaskTitle(e.target.value)} placeholder="Add a study task…" minLength={2} required/><select value={taskCategory} onChange={e=>setTaskCategory(e.target.value)}><option>DSA</option><option>Python</option><option>SQL</option><option>Aptitude</option><option>Core CS</option><option>Data Engineering</option><option>AI / ML</option></select><button className="primary">Add task</button></form>
        <div className="task-list">{tasks.filter(task=>!task.plan_id).map(task=><label key={task.id} className={task.is_completed?"task completed":"task"}><input type="checkbox" checked={task.is_completed} onChange={()=>toggleTask(task)}/><span>{task.title}<small>{task.category}{task.due_date ? " · Due " + task.due_date : ""}</small></span><CheckCircle2 size={17}/></label>)}
          {!tasks.some(task=>!task.plan_id) && <div className="empty-state">No additional tasks yet. Your generated plan tasks appear above.</div>}</div>
      </section>}

      {page === "companies" && <section className="page-content">
        {!selectedCompany ? <>
          <div className="section-head"><div><div className="eyebrow">EMPLOYER DIRECTORY</div><h2>Prepare with company context</h2><p>Official career portals are starting points. Assessment formats, eligibility and question patterns are shown only after dated evidence is reviewed.</p></div></div>
          <div className="company-filters"><label className="search"><Search size={16}/><input placeholder="Search employers" value={companySearch} onChange={e=>setCompanySearch(e.target.value)}/></label><select value={companyCategory} onChange={e=>setCompanyCategory(e.target.value)}><option value="">All employer types</option><option value="service">Service companies</option><option value="technology-services">Technology services</option><option value="professional-services">Professional services</option><option value="product">Product companies</option></select></div>
          <div className="company-grid">{companies.map(company=><article className="company-card" key={company.id}>
            <div className="company-card-top"><span className="company-monogram">{company.name.split(/\\s+/).map(part=>part[0]).slice(0,2).join("").toUpperCase()}</span><span className="research-state pending">{company.research_status.replaceAll("_"," ")}</span></div>
            <h3>{company.name}</h3><p>{company.description}</p>
            <div className="company-tags">{company.hiring_tracks.map(track=><span key={track}>{track}</span>)}</div>
            <div className="company-card-actions"><button className="secondary" onClick={()=>openCompany(company)}>Preparation profile</button><a href={company.career_url} target="_blank" rel="noreferrer">Careers site ↗</a></div>
          </article>)}</div>
          {!companies.length && <div className="empty-state">No companies match this filter. Run python -m app.company_seed in the backend folder.</div>}
        </> : <>
          <button className="back-link" onClick={backToCompanies}>← All companies</button>
          <div className="company-detail-head"><div><div className="eyebrow">COMPANY PREPARATION PROFILE</div><h2>{selectedCompany.name}</h2><p>{selectedCompany.description}</p></div><a className="primary career-link" href={selectedCompany.career_url} target="_blank" rel="noreferrer">Open official careers site ↗</a></div>
          <div className="company-research-grid">
            <article className="company-research-card"><div className="eyebrow">RESEARCH STATUS</div><h3>{selectedCompany.research_status.replaceAll("_"," ")}</h3><p>{selectedCompany.last_verified_at ? "Last verified " + new Date(selectedCompany.last_verified_at).toLocaleDateString() : "Eligibility and assessment-pattern research has not yet been verified for a current hiring cycle."}</p><div className="notice info">A careers portal is not proof of an active vacancy or a verified assessment pattern. Check the specific official job description.</div></article>
            <article className="company-research-card"><div className="eyebrow">RESEARCH SOURCES</div><h3>{selectedCompany.research_sources.length} evidence records</h3>
              {selectedCompany.research_sources.length ? selectedCompany.research_sources.map(source=><div className="evidence-row" key={source.id}><a href={source.url} target="_blank" rel="noreferrer">{source.title} ↗</a><span>{source.evidence_type} · {source.confidence} confidence · {new Date(source.checked_at).toLocaleDateString()}</span><p>{source.claim}</p></div>) : <p>No reviewed research sources yet. Assessment pattern and eligibility claims remain unverified.</p>}
            </article>
          </div>
          <article className="company-problems-panel"><div><div className="eyebrow">MAPPED PRACTICE PROBLEMS</div><h3>Company-tagged DSA practice</h3><p>Only problems explicitly mapped by an administrator appear here. Mapping means practice relevance, not a claim that a question was asked in an interview.</p></div>
            {companyProblems.length ? companyProblems.map(problem=><button key={problem.id} className="problem-row" onClick={()=>{setSearch(problem.title);setSelected(null);setPage("practice");}}><span className="problem-name">{problem.title}<small>{problem.slug}</small></span><span className={"difficulty "+problem.difficulty}>{problem.difficulty}</span><ChevronRight size={16}/></button>) : <div className="empty-state">No DSA problems are mapped to this employer yet.</div>}
          </article>
        </>}
      </section>}

      {page === "curriculum" && <section className="page-content">
        {!selectedCourse ? <>
          <div className="section-head"><div><div className="eyebrow">LEARNING LIBRARY</div><h2>Structured courses</h2><p>Original lessons with saved completion progress. Course coverage will expand as more validated content is added.</p></div></div>
          <div className="course-grid">{courses.map(course => {
            const progress = learningProgress.find(item => item.course_id === course.id);
            return <button className="course-card" key={course.id} onClick={() => openCourse(course)}>
              <div className="course-top"><span className="track-icon mint"><BookOpen size={20}/></span><span className="difficulty easy">{course.difficulty}</span></div>
              <h3>{course.title}</h3><p>{course.description}</p>
              <div className="course-progress"><span>{progress ? progress.completed_lessons + " / " + progress.total_lessons + " lessons completed" : course.lesson_count + " lessons"}</span><b>{progress ? progress.percentage + "%" : "Start"}</b></div>
              <div className="progress-track"><span style={{width:(progress?.percentage ?? 0)+"%"}}/></div>
            </button>;
          })}</div>
          {!courses.length && <div className="empty-state">No published courses found. Run python -m app.curriculum_seed from the backend folder.</div>}
          <div className="notice info">Company-specific exam formats remain research-pending. Practice items are not labelled as actual company interview questions.</div>
        </> : !selectedLesson ? <>
          <button className="back-link" onClick={() => {setSelectedCourse(null);setSelectedLesson(null);}}>← All courses</button>
          <div className="section-head"><div><div className="eyebrow">{selectedCourse.category.toUpperCase()} COURSE</div><h2>{selectedCourse.title}</h2><p>{selectedCourse.description}</p></div></div>
          <div className="lesson-list">{selectedCourse.lessons.map(lesson => <button className="lesson-row" key={lesson.id} onClick={() => setSelectedLesson(lesson)}><span className="lesson-number">{String(lesson.display_order).padStart(2,"0")}</span><span className="lesson-name">{lesson.title}<small>{lesson.estimated_minutes} min lesson</small></span><ChevronRight size={17}/></button>)}</div>
        </> : <>
          <button className="back-link" onClick={() => setSelectedLesson(null)}>← {selectedCourse.title}</button>
          <article className="lesson-view"><div className="lesson-kicker">{selectedCourse.category.toUpperCase()} · LESSON {selectedLesson.display_order} · {selectedLesson.estimated_minutes} MIN</div><h2>{selectedLesson.title}</h2>
            <div className="markdown-content"><ReactMarkdown>{selectedLesson.content}</ReactMarkdown></div>
            <div className="lesson-complete"><p>Finish the explanation and attempt the practice prompts before marking this lesson complete.</p><button className="primary" onClick={completeLesson}><CheckCircle2 size={15}/> Mark lesson complete</button></div>
          </article>
        </>}
      </section>}

      {page === "admin" && user.role === "admin" && <section className="page-content">
        <div className="section-head"><div><div className="eyebrow">CONTENT MANAGEMENT</div><h2>Admin workspace</h2><p>Create curriculum topics, draft problems, add hidden test cases and publish reviewed content.</p></div></div>
        <div className="admin-grid">
          <form className="admin-form" onSubmit={adminCreateTopic}><h3>Create topic</h3><label>Topic name<input value={adminTopicName} onChange={e=>setAdminTopicName(e.target.value)} required/></label><label>URL slug<input value={adminTopicSlug} onChange={e=>setAdminTopicSlug(e.target.value)} placeholder="arrays-basics" required/></label><button className="primary">Create topic</button></form>
          <form className="admin-form" onSubmit={adminCreateProblem}><h3>Create problem draft</h3><label>Title<input value={adminProblemTitle} onChange={e=>setAdminProblemTitle(e.target.value)} required/></label><label>Slug<input value={adminProblemSlug} onChange={e=>setAdminProblemSlug(e.target.value)} placeholder="my-practice-problem" required/></label><label>Difficulty<select value={adminProblemDifficulty} onChange={e=>setAdminProblemDifficulty(e.target.value)}><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label><label>Topic ID (optional)<input type="number" min="1" value={adminProblemTopicId} onChange={e=>setAdminProblemTopicId(e.target.value)}/></label><label>Problem statement<textarea value={adminProblemStatement} onChange={e=>setAdminProblemStatement(e.target.value)} required/></label><label>Public sample input<textarea value={adminSampleInput} onChange={e=>setAdminSampleInput(e.target.value)} required/></label><label>Public sample expected output<textarea value={adminSampleOutput} onChange={e=>setAdminSampleOutput(e.target.value)} required/></label><button className="primary">Create draft</button></form>
          <form className="admin-form" onSubmit={adminAddTestCase}><h3>Add hidden test case</h3><label>Problem ID<input type="number" min="1" value={adminProblemId} onChange={e=>setAdminProblemId(e.target.value)} required/></label><label>Standard input<textarea value={adminTestInput} onChange={e=>setAdminTestInput(e.target.value)} required/></label><label>Expected output<textarea value={adminTestOutput} onChange={e=>setAdminTestOutput(e.target.value)} required/></label><label className="check-label"><input type="checkbox" checked={adminTestIsSample} onChange={e=>setAdminTestIsSample(e.target.checked)}/> Mark as public sample (leave unchecked for hidden test)</label><button className="primary">Add test case</button></form>
          <form className="admin-form" onSubmit={e=>{e.preventDefault();adminPublish(adminProblemId,true);}}><h3>Publish reviewed problem</h3><label>Problem ID<input type="number" min="1" value={adminProblemId} onChange={e=>setAdminProblemId(e.target.value)} required/></label><p className="muted">Only publish after validating the statement, public samples and server-side test cases.</p><button className="primary">Publish problem</button><button type="button" className="secondary" onClick={()=>adminPublish(adminProblemId,false)}>Unpublish</button></form>
        </div>
        <div className="admin-research-grid">
          <form className="admin-form" onSubmit={adminAddCompanySource}>
            <h3>Maintain employer research</h3>
            <label>Company<select value={adminCompanyId} onChange={e=>setAdminCompanyId(e.target.value)} required><option value="">Select employer</option>{companies.map(company=><option key={company.id} value={company.id}>{company.name}</option>)}</select></label>
            <label>Source title<input value={adminCompanySourceTitle} onChange={e=>setAdminCompanySourceTitle(e.target.value)} required/></label>
            <label>Official source URL<input type="url" value={adminCompanySourceUrl} onChange={e=>setAdminCompanySourceUrl(e.target.value)} placeholder="https://…" required/></label>
            <label>Evidence type<select value={adminCompanySourceType} onChange={e=>setAdminCompanySourceType(e.target.value)}><option value="official">Official employer source</option><option value="candidate_report">Candidate-reported</option><option value="practice_pattern">Common practice pattern</option><option value="original_problem">Original platform exercise</option></select></label>
            <label>Specific supported claim<textarea value={adminCompanySourceClaim} onChange={e=>setAdminCompanySourceClaim(e.target.value)} placeholder="Record only what this source explicitly supports." required/></label>
            <label>Confidence<select value={adminCompanySourceConfidence} onChange={e=>setAdminCompanySourceConfidence(e.target.value)}><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select></label>
            <button className="primary">Add research source</button>
            <button type="button" className="secondary" onClick={()=>adminReviewCompany("reviewed")} disabled={!adminCompanyId}>Mark reviewed</button>
            <button type="button" className="secondary" onClick={()=>adminReviewCompany("pending")} disabled={!adminCompanyId}>Return to pending</button>
          </form>
          <form className="admin-form" onSubmit={adminMapCompanyProblem}>
            <h3>Map a practice problem to a company</h3>
            <label>Company<select value={adminMapCompanySlug} onChange={e=>setAdminMapCompanySlug(e.target.value)} required><option value="">Select employer</option>{companies.map(company=><option key={company.slug} value={company.slug}>{company.name}</option>)}</select></label>
            <label>Problem ID<input type="number" min="1" value={adminMapProblemId} onChange={e=>setAdminMapProblemId(e.target.value)} required/></label>
            <p className="muted">Mapping means the problem is relevant practice for a role or skill area. It does not claim that the problem was asked in a real company assessment.</p>
            <button className="primary">Map practice problem</button>
          </form>
        </div>
        <div className="admin-authoring-grid">
          <form className="admin-form" onSubmit={adminCreateSqlChallenge}>
            <h3>Create SQL challenge</h3>
            <label>Title<input value={adminSqlTitle} onChange={e=>setAdminSqlTitle(e.target.value)} required minLength={3}/></label>
            <label>Slug<input value={adminSqlSlug} onChange={e=>setAdminSqlSlug(e.target.value)} placeholder="e.g. top-customers-by-revenue" required pattern="[a-z0-9]+(-[a-z0-9]+)*"/></label>
            <label>Task prompt<textarea value={adminSqlPrompt} onChange={e=>setAdminSqlPrompt(e.target.value)} required minLength={10}/></label>
            <label>Topic<input value={adminSqlTopic} onChange={e=>setAdminSqlTopic(e.target.value)} required/></label>
            <label>Difficulty<select value={adminSqlDifficulty} onChange={e=>setAdminSqlDifficulty(e.target.value)}><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label>
            <label>Private reference query<textarea value={adminSqlReference} onChange={e=>setAdminSqlReference(e.target.value)} required placeholder="SELECT ..."/></label>
            <label>Explanation<textarea value={adminSqlExplanation} onChange={e=>setAdminSqlExplanation(e.target.value)}/></label>
            <button className="primary">Create SQL challenge</button>
          </form>
          <form className="admin-form" onSubmit={adminCreateQuizQuestion}>
            <h3>Create assessment question</h3>
            <label>Category<input value={adminQuizCategory} onChange={e=>setAdminQuizCategory(e.target.value)} required/></label>
            <label>Topic<input value={adminQuizTopic} onChange={e=>setAdminQuizTopic(e.target.value)} required/></label>
            <label>Question<textarea value={adminQuizPrompt} onChange={e=>setAdminQuizPrompt(e.target.value)} required minLength={8}/></label>
            <label>Options (one per line)<textarea value={adminQuizOptions} onChange={e=>setAdminQuizOptions(e.target.value)} required placeholder={"Option A\\nOption B\\nOption C"}/></label>
            <label>Correct option index (zero-based)<input type="number" min="0" max="5" value={adminQuizCorrectIndex} onChange={e=>setAdminQuizCorrectIndex(e.target.value)} required/></label>
            <label>Explanation<textarea value={adminQuizExplanation} onChange={e=>setAdminQuizExplanation(e.target.value)} required/></label>
            <label>Difficulty<select value={adminQuizDifficulty} onChange={e=>setAdminQuizDifficulty(e.target.value)}><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label>
            <button className="primary">Create assessment question</button>
          </form>
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
