import { useMemo, useState } from "react";
import {
  Activity, BookOpen, BrainCircuit, BriefcaseBusiness, CheckCircle2,
  ChevronRight, Code2, Database, Flame, GraduationCap, LayoutDashboard,
  Search, Target, Trophy, Zap,
} from "lucide-react";

const tracks = [
  { name: "Python Fundamentals", detail: "Build strong programming foundations", icon: Code2, count: "33 topics", tone: "amber" },
  { name: "Data Structures & Algorithms", detail: "Patterns from beginner to interview level", icon: BrainCircuit, count: "200 target problems", tone: "mint" },
  { name: "SQL & DBMS", detail: "Queries, joins, CTEs and window functions", icon: Database, count: "100 target questions", tone: "blue" },
  { name: "Aptitude & Reasoning", detail: "Quantitative, logical and verbal practice", icon: Target, count: "Coming next", tone: "violet" },
];

const nav = [
  ["Overview", LayoutDashboard], ["Learn", BookOpen], ["Practice", Code2],
  ["Assessments", Activity], ["Career tracks", BriefcaseBusiness],
] as const;

export default function App() {
  const [active, setActive] = useState("Overview");
  const [query, setQuery] = useState("");
  const shownTracks = useMemo(
    () => tracks.filter((track) => (track.name + track.detail).toLowerCase().includes(query.toLowerCase())),
    [query],
  );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">P</span><span>Placement<span className="brand-muted">OS</span></span></div>
        <div className="side-label">WORKSPACE</div>
        <nav>{nav.map(([label, Icon]) => (
          <button className={active === label ? "nav-item active" : "nav-item"} key={label} onClick={() => setActive(label)}>
            <Icon size={18}/><span>{label}</span>{active === label && <span className="nav-dot"/>}
          </button>
        ))}</nav>
        <div className="sidebar-bottom">
          <div className="goal-card"><div className="goal-icon"><GraduationCap size={18}/></div><b>2027 placement goal</b><p>Make every practice session count.</p><div className="goal-line"><span/></div><small>Preparation foundation</small></div>
          <div className="profile"><div className="avatar">RR</div><div><b>Ritik Raushan</b><small>Engineering student</small></div></div>
        </div>
      </aside>
      <main className="main">
        <header className="topbar"><div><span className="crumb">Workspace</span><ChevronRight size={14}/><b>{active}</b></div><div className="top-actions"><span className="status"><i/> Development build</span><button className="avatar small">RR</button></div></header>
        <section className="welcome"><div><div className="eyebrow"><Zap size={14}/> YOUR PLACEMENT WORKSPACE</div><h1>Build skills. <em>Prove them.</em></h1><p>A focused space to learn, practise and measure your progress — one problem at a time.</p></div><div className="welcome-orbit"><div className="orbit-ring ring-one"/><div className="orbit-ring ring-two"/><div className="orbit-core"><GraduationCap size={33}/></div><span className="orbit-chip chip-one"><Code2 size={15}/> DSA</span><span className="orbit-chip chip-two"><Database size={15}/> SQL</span><span className="orbit-chip chip-three"><BrainCircuit size={15}/> Python</span></div></section>
        <section className="metric-grid">
          <article className="metric"><div className="metric-top"><span>Learning tracks</span><BookOpen size={17}/></div><strong>4</strong><small>Foundation modules listed</small></article>
          <article className="metric"><div className="metric-top"><span>DSA problem target</span><Code2 size={17}/></div><strong>200</strong><small>Curated bank planned</small></article>
          <article className="metric"><div className="metric-top"><span>SQL question target</span><Database size={17}/></div><strong>100</strong><small>Practice bank planned</small></article>
          <article className="metric"><div className="metric-top"><span>Study streak</span><Flame size={17}/></div><strong>—</strong><small>Starts after tracked activity</small></article>
        </section>
        <section className="section-head"><div><div className="eyebrow">YOUR CURRICULUM</div><h2>Choose what to work on</h2><p>Start with the foundations. Advanced tracks will unlock as content is validated.</p></div><label className="search"><Search size={16}/><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Find a learning track"/></label></section>
        <section className="track-grid">{shownTracks.map(({name, detail, icon: Icon, count, tone}, index) => <article className="track-card" key={name}><div className={"track-icon " + tone}><Icon size={21}/></div><div className="track-index">0{index+1}</div><h3>{name}</h3><p>{detail}</p><div className="track-footer"><span>{count}</span><button aria-label={"Open " + name} onClick={() => setActive("Learn")}><ChevronRight size={18}/></button></div></article>)}</section>
        <section className="bottom-grid"><article className="panel"><div className="panel-heading"><div><div className="eyebrow">PREPARATION PRINCIPLE</div><h3>Consistency over cramming.</h3></div><Trophy size={20}/></div><p>Work through a topic, solve problems independently, and use timed assessments to check whether the skill is sticking.</p><div className="principle-row"><CheckCircle2 size={17}/><span>Progress should be based on demonstrated performance, not page visits.</span></div></article><article className="panel career"><div className="eyebrow">TARGET OUTCOME</div><h3>Ready for the right opportunity.</h3><p>Prepare for service companies, product teams and specialist fresher roles with evidence-backed practice paths.</p><div className="career-tags"><span>Mass hiring</span><span>Data Engineering</span><span>AI / ML</span></div></article></section>
        <footer><span>PlacementOS <b>•</b> Foundation release</span><span><Activity size={13}/> Learning progress will appear after assessments are implemented.</span></footer>
      </main>
    </div>
  );
}
