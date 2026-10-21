type FileRecord = { id: string; name: string; size: number };
type Message = { role: 'assistant' | 'user'; text: string };
type Status = 'ready' | 'running' | 'paused' | 'failed' | 'complete';
type Project = {
  id: string;
  app: string;
  goal: string;
  kind: string;
  sample: boolean;
  completed: number;
  phase: number;
  status: Status;
  started: number;
  elapsed: number;
  scopePending?: boolean;
  created: number;
  files: FileRecord[];
  link: string;
  messages: Message[];
};
type Receipt = {
  id: string;
  projectId: string;
  app: string;
  phase: number;
  price: number;
  date: number;
  refunded: boolean;
};
type State = {
  version: number;
  profile: { name: string; email: string } | null;
  projects: Project[];
  receipts: Receipt[];
  dark: boolean;
};
const STORE = 'rea-prototype-v1';
const phases = ['Initial assessment', 'Investigation', 'Deliverables', 'Validation'];
const prices = [0, 49, 79, 29];
const durations = [9000, 16000, 16000, 12000];
const activities = [
  ['Identifying the target', 'Mapping available information', 'Preparing findings and a proposed scope'],
  ['Restoring the project workspace', 'Tracing the selected workflow', 'Collecting evidence and documenting gaps'],
  ['Reviewing investigation findings', 'Building the scoped deliverable', 'Packaging the report and evidence'],
  ['Checking the agreed criteria', 'Reviewing evidence and limitations', 'Preparing the final handoff'],
];
const paths: Record<string, string> = {
  dashboard:
    '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  projects: '<path d="M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>',
  billing: '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="M3 10h18M7 15h3"/>',
  settings: '<path d="m10 3-1 3-3 1-3 3v4l3 3 3 1 1 3h4l1-3 3-1 3-3v-4l-3-3-3-1-1-3Z"/><circle cx="12" cy="12" r="3"/>',
  arrow: '<path d="M4 12h16m-6-6 6 6-6 6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
  chevron: '<path d="m9 5 7 7-7 7"/>',
  down: '<path d="m6 9 6 6 6-6"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  file: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 13h8M8 17h5"/>',
  shield: '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6Z"/><path d="m8 12 3 3 5-6"/>',
  spark: '<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z"/>',
  chat: '<path d="M21 11.5a8.5 8.5 0 0 1-8.5 8.5H3l2-5a8.5 8.5 0 1 1 16-3.5Z"/><path d="M8 10h8M8 14h5"/>',
  close: '<path d="m6 6 12 12M6 18 18 6"/>',
  send: '<path d="m3 10 18-7-7 18-3-8Zm8 3L21 3"/>',
  link: '<path d="m10 13 4-4m-6 6-2 2a4 4 0 0 1-6-6l5-5a4 4 0 0 1 6 0m2 3 2-2a4 4 0 0 1 6 6l-5 5a4 4 0 0 1-6 0" transform="translate(1 0)"/>',
  upload: '<path d="M12 16V3m-5 5 5-5 5 5M4 15v5h16v-5"/>',
  lock: '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
  download: '<path d="M12 3v13m-5-5 5 5 5-5M4 17v4h16v-4"/>',
  globe: '<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/>',
  code: '<path d="m8 7-5 5 5 5m8-10 5 5-5 5m-5 2 2-14"/>',
  moon: '<path d="M20 15A9 9 0 0 1 9 4a9 9 0 1 0 11 11Z"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  pause: '<path d="M8 5v14M16 5v14"/>',
  play: '<path d="m7 4 14 8-14 8Z"/>',
  help: '<circle cx="12" cy="12" r="9"/><path d="M9 9a3 3 0 0 1 6 0c0 2-3 2-3 4m0 3h.01"/>',
  trash: '<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7"/>',
};
export const icon = (name: string, cls = '') =>
  `<svg class="icon ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.file}</svg>`;
export const esc = (v: unknown) =>
  String(v ?? '').replace(
    /[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] || c
  );
const uid = () => crypto.randomUUID();
const date = (v: number) => new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
const money = (v: number) => `$${v.toFixed(2)}`;
export const button = (text: string, action: string, cls = 'primary', extra = '') =>
  `<button class="button ${cls}" data-action="${action}" ${extra}>${text}</button>`;
export const badge = (text: string, cls = '') => `<span class="badge ${cls}">${text}</span>`;
const appMark = (p: Project, large = false) =>
  `<span class="app-mark ${p.sample ? 'instagram' : 'generic'} ${large ? 'large' : ''}">${p.sample ? '<span class="camera-mark"></span>' : icon('code')}</span>`;

function seed(): State {
  return {
    version: 1,
    profile: null,
    dark: false,
    receipts: [],
    projects: [
      {
        id: 'instagram-example',
        app: 'Instagram',
        kind: 'Android application',
        sample: true,
        goal: 'Map the Reel publishing workflow and document the underlying API.',
        completed: 0,
        phase: 1,
        status: 'ready',
        started: 0,
        elapsed: 0,
        created: Date.now(),
        files: [],
        link: '',
        messages: [
          {
            role: 'assistant',
            text: 'Your initial assessment is ready. Explore the sample findings, review the proposed investigation, or tell me what you’d like to focus on. This is an interactive demo; no application has been analyzed.',
          },
        ],
      },
    ],
  };
}

export function startWorkspace() {
  let state: State;
  let storageAvailable = true;
  try {
    const raw = localStorage.getItem(STORE);
    state = raw ? JSON.parse(raw) : seed();
    if (state.version !== 1 || !Array.isArray(state.projects)) state = seed();
  } catch {
    state = seed();
    storageAvailable = false;
  }
  let page = 'dashboard';
  let activeId = state.projects[0]?.id || '';
  let tab = 'overview';
  let chatOpen = !window.matchMedia('(max-width: 760px)').matches;
  let search = '';
  let draft = { app: '', goal: '' };
  const app = document.querySelector<HTMLDivElement>('#app')!;
  const modalRoot = document.querySelector<HTMLDivElement>('#modal-root')!;
  let toastTimer: ReturnType<typeof setTimeout>;
  let visibleStep = '';

  function save() {
    try {
      localStorage.setItem(STORE, JSON.stringify(state));
    } catch {
      storageAvailable = false;
      toast('Browser storage is unavailable. Changes will last for this visit only.');
    }
  }
  function toast(text: string) {
    const el = document.querySelector<HTMLDivElement>('#toast')!;
    el.textContent = text;
    el.classList.add('visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove('visible'), 4000);
  }
  const project = () => state.projects.find((p) => p.id === activeId);
  const statusText = (p: Project) =>
    p.status === 'ready'
      ? p.completed > 0
        ? 'Phase delivered'
        : 'Assessment ready'
      : { running: 'In progress', paused: 'Paused', failed: 'Needs attention', complete: 'Completed' }[p.status];
  function navigate(next: string, id?: string) {
    page = next;
    if (id) activeId = id;
    tab = 'overview';
    search = '';
    history.replaceState(null, '', `#${next}${next === 'workspace' ? '/' + activeId : ''}`);
    render();
    window.scrollTo({ top: 0 });
    document.querySelector<HTMLElement>('#main h1')?.focus();
  }
  function parseRoute() {
    const [route, id] = location.hash.slice(1).split('/');
    if (['dashboard', 'projects', 'billing', 'settings', 'workspace'].includes(route)) page = route;
    if (id && state.projects.some((p) => p.id === id)) activeId = id;
    if (page === 'workspace' && !project()) page = 'projects';
  }
  function shell(content: string) {
    const nav = [
      ['dashboard', 'Dashboard'],
      ['projects', 'Projects'],
      ['billing', 'Billing'],
      ['settings', 'Settings'],
    ];
    return `<aside class="sidebar" aria-label="Main navigation" ${window.matchMedia('(max-width: 760px)').matches && !document.body.classList.contains('nav-open') ? 'inert' : ''}>
      <a class="brand" href="#dashboard"><img src="/rea.svg" width="35" height="35" alt=""/><span>Reverse Engineer<span class="brand-sub">Anything</span></span></a>
      <div class="workspace-switch">${icon('projects')}<span>Personal workspace</span>${badge('DEMO')}</div>
      <span class="nav-label">WORKSPACE</span><nav>${nav.map(([key, label]) => `<a class="nav-item ${page === key || (key === 'projects' && page === 'workspace') ? 'active' : ''}" href="#${key}" ${page === key || (key === 'projects' && page === 'workspace') ? 'aria-current="page"' : ''}>${icon(key)}<span>${label}</span>${key === 'projects' ? `<span class="nav-count">${state.projects.length}</span>` : ''}</a>`).join('')}</nav>
      <div class="sidebar-bottom"><div class="small-note">${icon('spark')}<div><strong>From curiosity to clarity.</strong><p>Understand what’s underneath.</p></div></div><button class="nav-item" data-action="help">${icon('help')}<span>Prototype guide</span>${icon('arrow')}</button><button class="profile" data-action="profile"><span class="avatar">${esc(
        (state.profile?.name || 'Demo user')
          .split(' ')
          .map((n) => n[0])
          .slice(0, 2)
          .join('')
      )}</span><span><strong>${esc(state.profile?.name || 'Demo workspace')}</strong><small>Personal account</small></span>${icon('down')}</button></div>
    </aside><div class="mobile-backdrop" data-action="mobile-close"></div><div class="app-shell ${page === 'workspace' ? 'workspace-shell' : ''}">
      <header class="topbar"><div class="breadcrumbs"><button class="icon-button mobile-menu" aria-label="Open navigation" data-action="mobile">${icon('menu')}</button><span class="crumb-root">Workspace</span>${icon('chevron')}<span>${page === 'workspace' ? esc(project()?.app) : page[0].toUpperCase() + page.slice(1)}</span></div><div class="topbar-right"><span class="demo-indicator"><i></i> Interactive prototype</span><button class="icon-button" data-action="theme" aria-label="Toggle color theme">${icon('moon')}</button><button class="mini-avatar" data-action="profile" aria-label="Account settings">${esc((state.profile?.name || 'D')[0])}</button></div></header>
      <main id="main" class="${page === 'workspace' ? 'workspace-main' : 'page-main'}">${content}</main><footer class="app-footer"><span>Built with AstroWind <span>·</span> Demo data stays in this browser</span><span>REA / WORKSPACE <span>v0.1</span></span></footer></div>`;
  }
  function projectRow(p: Project) {
    return `<button class="project-row" data-action="open" data-id="${p.id}">${appMark(p)}<span class="project-name"><strong>${esc(p.app)}</strong><small>${esc(p.goal)}</small></span><span class="row-phase">${phases[Math.min(p.phase, 3)]}</span>${badge(statusText(p), p.status === 'running' ? 'blue' : p.status === 'failed' ? 'amber' : 'green')}<span class="row-date">${date(p.created)}</span>${icon('arrow')}</button>`;
  }
  function dashboard() {
    const p = project();
    return `<div class="page-heading"><div><div class="eyebrow">YOUR WORKSPACE</div><h1 tabindex="-1">A little curiosity. A lot of clarity.</h1><p>Pick up an investigation, or start with a new question.</p></div>${button(`${icon('plus')} New investigation`, 'new')}</div>
      <div class="dashboard-grid"><section class="resume-card"><div class="resume-top"><span class="eyebrow">${p ? 'PICK UP WHERE YOU LEFT OFF' : 'YOUR NEXT DISCOVERY STARTS HERE'}</span><span class="live-dot">${p ? statusText(p) : 'Ready when you are'}</span></div><div class="resume-body">${p ? appMark(p, true) : `<span class="app-mark large generic">${icon('search')}</span>`}<div><h2>${p ? esc(p.app) : 'What’s underneath?'}</h2><p>${p ? esc(p.goal) : 'Bring an application and a question. We’ll map the path forward.'}</p></div></div><div class="mini-roadmap">${phases.map((name, i) => `<div class="${p && i <= p.completed ? 'done' : ''} ${p && i === p.phase ? 'next' : ''}"><span>${p && i <= p.completed ? icon('check') : i === 0 ? '0' : i}</span><small>${name}</small></div>`).join('')}</div><div class="resume-bottom"><span>${icon('clock')} ${p ? (p.status === 'ready' ? 'Your next step is ready to review' : 'Progress is saved to this browser') : 'Start with a free initial assessment'}</span>${button(`${p ? 'Open investigation' : 'Get started'} ${icon('arrow')}`, p ? 'open' : 'new', 'primary', p ? `data-id="${p.id}"` : '')}</div></section>
      <section class="how-card"><span class="eyebrow">A CLEAR PATH FORWARD</span><h2>Big questions.<br/>Manageable steps.</h2><p>Start with a free assessment. Go deeper when you know what you’re buying.</p><div class="how-step">${icon('search')}<div><strong>Explore first</strong><small>Initial findings, on us.</small></div></div><div class="how-step">${icon('file')}<div><strong>Know the scope</strong><small>Clear deliverables. A fixed price.</small></div></div><div class="how-step">${icon('shield')}<div><strong>Stay in control</strong><small>Approve each paid phase.</small></div></div></section></div>
      <div class="stats-row"><div>${icon('projects')}<span><strong>${state.projects.length}</strong><small>Saved investigations</small></span></div><div>${icon('file')}<span><strong>${state.projects.reduce((n, p) => n + Math.max(0, p.completed + 1) * 3, 0)}</strong><small>Illustrative findings</small></span></div><div>${icon('billing')}<span><strong>${money(state.receipts.filter((r) => !r.refunded).reduce((n, r) => n + r.price, 0))}</strong><small>Demo purchases · no real charges</small></span></div></div>
      <section class="section"><div class="section-heading"><div><h2>Recent investigations <span class="count">${state.projects.length}</span></h2><p>Your questions, findings, and next steps in one place.</p></div><a href="#projects" class="text-link">View all projects ${icon('arrow')}</a></div><div class="project-table"><div class="table-heading"><span>APPLICATION / GOAL</span><span>CURRENT PHASE</span><span>STATUS</span><span>CREATED</span></div>${state.projects.slice(0, 3).map(projectRow).join('') || empty('Your first investigation starts with a question.', 'Create a project to save your findings and progress.')}</div></section>
      <div class="dashboard-footnote">${icon('lock')} Prototype only. Analysis, accounts, uploads, and payments are simulated.</div>`;
  }
  function empty(title: string, text: string) {
    return `<div class="empty-state">${icon('projects')}<h3>${title}</h3><p>${text}</p>${button(`${icon('plus')} New investigation`, 'new', 'secondary')}</div>`;
  }
  function projectsPage() {
    const filtered = state.projects.filter((p) => `${p.app} ${p.goal}`.toLowerCase().includes(search.toLowerCase()));
    return `<div class="page-heading"><div><div class="eyebrow">KEEP THE THREAD</div><h1 tabindex="-1">Your investigations</h1><p>Every application, question, and discovery. Saved together.</p></div>${button(`${icon('plus')} New investigation`, 'new')}</div><div class="list-toolbar"><label class="search-field">${icon('search')}<input id="project-search" placeholder="Search applications or goals…" value="${esc(search)}" aria-label="Search projects"/></label><span>${filtered.length} project${filtered.length === 1 ? '' : 's'}</span></div><div class="project-table"><div class="table-heading"><span>APPLICATION / GOAL</span><span>CURRENT PHASE</span><span>STATUS</span><span>CREATED</span></div>${filtered.map(projectRow).join('') || empty(search ? 'No matching investigations.' : 'A blank page. A good place to start.', search ? 'Try another application name or goal.' : 'Create your first project to get started.')}</div>`;
  }
  function evidencePanel(p: Project) {
    return `<div class="evidence-preview"><div class="evidence-bar"><span>${icon('code')} ${p.sample ? 'publishing-flow.example' : 'investigation-outline.example'}</span>${badge('SAMPLE')}</div><pre><code><span class="code-muted">// Illustrative workflow · not a live trace</span>
<span class="code-purple">application</span> ${esc(p.app)}
  │
  ├─ <span class="code-blue">01</span> Identify entry points
  ├─ <span class="code-blue">02</span> Trace relevant behavior
  ├─ <span class="code-blue">03</span> Record evidence + unknowns
  │
  └─ <span class="code-green">deliver</span> Findings mapped to your goal</code></pre><button class="evidence-link" data-action="evidence">Explore the evidence ${icon('arrow')}</button></div>`;
  }
  function findings(p: Project) {
    const rows = p.sample
      ? [
          [
            'Target & structure',
            'Android application with multiple packages',
            'Acquisition and package inventory are the first checkpoints for this example.',
            'globe',
          ],
          [
            'Workflow to investigate',
            'Reel publishing spans several steps',
            'Trace media preparation, request construction, and response handling.',
            'code',
          ],
          [
            'Known unknowns',
            'Client evidence has a boundary',
            'Server behavior and runtime assumptions need separate validation.',
            'help',
          ],
        ]
      : [
          [
            'Investigation target',
            `${p.app} is the selected application`,
            'Confirm the exact version and provide relevant source material when requested.',
            'globe',
          ],
          [
            'Goal & approach',
            'A path from your question to evidence',
            'Identify relevant entry points, trace behavior, and record reproducible findings.',
            'code',
          ],
          [
            'Known unknowns',
            'Source material still needs verification',
            'This demo illustrates a report structure; it has not inspected your application.',
            'help',
          ],
        ];
    return `<section class="findings-section"><div class="section-heading"><div><h2>${p.completed > 0 ? 'Investigation findings' : 'Your first findings'}</h2><p>${p.completed > 0 ? 'The report stays with your project as you move forward.' : 'A starting point for deciding what to investigate next.'}</p></div>${badge('Illustrative data', 'neutral')}</div><div class="findings-grid"><div class="findings-list">${rows.map(([label, title, text, mark], i) => `<button class="finding" data-action="finding" data-index="${i}"><span class="finding-icon">${icon(mark)}</span><span><small>${label}</small><strong>${esc(title)}</strong><p>${text}</p></span>${icon('chevron')}</button>`).join('')}</div>${evidencePanel(p)}</div></section>`;
  }
  function scope(p: Project) {
    if (p.phase === 0)
      return [
        'Identify the target and available source material',
        'Deliver initial findings with explicit gaps',
        'Propose a useful next phase with a defined scope',
      ];
    if (p.phase > 3)
      return [
        'Final investigation report',
        'Evidence bundle with reproducible steps',
        'Documented limitations and validation results',
      ];
    return p.phase === 1
      ? [
          `Trace the behavior relevant to your goal`,
          'Deliver an evidence-backed investigation report',
          'Document gaps and recommend the next steps',
        ]
      : p.phase === 2
        ? [
            'Build the artifact defined by the agreed goal',
            'Package supporting documentation and evidence',
            'Provide reproduction instructions and limitations',
          ]
        : [
            'Check the deliverable against agreed criteria',
            'Document what passed, failed, or remains unknown',
            'Package the validated results for handoff',
          ];
  }
  function proposal(p: Project) {
    if (p.status === 'complete')
      return `<section class="completion-card"><span class="completion-icon">${icon('check')}</span><div><span class="eyebrow">INVESTIGATION COMPLETE</span><h2>From question to something you can use.</h2><p>Your sample report, evidence, and validation notes are ready.</p></div>${button(`${icon('download')} Download report`, 'export', 'primary')}</section>`;
    if (p.status === 'running' || p.status === 'paused' || p.status === 'failed') {
      const elapsed = p.elapsed + (p.status === 'running' ? Date.now() - p.started : 0);
      const idx = Math.min(2, Math.floor((elapsed / durations[p.phase]) * 3));
      return `<section class="progress-card"><div class="section-heading"><div><span class="eyebrow">${p.phase === 0 ? 'FREE ASSESSMENT' : 'PURCHASED PHASE'} · ${phases[p.phase].toUpperCase()}</span><h2>${p.status === 'failed' ? 'We hit a technical interruption.' : p.status === 'paused' ? (p.scopePending ? 'Review the expanded scope.' : 'Your work is paused.') : activities[p.phase][idx]}</h2></div>${badge(p.status === 'running' ? 'Running in background' : statusText(p), p.status === 'failed' ? 'amber' : 'blue')}</div><p>${p.status === 'failed' ? 'Completed checkpoints are saved. Retry this step without an additional charge.' : p.status === 'paused' ? (p.scopePending ? 'Work is paused until you accept a revised proposal. Existing findings are preserved.' : 'Your findings are saved. Resume when you’re ready.') : 'You can leave this page. The demo continues from elapsed time when you return.'}</p><div class="activity-steps">${activities[p.phase].map((a, i) => `<div class="${i < idx ? 'finished' : i === idx ? 'current' : ''}"><span>${i < idx ? icon('check') : i === idx && p.status === 'running' ? '<i class="spinner"></i>' : '○'}</span>${a}</div>`).join('')}</div><div class="progress-actions">${button(`${icon(p.status === 'running' ? 'pause' : 'play')} ${p.status === 'running' ? 'Pause demo' : p.status === 'failed' ? 'Retry at no charge' : p.scopePending ? 'Review revised proposal' : 'Resume demo'}`, p.scopePending ? 'scope-requote' : 'toggle-run', 'secondary')}${p.status === 'running' ? button('Simulate interruption', 'fail', 'text-button') : p.status === 'failed' && p.phase > 0 ? button('Simulate unable to deliver & refund', 'refund', 'text-button danger') : ''}<small>Simulated activity · no tools are running</small></div></section>`;
    }
    return `<section class="proposal-card"><div class="proposal-main"><span class="eyebrow">${p.completed > 0 ? 'YOUR NEXT CHAPTER' : 'READY TO GO DEEPER?'}</span><h2>${p.phase === 1 ? 'Turn an initial finding into a clear answer.' : p.phase === 2 ? 'Turn your findings into a useful deliverable.' : 'Put the results to the test.'}</h2><p>Phase ${p.phase} · ${phases[p.phase]}. A defined scope, with evidence you can come back to.</p><ul>${scope(
      p
    )
      .map((s) => `<li>${icon('check')}${s}</li>`)
      .join(
        ''
      )}</ul><button class="text-link" data-action="scope">Review scope, limits & completion criteria ${icon('arrow')}</button></div><div class="proposal-price"><span class="price-label">ONE-TIME PHASE PURCHASE</span><strong>$${prices[p.phase]}<small>.00</small></strong><span>Illustrative price · no subscription</span>${button(`Review & continue ${icon('arrow')}`, 'checkout')}<small>${icon('lock')} Demo checkout · no real charge</small></div></section>`;
  }
  function chat(p: Project) {
    return `<aside class="chat-panel" aria-label="Investigation chat"><div class="chat-heading"><span>${icon('spark')} Investigation assistant</span><button class="icon-button" data-action="chat-toggle" aria-label="Close chat" aria-expanded="true">${icon('close')}</button></div><div class="chat-context">${appMark(p)}<span>${esc(p.app)}<small>Project context stays with you</small></span></div><div class="chat-messages" aria-live="polite">${p.messages.map((m) => `<div class="message ${m.role}">${m.role === 'assistant' ? `<span class="message-mark">${icon('spark')}</span>` : ''}<div><small>${m.role === 'assistant' ? 'REA ASSISTANT · DEMO' : 'YOU'}</small><p>${esc(m.text)}</p></div></div>`).join('')}<div class="chat-suggestions">${button('What will I receive?', 'suggest-deliverable', 'suggestion')}${button('Refine my goal', 'edit-goal', 'suggestion')}</div></div><form id="chat-form" class="chat-compose"><label class="sr-only" for="chat-input">Message the demo assistant</label><textarea id="chat-input" name="message" rows="2" maxlength="2000" placeholder="Ask about your investigation…" required></textarea><div><small>Demo replies · no AI connected</small><button class="send-button" type="submit" aria-label="Send message">${icon('send')}</button></div></form><p class="chat-footer">Findings live in your project, beyond the conversation.</p></aside>`;
  }
  function filesPanel(p: Project) {
    return `<section><div class="section-heading"><div><h2>Source material</h2><p>Keep inputs separate from the findings they support.</p></div>${badge(`${p.files.length} files`, 'neutral')}</div><div class="upload-zone">${icon('upload')}<h3>Add source material when it’s needed.</h3><p>In this prototype, only file names and sizes are saved locally.<br/>File contents are never read or uploaded.</p><label class="button secondary file-picker">${icon('plus')} Choose demo files<input type="file" id="file-input" multiple /></label></div>${p.files.length ? `<div class="file-list">${p.files.map((f) => `<div>${icon('file')}<span><strong>${esc(f.name)}</strong><small>${(f.size / 1024).toFixed(1)} KB · metadata only</small></span><button class="icon-button" data-action="delete-file" data-id="${f.id}" aria-label="Delete ${esc(f.name)}">${icon('trash')}</button></div>`).join('')}</div>` : ''}<form class="link-form card" id="link-form"><label for="target-link">Reference link</label><p>Saved as project context. This prototype does not fetch the URL.</p><div><input type="url" id="target-link" name="url" value="${esc(p.link)}" placeholder="https://example.com/application" maxlength="2000"/><button type="submit" class="button secondary">Save link</button></div></form><div class="privacy-note">${icon('shield')}<p><strong>Your findings stay yours.</strong> Delete source file metadata at any time without removing your reports. Production upload security is not implemented in this prototype.</p></div></section>`;
  }
  function evidenceTab(p: Project) {
    return `<section><div class="section-heading"><div><h2>A finding should have a trail.</h2><p>Separate observations, interpretations, and open questions.</p></div>${button(`${icon('download')} Export report`, 'export', 'secondary')}</div><div class="evidence-notice">${icon('help')} Sample evidence explains the interface. It is not an analysis of ${esc(p.app)}.</div>${['Target inventory', 'Workflow outline', 'Limitations & next checks'].map((title, i) => `<details class="evidence-detail" ${i === 0 ? 'open' : ''}><summary><span class="evidence-number">E0${i + 1}</span><span><strong>${title}</strong><small>${['Inputs and application structure', 'Steps relevant to the investigation goal', 'What still needs to be established'][i]}</small></span>${badge(i === 2 ? 'Unknown' : 'Example', i === 2 ? 'amber' : 'neutral')}${icon('down')}</summary><div><p>${i === 0 ? 'Record the exact target, version, file inventory, and integrity checks here. No files have been analyzed in this demo.' : i === 1 ? `Goal: ${esc(p.goal)}. A real investigation would link each observation to a tool output, artifact, or reproducible step.` : 'An absent finding is not proof of absent behavior. Runtime, server-side behavior, and inaccessible inputs remain explicit unknowns until verified.'}</p><pre><code>${esc(JSON.stringify({ evidence_id: `example-E0${i + 1}`, target: p.app, source: 'prototype fixture', verified: false }, null, 2))}</code></pre></div></details>`).join('')}</section>`;
  }
  function workspace() {
    const p = project();
    if (!p) return empty('Project not found.', 'Return to Projects to choose an investigation.');
    return `<div class="workspace-title"><div><a class="back-link" href="#projects">Projects ${icon('chevron')}</a><div class="project-title">${appMark(p)}<h1 tabindex="-1">${esc(p.app)}</h1>${badge(p.kind, 'neutral')}</div><p class="goal-line">${esc(p.goal)} <button class="inline-edit" data-action="edit-goal">Edit goal</button></p></div><div class="workspace-tools">${button(`${icon('download')} Export`, 'export', 'secondary small')}${button(`${icon('chat')} ${chatOpen ? 'Hide' : 'Open'} chat`, 'chat-toggle', 'secondary small', `aria-expanded="${chatOpen}"`)}</div></div><div class="phase-track" aria-label="Investigation phases">${phases.map((name, i) => `<button class="phase-step ${i <= p.completed ? 'done' : ''} ${i === p.phase && p.status !== 'complete' ? 'current' : ''}" data-action="phase" data-index="${i}"><span class="phase-dot">${i <= p.completed ? icon('check') : String(i).padStart(2, '0')}</span><span><small>PHASE ${i}${i === 0 ? ' · FREE' : ''}</small><strong>${name}</strong></span>${i < 3 ? icon('chevron') : ''}</button>`).join('')}</div><div class="investigation-layout ${chatOpen ? '' : 'chat-hidden'}"><div class="investigation-body"><div class="tabs" role="tablist" aria-label="Project views">${[
      ['overview', 'Overview'],
      ['evidence', 'Evidence'],
      ['files', 'Files & links'],
    ]
      .map(
        ([key, label]) =>
          `<button role="tab" id="tab-${key}" aria-controls="project-panel" aria-selected="${tab === key}" tabindex="${tab === key ? 0 : -1}" class="${tab === key ? 'active' : ''}" data-action="tab" data-tab="${key}">${label}${key === 'evidence' ? '<span>3</span>' : ''}</button>`
      )
      .join(
        ''
      )}<span class="saved-label">${icon('check')} ${storageAvailable ? 'Saved locally' : 'Session only'}</span></div><div id="project-panel" role="tabpanel" aria-labelledby="tab-${tab}" class="tab-content">${tab === 'overview' ? `${p.completed > 0 ? `<div class="delivered-banner">${icon('check')} ${phases[p.completed]} delivered · Sample results are ready.${button('View report', 'export', 'text-button')}</div>` : ''}${p.phase === 0 ? proposal(p) : findings(p) + proposal(p)}<div class="scope-footnote">${icon('shield')} You approve the scope. You approve the price. Further phases are always your choice.</div>` : tab === 'evidence' ? evidenceTab(p) : filesPanel(p)}</div></div>${chatOpen ? chat(p) : ''}</div>`;
  }
  function billing() {
    return `<div class="page-heading"><div><div class="eyebrow">NO SURPRISES</div><h1 tabindex="-1">Billing</h1><p>One purchase per agreed phase. Every charge has a scope.</p></div>${badge('Demo mode · no real charges', 'blue')}</div><div class="billing-summary card"><div><small>TOTAL DEMO PURCHASES</small><h2>${money(state.receipts.filter((r) => !r.refunded).reduce((a, r) => a + r.price, 0))}</h2></div><div>${icon('shield')}<span><strong>No automatic renewals</strong><small>Each additional phase requires a new purchase.</small></span></div></div><div class="section-heading"><h2>Purchase history</h2></div><div class="billing-history">${
      state.receipts.length
        ? state.receipts
            .slice()
            .reverse()
            .map(
              (r) =>
                `<div class="receipt-row">${icon('file')}<span><strong>${esc(r.app)} · ${phases[r.phase]}</strong><small>${date(r.date)} · ${r.id.slice(0, 8)} · Simulated receipt</small></span>${badge(r.refunded ? 'Refunded' : 'Demo purchase', r.refunded ? 'amber' : 'green')}<strong>${money(r.price)}</strong><button class="button secondary small" data-action="receipt" data-id="${r.id}">Details</button></div>`
            )
            .join('')
        : `<div class="empty-state">${icon('billing')}<h3>A clean slate.</h3><p>Your demo phase purchases will appear here.<br/>The initial assessment is free.</p><a href="#projects" class="button secondary">Explore your projects ${icon('arrow')}</a></div>`
    }</div><div class="privacy-note">${icon('help')}<p>Technical failures are retried at no additional charge. If the purchased scope cannot be delivered, the prototype lets you simulate a refund. A report establishing a limitation can still meet the agreed scope.</p></div>`;
  }
  function settings() {
    return `<div class="page-heading"><div><div class="eyebrow">YOUR WORKSPACE, YOUR CONTROL</div><h1 tabindex="-1">Settings</h1><p>Manage your demo profile, appearance, and local project data.</p></div></div><section class="settings-card card"><h2>Profile</h2><p>This is a local demo identity, not an authenticated account.</p><form id="profile-form"><div class="form-grid"><label>Name<input name="name" value="${esc(state.profile?.name || '')}" placeholder="Your name" required maxlength="80"/></label><label>Email<input name="email" type="email" value="${esc(state.profile?.email || '')}" placeholder="you@example.com" required maxlength="200"/></label></div><button class="button primary" type="submit">Save demo profile</button></form></section><section class="settings-card card"><div class="section-heading"><div><h2>Appearance</h2><p>AstroWind’s shared theme, across every view.</p></div>${button(`${icon('moon')} ${state.dark ? 'Switch to light' : 'Switch to dark'}`, 'theme', 'secondary')}</div></section><section class="settings-card card"><h2>Files & retention</h2><p>Demo project data, messages, file names, and link text are saved in this browser. File contents are never read. There is no server-side account, private upload service, or live AI connection.</p><p>Remove file metadata on a project’s Files & links tab to keep its findings. Delete a project below to remove its saved demo data, messages, and purchase history.</p>${state.projects.map((p) => `<div class="settings-project"><span>${esc(p.app)}</span>${button('Delete project', 'delete-project', 'text-button danger', `data-id="${p.id}"`)}</div>`).join('')}</section><section class="settings-card card"><h2>Start fresh</h2><p>Restore the original sample investigation and clear all locally saved demo changes.</p>${button('Reset prototype', 'reset', 'secondary danger')}</section>`;
  }
  function render() {
    const focused = document.activeElement as HTMLInputElement | HTMLTextAreaElement | null;
    const preserve = focused?.id
      ? { id: focused.id, value: focused.value, start: focused.selectionStart, end: focused.selectionEnd }
      : null;
    document.documentElement.classList.toggle('dark', state.dark);
    app.innerHTML = shell(
      page === 'dashboard'
        ? dashboard()
        : page === 'projects'
          ? projectsPage()
          : page === 'workspace'
            ? workspace()
            : page === 'billing'
              ? billing()
              : settings()
    );
    if (preserve) {
      const el = document.getElementById(preserve.id) as HTMLInputElement | HTMLTextAreaElement | null;
      if (el) {
        if (typeof preserve.value === 'string') el.value = preserve.value;
        el.focus({ preventScroll: true });
        try {
          el.setSelectionRange(preserve.start, preserve.end);
        } catch {
          /* Non-text inputs have no selection. */
        }
      }
    }
  }
  function closeModal() {
    const dialog = modalRoot.querySelector('dialog');
    dialog?.close();
    modalRoot.innerHTML = '';
  }
  function modal(title: string, body: string, wide = false) {
    closeModal();
    modalRoot.innerHTML = `<dialog class="dialog ${wide ? 'wide' : ''}" aria-labelledby="dialog-title"><div class="dialog-header"><span class="eyebrow">REVERSE ENGINEER ANYTHING</span><button class="icon-button" data-action="close-modal" aria-label="Close dialog">${icon('close')}</button></div><h2 id="dialog-title">${title}</h2>${body}</dialog>`;
    const dialog = modalRoot.querySelector('dialog')!;
    dialog.addEventListener('cancel', () => {
      setTimeout(() => {
        modalRoot.innerHTML = '';
      }, 0);
    });
    dialog.showModal();
  }
  function newProject() {
    modal(
      'What do you want to figure out?',
      `<p class="dialog-description">Start with an application and a goal. We’ll work out the investigation together.</p><form id="intake-form"><label>Application<input name="app" placeholder="e.g. Instagram, a desktop app, or a website" value="${esc(draft.app)}" required maxlength="100" autofocus/></label><label>What would success look like?<textarea name="goal" rows="4" placeholder="e.g. Document how Reel publishing works so I can build an integration." required maxlength="1000">${esc(draft.goal)}</textarea></label><div class="intake-note">${icon('file')} No files needed to start. We’ll ask for source material when it’s useful.</div><button class="button primary full" type="submit">Start free assessment ${icon('arrow')}</button><p class="fine-print">Prototype only. Your inputs are saved in this browser.<br/>No analysis or real account creation takes place.</p></form>`
    );
  }
  function signup() {
    modal(
      'Keep your investigation together.',
      `<p class="dialog-description">Create a demo profile to save <strong>${esc(draft.app)}</strong> and its findings in this browser. Your application and goal are already preserved.</p><form id="signup-form"><label>Your name<input name="name" placeholder="Alex Morgan" required maxlength="80" autofocus/></label><label>Email<input type="email" name="email" placeholder="you@example.com" required maxlength="200"/></label><button class="button primary full" type="submit">Create demo workspace ${icon('arrow')}</button><p class="fine-print">No password, email, or authentication request is sent.<br/>This profile exists only in this browser.</p></form>`
    );
  }
  function createProject() {
    const p: Project = {
      id: uid(),
      app: draft.app,
      goal: draft.goal,
      kind: 'Application',
      sample: false,
      completed: -1,
      phase: 0,
      status: 'running',
      started: Date.now(),
      elapsed: 0,
      created: Date.now(),
      files: [],
      link: '',
      messages: [
        {
          role: 'assistant',
          text: 'Your demo assessment has started. I’ll illustrate an investigation plan based on your goal. This prototype does not inspect applications or contact an AI model.',
        },
      ],
    };
    state.projects.unshift(p);
    draft = { app: '', goal: '' };
    save();
    closeModal();
    navigate('workspace', p.id);
  }
  function scopeBody(p: Project) {
    return `<div class="scope-goal"><small>YOUR GOAL</small><p>${esc(p.goal)}</p></div><h3>What you’re buying</h3><ul class="scope-list">${scope(
      p
    )
      .map((s) => `<li>${icon('check')}${s}</li>`)
      .join(
        ''
      )}</ul><div class="scope-facts"><div><small>Fixed phase price</small><strong>${money(prices[p.phase])} <span>illustrative</span></strong></div><div><small>Estimated duration</small><strong>About ${durations[p.phase] / 1000}s in this demo</strong></div></div><h3>Completion criteria</h3><p class="scope-copy">A downloadable report and evidence outline addressing the agreed goal, with reproducible steps where available and explicit limitations.</p><h3>Limits & purchase protection</h3><p class="scope-copy">This phase does not guarantee access to unavailable code, server behavior, or a complete reconstruction. A documented limitation may be a valid result. Technical failures are retried without additional charges; inability to deliver the agreed scope results in a refund. Expanded scope requires a new proposal.</p>`;
  }
  function checkout() {
    const p = project();
    if (!p || p.status !== 'ready') return;
    modal(
      `Review Phase ${p.phase}: ${phases[p.phase]}`,
      `${scopeBody(p)}<div class="checkout-total"><span>One-time total</span><strong>${money(prices[p.phase])}</strong></div><div class="demo-checkout-note">${icon('shield')} Simulated checkout. No payment details are collected and no real charge is made.</div><form id="checkout-form"><label class="checkbox-label"><input name="agree" type="checkbox" required/> I’ve reviewed the scope, deliverables, and limitations.</label><button class="button primary full" type="submit">Complete demo checkout · ${money(prices[p.phase])} ${icon('arrow')}</button></form>`,
      true
    );
  }
  function exportReport(p: Project) {
    const report = `REVERSE ENGINEER ANYTHING — PROTOTYPE REPORT\n\nThis is illustrative demo content, not a real application analysis.\n\nApplication: ${p.app}\nGoal: ${p.goal}\nCompleted phase: ${p.completed < 0 ? 'None' : phases[p.completed]}\n\nILLUSTRATIVE FINDINGS\n1. Establish the target version and artifact inventory.\n2. Trace behavior relevant to the selected goal.\n3. Separate observations from interpretations and unknowns.\n\nLIMITATIONS\nNo files were analyzed, URLs fetched, AI invoked, or payments collected.\n\nSOURCE METADATA\n${p.files.map((f) => `${f.name} (${f.size} bytes)`).join('\n') || 'No file metadata attached.'}\n\nReference link (not fetched): ${p.link || 'None'}\n`;
    const url = URL.createObjectURL(new Blob([report], { type: 'text/plain;charset=utf-8' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = `rea-${p.app.replace(/[^a-z0-9-]/gi, '-').slice(0, 80)}-demo-report.txt`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast('Demo report downloaded.');
  }
  function updateJobs() {
    let changed = false;
    state.projects.forEach((p) => {
      if (p.status !== 'running') return;
      if (p.elapsed + Date.now() - p.started >= durations[p.phase]) {
        p.completed = p.phase;
        p.phase += 1;
        p.status = p.phase > 3 ? 'complete' : 'ready';
        p.elapsed = 0;
        p.started = 0;
        p.messages.push({
          role: 'assistant',
          text: `${phases[p.completed]} is complete in this demo. The sample results are saved. ${p.phase > 3 ? 'Your final report is ready to download.' : 'Review the next phase’s scope whenever you’re ready; it will never start or charge automatically.'}`,
        });
        changed = true;
      }
    });
    if (changed) save();
    const p = project();
    const signature = `${p?.id}:${p?.status}:${p?.phase}:${p?.status === 'running' ? Math.min(2, Math.floor(((p.elapsed + Date.now() - p.started) / durations[p.phase]) * 3)) : ''}`;
    if (changed || (page === 'workspace' && signature !== visibleStep)) {
      visibleStep = signature;
      render();
    }
  }
  function editGoal() {
    const p = project();
    if (!p) return;
    modal(
      'Refine the question.',
      `<p class="dialog-description">Previous findings stay with this project. A material scope expansion needs a revised proposal before any further paid work.</p><form id="goal-form"><label>Investigation goal<textarea name="goal" rows="4" required maxlength="1000" autofocus>${esc(p.goal)}</textarea></label><label class="checkbox-label"><input name="expanded" type="checkbox"/> This changes the scope of the current investigation.</label><button class="button primary full" type="submit">Save goal ${icon('check')}</button></form>`
    );
  }
  document.addEventListener('click', (event) => {
    const el = (event.target as HTMLElement).closest<HTMLElement>('[data-action]');
    if (!el) return;
    const action = el.dataset.action;
    const p = project();
    switch (action) {
      case 'new':
        newProject();
        break;
      case 'open':
        navigate('workspace', el.dataset.id);
        break;
      case 'close-modal':
        closeModal();
        break;
      case 'profile':
        closeModal();
        navigate('settings');
        break;
      case 'theme':
        state.dark = !state.dark;
        save();
        render();
        break;
      case 'mobile':
        document.body.classList.add('nav-open');
        document.querySelector<HTMLElement>('.sidebar')!.inert = false;
        document.querySelector<HTMLElement>('.sidebar a')?.focus();
        break;
      case 'mobile-close':
        document.body.classList.remove('nav-open');
        document.querySelector<HTMLElement>('.sidebar')!.inert = window.matchMedia('(max-width: 760px)').matches;
        document.querySelector<HTMLElement>('[data-action=mobile]')?.focus();
        break;
      case 'chat-toggle':
        chatOpen = !chatOpen;
        render();
        break;
      case 'tab':
        tab = el.dataset.tab || 'overview';
        render();
        document.querySelector<HTMLElement>(`#tab-${tab}`)?.focus();
        break;
      case 'evidence':
        tab = 'evidence';
        render();
        break;
      case 'checkout':
        checkout();
        break;
      case 'export':
        if (p) exportReport(p);
        break;
      case 'edit-goal':
        editGoal();
        break;
      case 'scope':
        if (p)
          modal(
            `Phase ${p.phase}: ${phases[p.phase]}`,
            `${scopeBody(p)}${button('Continue to demo checkout ' + icon('arrow'), 'checkout', 'primary full')}`,
            true
          );
        break;
      case 'finding':
        if (p)
          modal(
            'From finding to evidence.',
            `<p class="dialog-description">This sample finding illustrates how the real report would explain an observation, cite supporting evidence, and state what remains unknown.</p><div class="scope-goal"><small>PROJECT GOAL</small><p>${esc(p.goal)}</p></div><p class="scope-copy">No analysis has run. Open the Evidence view to explore the proposed record structure.</p>${button('View evidence ' + icon('arrow'), 'open-evidence', 'primary full')}`
          );
        break;
      case 'open-evidence':
        closeModal();
        tab = 'evidence';
        render();
        break;
      case 'phase':
        if (p) {
          const i = Number(el.dataset.index);
          modal(
            `Phase ${i}: ${phases[i]}`,
            `<p class="dialog-description">${['Identify the target, inspect available material, and establish a useful next scope. This initial assessment is free.', 'Trace the behavior relevant to your goal. Deliver findings backed by evidence and explicit unknowns.', 'Build the artifact agreed for this goal, such as documentation, an API catalog, or a reconstruction.', 'Check the deliverable against the agreed criteria and document remaining limitations.'][i]}</p>${badge(i <= p.completed ? 'Completed in demo' : i === p.phase ? statusText(p) : 'Future phase', i <= p.completed ? 'green' : 'neutral')}<p class="scope-copy">Specific tasks and deliverables adapt to your project. Each paid phase has its own proposal.</p>${button('Back to investigation', 'close-modal', 'secondary full')}`
          );
        }
        break;
      case 'scope-requote':
        if (p?.scopePending)
          modal(
            'Review your expanded scope',
            `${scopeBody(p)}<div class="checkout-total"><span>Additional demo scope fee</span><strong>$19.00</strong></div><p class="scope-copy">This illustrative addition covers investigation of the revised goal. Existing purchases remain in your history. No real payment is collected.</p><form id="revision-form"><label class="checkbox-label"><input type="checkbox" name="agree" required/> I approve the revised goal, scope, and additional demo price.</label><button class="button primary full" type="submit">Accept revised scope · $19.00</button></form>`,
            true
          );
        break;
      case 'toggle-run':
        if (p && !p.scopePending) {
          if (p.status === 'running') {
            p.elapsed += Date.now() - p.started;
            p.status = 'paused';
          } else {
            p.started = Date.now();
            p.status = 'running';
          }
          save();
          render();
        }
        break;
      case 'fail':
        if (p?.status === 'running') {
          p.elapsed += Date.now() - p.started;
          p.status = 'failed';
          save();
          render();
        }
        break;
      case 'refund':
        if (p) {
          modal(
            'Unable to deliver this phase?',
            `<p class="dialog-description">Simulate a technical failure that prevents delivery of the purchased scope. All demo purchases for the undelivered phase will be refunded. Existing findings stay saved.</p>${button('Simulate refund', 'confirm-refund', 'primary full')}`
          );
        }
        break;
      case 'confirm-refund':
        if (p) {
          state.receipts.forEach((r) => {
            if (r.projectId === p.id && r.phase === p.phase) r.refunded = true;
          });
          p.scopePending = false;
          p.status = 'ready';
          p.elapsed = 0;
          p.started = 0;
          save();
          closeModal();
          render();
          toast('Demo refund recorded. No real money moved.');
        }
        break;
      case 'suggest-deliverable':
        if (p) {
          p.messages.push(
            { role: 'user', text: 'What will I receive?' },
            {
              role: 'assistant',
              text: `For ${phases[Math.min(p.phase, 3)].toLowerCase()}, the proposal specifies: ${scope(p).join('; ')}. Review the scope and limitations before checkout. These are illustrative deliverables in this prototype.`,
            }
          );
          save();
          render();
        }
        break;
      case 'delete-file':
        if (p) {
          p.files = p.files.filter((f) => f.id !== el.dataset.id);
          save();
          render();
          toast('File metadata removed. Findings are preserved.');
        }
        break;
      case 'delete-project':
        modal(
          'Delete this investigation?',
          `<p class="dialog-description">This removes its demo findings, chat, file metadata, and purchase history from this browser. This cannot be undone.</p>${button('Delete project', 'confirm-delete', 'primary full', `data-id="${esc(el.dataset.id)}"`)}`
        );
        break;
      case 'confirm-delete':
        state.projects = state.projects.filter((p) => p.id !== el.dataset.id);
        state.receipts = state.receipts.filter((r) => r.projectId !== el.dataset.id);
        activeId = state.projects[0]?.id || '';
        save();
        closeModal();
        render();
        toast('Project data deleted from this browser.');
        break;
      case 'reset':
        modal(
          'Reset the prototype?',
          `<p class="dialog-description">This clears your local projects, profile, chat, and demo purchases, then restores the sample investigation.</p>${button('Reset all demo data', 'confirm-reset', 'primary full')}`
        );
        break;
      case 'confirm-reset':
        state = seed();
        activeId = state.projects[0].id;
        save();
        closeModal();
        navigate('dashboard');
        toast('Prototype reset.');
        break;
      case 'receipt': {
        const r = state.receipts.find((r) => r.id === el.dataset.id);
        if (r)
          modal(
            'Demo purchase receipt',
            `<div class="scope-goal"><small>${esc(r.id)}</small><h3>${esc(r.app)} · ${phases[r.phase]}</h3><p>${date(r.date)} · ${money(r.price)} · ${r.refunded ? 'Refunded' : 'Simulated purchase'}</p></div><p class="scope-copy">No payment method was collected or charged. The purchase covered the scoped phase and its report, supporting evidence, and documented limitations.</p>${button('Close receipt', 'close-modal', 'secondary full')}`
          );
        break;
      }
      case 'help':
        modal(
          'Take the prototype for a spin.',
          `<ol class="guide-list"><li>Open the Instagram example to explore findings and evidence.</li><li>Review the scope and complete a simulated checkout.</li><li>Watch a phase progress. Pause, retry an interruption, or simulate a refund.</li><li>Start a new investigation to try intake and demo signup.</li><li>Return to Projects, Billing, or Settings to see what was saved.</li></ol><div class="demo-checkout-note">${icon('help')} No live REA analysis, Bedrock requests, file uploads, authentication, emails, or real payments are connected.</div>${button('Got it', 'close-modal', 'primary full')}`
        );
        break;
    }
  });
  document.addEventListener('submit', (event) => {
    const form = event.target as HTMLFormElement;
    if (!form.id) return;
    event.preventDefault();
    const data = new FormData(form);
    const p = project();
    switch (form.id) {
      case 'intake-form':
        draft = { app: String(data.get('app')).trim(), goal: String(data.get('goal')).trim() };
        if (!draft.app || !draft.goal) {
          toast('Enter an application and a goal.');
          return;
        }
        if (state.profile) createProject();
        else signup();
        break;
      case 'signup-form':
        state.profile = { name: String(data.get('name')).trim(), email: String(data.get('email')).trim() };
        createProject();
        break;
      case 'profile-form':
        state.profile = { name: String(data.get('name')).trim(), email: String(data.get('email')).trim() };
        save();
        render();
        toast('Demo profile saved locally.');
        break;
      case 'revision-form':
        if (p?.scopePending && data.get('agree')) {
          state.receipts.push({
            id: uid(),
            projectId: p.id,
            app: p.app,
            phase: p.phase,
            price: 19,
            date: Date.now(),
            refunded: false,
          });
          p.scopePending = false;
          p.status = 'running';
          p.started = Date.now();
          p.messages.push({
            role: 'assistant',
            text: 'Revised scope accepted in demo checkout. Work has resumed on the updated goal. No real payment was collected.',
          });
          save();
          closeModal();
          render();
          toast('Revised demo scope accepted. Work resumed.');
        }
        break;
      case 'checkout-form':
        if (p && p.status === 'ready' && data.get('agree')) {
          state.receipts.push({
            id: uid(),
            projectId: p.id,
            app: p.app,
            phase: p.phase,
            price: prices[p.phase],
            date: Date.now(),
            refunded: false,
          });
          p.status = 'running';
          p.started = Date.now();
          p.elapsed = 0;
          p.messages.push({
            role: 'assistant',
            text: `Demo checkout completed for Phase ${p.phase}. The simulated phase is running. No payment was collected.`,
          });
          save();
          closeModal();
          render();
          toast('Demo purchase complete. Your phase has started.');
        }
        break;
      case 'chat-form':
        if (p) {
          const text = String(data.get('message')).trim();
          if (!text) return;
          p.messages.push(
            { role: 'user', text },
            {
              role: 'assistant',
              text: /cost|price|pay|buy/i.test(text)
                ? 'The next phase has a fixed illustrative price shown in its proposal. Review exactly what it includes before demo checkout. There are no automatic purchases or real charges.'
                : /goal|scope|instead|change/i.test(text)
                  ? 'Use “Edit goal” to save a refinement. Mark material scope changes so the current phase pauses for a revised proposal. Your earlier findings will remain available.'
                  : /file|upload|privacy|secure/i.test(text)
                    ? 'Files & links lets you save source metadata. This prototype never reads file contents or fetches links. All demo data is local to this browser.'
                    : 'This is a scripted demo reply. A live assistant would use your goal and saved evidence to answer, cite observations, and identify unknowns. Explore the findings or refine your goal to continue the prototype.',
            }
          );
          form.reset();
          save();
          render();
          document.querySelector<HTMLTextAreaElement>('#chat-input')?.focus();
          document.querySelector('.chat-messages')?.scrollTo({ top: 100000, behavior: 'smooth' });
        }
        break;
      case 'goal-form':
        if (p) {
          const goal = String(data.get('goal')).trim();
          if (!goal) return;
          p.goal = goal;
          if (data.get('expanded') && p.phase > 0 && ['running', 'paused', 'failed'].includes(p.status)) {
            if (p.status === 'running') p.elapsed += Date.now() - p.started;
            p.status = 'paused';
            p.scopePending = true;
          }
          p.messages.push({
            role: 'assistant',
            text: data.get('expanded')
              ? `Goal updated: ${goal}. Existing findings are preserved. Scope expansion is flagged. A running paid phase remains paused until its revised proposal is accepted; no additional charge has been authorized.`
              : `Goal refined: ${goal}. Existing findings are preserved.`,
          });
          save();
          closeModal();
          render();
          toast(
            data.get('expanded')
              ? 'Scope change flagged. No additional charge authorized.'
              : 'Goal updated. Previous findings preserved.'
          );
        }
        break;
      case 'link-form':
        if (p) {
          const url = String(data.get('url')).trim();
          if (url && !/^https?:\/\//i.test(url)) {
            toast('Use an http or https reference link.');
            return;
          }
          p.link = url;
          save();
          toast('Reference saved locally. The URL was not fetched.');
        }
        break;
    }
  });
  document.addEventListener('input', (event) => {
    const el = event.target as HTMLInputElement;
    if (el.id === 'project-search') {
      search = el.value;
      render();
    }
  });
  document.addEventListener('change', (event) => {
    const el = event.target as HTMLInputElement;
    if (el.id === 'file-input' && el.files && project()) {
      const p = project()!;
      p.files.push(...Array.from(el.files).map((f) => ({ id: uid(), name: f.name, size: f.size })));
      save();
      render();
      toast('File names saved locally. No file contents were read.');
    }
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && document.body.classList.contains('nav-open')) {
      document.body.classList.remove('nav-open');
      document.querySelector<HTMLElement>('.sidebar')!.inert = window.matchMedia('(max-width: 760px)').matches;
      document.querySelector<HTMLElement>('[data-action=mobile]')?.focus();
    }
    const el = event.target as HTMLElement;
    if (el.getAttribute('role') === 'tab' && ['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) {
      event.preventDefault();
      const tabs = ['overview', 'evidence', 'files'];
      const i = tabs.indexOf(tab);
      tab = tabs[event.key === 'Home' ? 0 : event.key === 'End' ? 2 : (i + (event.key === 'ArrowRight' ? 1 : 2)) % 3];
      render();
      document.querySelector<HTMLElement>(`#tab-${tab}`)?.focus();
    }
  });
  window.addEventListener('hashchange', () => {
    document.body.classList.remove('nav-open');
    parseRoute();
    search = '';
    render();
    window.scrollTo({ top: 0 });
  });
  window.matchMedia('(max-width: 760px)').addEventListener('change', () => render());
  parseRoute();
  updateJobs();
  render();
  save();
  setInterval(updateJobs, 1000);
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) updateJobs();
  });
}
