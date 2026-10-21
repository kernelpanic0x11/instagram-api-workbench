import { icon, esc, button, badge } from './workspace';

type User = { id: string; name: string; email: string };
type Source = { id: string; name: string; bytes: number; sha256: string };
type Evidence = { id: string; source_id: string; kind: string; sha256: string; content: unknown; created: number };
type Finding = { title: string; body: string; evidenceIds: string[]; confidence: 'observed' | 'inferred' };
type Assessment = {
  summary: string;
  goal: string;
  revision: number;
  findings: Finding[];
  limitations: string[];
  nextScope: { title: string; deliverables: string[]; exclusions: string[]; completionCriteria: string[] };
  generatedAt: number;
  coverage: { inspectedFileIds: string[]; omittedFileIds: string[] };
  model: string;
};
type Project = {
  id: string;
  app: string;
  goal: string;
  created: number;
  revision: number;
  status: string;
  activity: string;
  files: Source[];
  evidence: Evidence[];
  assessment: Assessment | null;
  link: string;
  job: { id: string; created: number; updated: number; error: string | null } | null;
};
type ServiceConfig = {
  auth: { provider: string; configured: boolean };
  analysis: { modelConfigured: boolean; executorReady: boolean; reason: string };
  limits: { maxFileBytes: number; maxProjectBytes: number; maxFiles: number; analyzedFilesPerAssessment: number };
};
const phases = ['Initial assessment', 'Investigation', 'Deliverables', 'Validation'];
const day = (v: number) => new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
const mark = () => `<span class="app-mark generic">${icon('code')}</span>`;

export async function startLiveWorkspace() {
  const app = document.querySelector<HTMLDivElement>('#app')!;
  const modalRoot = document.querySelector<HTMLDivElement>('#modal-root')!;
  let config: ServiceConfig;
  let user: User | null = null,
    csrf: string | null = null;
  let projects: Project[] = [],
    page = 'dashboard',
    activeId = '',
    tab = 'overview',
    search = '';
  let chatOpen = !matchMedia('(max-width: 760px)').matches;
  let dark = localStorage.getItem('rea-live-theme') === 'dark';
  let authEpoch = 0;
  let projectRequestId = sessionStorage.getItem('rea-project-request') || crypto.randomUUID();
  let busy = false,
    loadError = '',
    draft: { app: string; goal: string; requestId?: string } = { app: '', goal: '' };
  let toastTimer: ReturnType<typeof setTimeout>;
  try {
    const saved = sessionStorage.getItem('rea-project-draft');
    if (saved) draft = JSON.parse(saved);
  } catch {
    /* A draft is optional. */
  }
  const current = () => projects.find((p) => p.id === activeId);
  const active = (p: Project) => ['queued', 'running'].includes(p.status);
  const status = (p: Project) =>
    ({
      needs_input: 'Source material needed',
      queued: 'Queued',
      running: 'In progress',
      ready: 'Assessment ready',
      failed: 'Needs attention',
      cancelled: 'Cancelled',
    })[p.status] || p.status;

  async function api<T>(url: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers);
    if (options.body && typeof options.body === 'string') headers.set('Content-Type', 'application/json');
    if (csrf && options.method && options.method !== 'GET') headers.set('X-CSRF-Token', csrf);
    const response = await fetch(url, { ...options, headers, credentials: 'same-origin' });
    const result = await response.json();
    if (!response.ok) {
      if (response.status === 401 && !url.startsWith('/api/auth/')) {
        user = null;
        csrf = null;
        projects = [];
        render();
      }
      throw new Error(result.error || 'The service could not complete this request.');
    }
    return result;
  }
  function toast(text: string) {
    const el = document.querySelector<HTMLDivElement>('#toast')!;
    el.textContent = text;
    el.classList.add('visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove('visible'), 5000);
  }
  function closeModal() {
    modalRoot.querySelector('dialog')?.close();
    modalRoot.innerHTML = '';
  }
  function modal(title: string, content: string, wide = false) {
    closeModal();
    modalRoot.innerHTML = `<dialog class="dialog ${wide ? 'wide' : ''}" aria-labelledby="live-dialog-title"><div class="dialog-header"><span class="eyebrow">REVERSE ENGINEER ANYTHING</span><button class="icon-button" data-live="close" aria-label="Close dialog">${icon('close')}</button></div><h2 id="live-dialog-title">${title}</h2>${content}</dialog>`;
    const dialog = modalRoot.querySelector('dialog')!;
    dialog.showModal();
    dialog.addEventListener('cancel', () => {
      modalRoot.innerHTML = '';
    });
  }
  function liveButton(text: string, action: string, cls = 'primary', extra = '') {
    return button(text, action, cls, extra).replace('data-action=', 'data-live=');
  }
  function nav(next: string, id?: string) {
    page = next;
    if (id) activeId = id;
    tab = 'overview';
    history.replaceState(null, '', `#${page}${page === 'workspace' ? '/' + activeId : ''}`);
    render();
    window.scrollTo({ top: 0 });
  }
  function parseRoute() {
    const [route, id] = location.hash.slice(1).split('/');
    if (['dashboard', 'projects', 'billing', 'settings', 'workspace'].includes(route)) page = route;
    if (id && projects.some((p) => p.id === id)) activeId = id;
    if (page === 'workspace' && !current()) page = 'projects';
  }
  function replaceProject(p: Project) {
    projects = [p, ...projects.filter((old) => old.id !== p.id)].sort((a, b) => b.created - a.created);
  }
  async function refresh() {
    if (!user) return;
    const epoch = authEpoch;
    const result = await api<{ projects: Project[] }>('/api/projects');
    if (!user || epoch !== authEpoch) return;
    projects = result.projects.map((p) => ({
      ...p,
      evidence: p.evidence.map((e) => ({
        ...e,
        content: projects.find((old) => old.id === p.id)?.evidence.find((old) => old.id === e.id)?.content,
      })),
    }));
    if (!activeId) activeId = projects[0]?.id || '';
  }
  async function loadEvidence() {
    const p = current();
    if (!p || !user) return;
    const epoch = authEpoch;
    const result = await api<{ project: Project }>(`/api/projects/${p.id}?evidence=1`);
    if (user && epoch === authEpoch) replaceProject(result.project);
  }

  function shell(content: string) {
    return `<aside class="sidebar" aria-label="Main navigation" ${matchMedia('(max-width: 760px)').matches && !document.body.classList.contains('nav-open') ? 'inert' : ''}><a class="brand" href="#dashboard"><img src="/rea.svg" width="35" height="35" alt=""/><span>Reverse Engineer<span class="brand-sub">Anything</span></span></a><div class="workspace-switch">${icon('projects')}<span>${user ? 'Private workspace' : 'Your workspace'}</span>${badge('PHASE 0')}</div><span class="nav-label">WORKSPACE</span><nav>${[
      ['dashboard', 'Dashboard'],
      ['projects', 'Projects'],
      ['billing', 'Billing'],
      ['settings', 'Settings'],
    ]
      .map(
        ([key, label]) =>
          `<a href="#${key}" class="nav-item ${page === key || (page === 'workspace' && key === 'projects') ? 'active' : ''}" ${page === key || (page === 'workspace' && key === 'projects') ? 'aria-current="page"' : ''}>${icon(key)}<span>${label}</span>${key === 'projects' ? `<span class="nav-count">${projects.length}</span>` : ''}</a>`
      )
      .join(
        ''
      )}</nav><div class="sidebar-bottom"><div class="small-note">${icon('shield')}<div><strong>Evidence over assumptions.</strong><p>Findings should have a trail.</p></div></div><button class="nav-item" data-live="about">${icon('help')}<span>About this workspace</span>${icon('arrow')}</button><button class="profile" data-live="${user ? 'settings' : 'login'}"><span class="avatar">${esc(
      user
        ? user.name
            .split(' ')
            .map((n) => n[0])
            .slice(0, 2)
            .join('')
        : '?'
    )}</span><span><strong>${esc(user?.name || 'Sign in')}</strong><small>${user ? 'Personal account' : 'Save your investigation'}</small></span>${icon('down')}</button></div></aside><div class="mobile-backdrop" data-live="mobile-close"></div><div class="app-shell"><header class="topbar"><div class="breadcrumbs"><button class="icon-button mobile-menu" data-live="mobile" aria-label="Open navigation">${icon('menu')}</button><span class="crumb-root">Workspace</span>${icon('chevron')}<span>${page === 'workspace' ? esc(current()?.app) : page[0].toUpperCase() + page.slice(1)}</span></div><div class="topbar-right"><span class="demo-indicator"><i></i> Phase zero service</span><button class="icon-button" data-live="theme" aria-label="Toggle color theme">${icon('moon')}</button>${user ? liveButton('Sign out', 'logout', 'text-button', busy ? 'disabled' : '') : liveButton('Sign in', 'login', 'secondary small')}</div></header><main id="main" class="${page === 'workspace' ? 'workspace-main' : 'page-main'}">${loadError ? `<div class="service-error" role="alert">${icon('help')}<span>${esc(loadError)}</span>${liveButton('Retry', 'refresh', 'secondary small')}</div>` : ''}${content}</main><footer class="app-footer"><span>REA workspace <span>·</span> Static analysis only <span>·</span> No paid phases enabled</span><span>PHASE ZERO</span></footer></div>`;
  }
  function projectRow(p: Project) {
    return `<button class="project-row" data-live="open" data-id="${p.id}">${mark()}<span class="project-name"><strong>${esc(p.app)}</strong><small>${esc(p.goal)}</small></span><span class="row-phase">Initial assessment</span>${badge(status(p), p.status === 'ready' ? 'green' : active(p) ? 'blue' : p.status === 'failed' ? 'amber' : 'neutral')}<span class="row-date">${day(p.created)}</span>${icon('arrow')}</button>`;
  }
  function serviceNotice() {
    if (!config.auth.configured)
      return `<div class="service-notice">${icon('help')}<div><strong>Sign-in is being configured.</strong><p>You can draft an investigation now. Account access and assessments will become available once setup is complete.</p></div></div>`;
    return !config.analysis.modelConfigured || !config.analysis.executorReady
      ? `<div class="service-notice">${icon('help')}<div><strong>Assessments are temporarily unavailable.</strong><p>Your saved projects and source material remain accessible. You can continue when the assessment service is ready.</p></div></div>`
      : '';
  }
  function dashboard() {
    const p = current() || projects[0];
    return `<div class="page-heading"><div><div class="eyebrow">YOUR WORKSPACE</div><h1>A little curiosity. A lot of clarity.</h1><p>Start with an application and a question. Build toward an answer you can verify.</p></div>${liveButton(`${icon('plus')} New investigation`, 'new')}</div>${serviceNotice()}<div class="dashboard-grid"><section class="resume-card"><div class="resume-top"><span class="eyebrow">${p ? 'PICK UP WHERE YOU LEFT OFF' : 'YOUR FIRST INVESTIGATION'}</span>${p ? badge(status(p), p.status === 'ready' ? 'green' : 'blue') : badge('FREE INITIAL ASSESSMENT', 'blue')}</div><div class="resume-body"><span class="app-mark large generic">${icon('search')}</span><div><h2>${p ? esc(p.app) : 'What’s underneath?'}</h2><p>${p ? esc(p.goal) : 'Bring any application and a goal. We’ll establish what the available evidence can tell us.'}</p></div></div><div class="mini-roadmap">${phases.map((name, i) => `<div class="${i === 0 ? 'next' : ''}"><span>${i === 0 && p?.assessment ? icon('check') : i}</span><small>${name}</small></div>`).join('')}</div><div class="resume-bottom"><span>${icon('lock')} ${user ? 'Saved to your account' : 'Create an account after entering your goal'}</span>${liveButton(`${p ? 'Open investigation' : 'Start free assessment'} ${icon('arrow')}`, p ? 'open' : 'new', 'primary', p ? `data-id="${p.id}"` : '')}</div></section><section class="how-card"><span class="eyebrow">A CLEAR PATH FORWARD</span><h2>Big questions.<br/>Manageable steps.</h2><p>Initial findings come from your source material. A proposed scope explains the path forward.</p><div class="how-step">${icon('file')}<div><strong>Bring the evidence</strong><small>Add relevant source files.</small></div></div><div class="how-step">${icon('search')}<div><strong>Inspect safely</strong><small>Static tools in isolated workspaces.</small></div></div><div class="how-step">${icon('shield')}<div><strong>Know the limits</strong><small>Facts, inferences, and unknowns.</small></div></div></section></div><div class="stats-row"><div>${icon('projects')}<span><strong>${projects.length}</strong><small>Saved investigations</small></span></div><div>${icon('file')}<span><strong>${projects.reduce((sum, p) => sum + (p.assessment?.findings.length || 0), 0)}</strong><small>Evidence-backed findings</small></span></div><div>${icon('billing')}<span><strong>$0.00</strong><small>Initial assessment · no payment required</small></span></div></div><section><div class="section-heading"><div><h2>Recent investigations</h2><p>Your goals, source material, and findings stay together.</p></div><a href="#projects" class="text-link">View projects ${icon('arrow')}</a></div><div class="project-table">${projects.slice(0, 3).map(projectRow).join('') || `<div class="empty-state">${icon('projects')}<h3>A good answer starts with a question.</h3><p>Your investigations will appear here after you create one.</p>${liveButton('Start your first investigation', 'new', 'secondary')}</div>`}</div></section>`;
  }
  function projectsPage() {
    const rows = projects.filter((p) => `${p.app} ${p.goal}`.toLowerCase().includes(search.toLowerCase()));
    return `<div class="page-heading"><div><div class="eyebrow">KEEP THE THREAD</div><h1>Your investigations</h1><p>Each application and goal has its own source material and evidence.</p></div>${liveButton(`${icon('plus')} New investigation`, 'new')}</div><label class="search-field live-search">${icon('search')}<input id="live-search" aria-label="Search projects" value="${esc(search)}" placeholder="Search applications or goals…"/></label><div class="project-table">${rows.map(projectRow).join('') || `<div class="empty-state"><h3>${user ? 'No investigations found.' : 'Sign in to see your projects.'}</h3><p>${user ? 'Start with an application and a goal.' : 'Projects are private to the account that created them.'}</p>${liveButton(user ? 'New investigation' : 'Sign in', user ? 'new' : 'login', 'secondary')}</div>`}</div>`;
  }
  function overview(p: Project) {
    const report = p.assessment;
    const pending = active(p);
    return `${serviceNotice()}<section class="progress-card live-progress"><div class="section-heading"><div><span class="eyebrow">PHASE 0 · FREE INITIAL ASSESSMENT</span><h2>${esc(p.activity)}</h2></div>${badge(status(p), p.status === 'ready' ? 'green' : p.status === 'failed' ? 'amber' : 'blue')}</div><p>${pending ? 'The service keeps working when you close the browser. Current activity is shown because analysis duration has no reliable percentage.' : p.status === 'failed' ? 'Completed evidence remains available. Retrying starts a new bounded job using your saved inputs.' : report ? 'Review what was observed, what was inferred, and what remains unknown.' : 'Your application and goal are saved. Add relevant source files so the assessment can establish facts about this target.'}</p><div class="progress-actions">${pending ? liveButton(`${icon('pause')} Cancel assessment`, 'cancel', 'secondary') : liveButton(`${icon(p.files.length ? 'play' : 'upload')} ${p.files.length ? (report || p.status === 'failed' ? 'Run a fresh assessment' : 'Start assessment') : 'Add source material'}`, p.files.length ? 'start' : 'files', 'primary', busy ? 'disabled' : '')}${p.job ? `<small>Last activity ${new Date(p.job.updated).toLocaleTimeString()} · ${p.evidence.length} saved evidence record${p.evidence.length === 1 ? '' : 's'}</small>` : ''}</div></section>${report ? `${report.revision !== p.revision ? `<div class="service-notice">${icon('help')}<p>This report belongs to an earlier goal or source revision. Previous goal: ${esc(report.goal)}. Run a fresh assessment to address the current scope.</p></div>` : ''}<section class="findings-section live-findings"><div class="section-heading"><div><h2>Your first findings</h2><p>${day(report.generatedAt)} · Based on static inspection of ${report.coverage.inspectedFileIds.length} source file${report.coverage.inspectedFileIds.length === 1 ? '' : 's'}.</p></div>${liveButton(`${icon('download')} Export`, 'export', 'secondary small')}</div><div class="assessment-summary">${esc(report.summary)}</div><div class="findings-list">${report.findings.map((finding, i) => `<button class="finding" data-live="finding" data-index="${i}"><span class="finding-icon">${icon('file')}</span><span><small>${finding.confidence === 'observed' ? 'Observed in evidence' : 'Inference from evidence'}</small><strong>${esc(finding.title)}</strong><p>${esc(finding.body)}</p><small>${finding.evidenceIds.length} supporting evidence record${finding.evidenceIds.length === 1 ? '' : 's'}</small></span>${icon('chevron')}</button>`).join('')}</div></section><section class="card live-limits"><h2>What remains unknown</h2><ul>${report.limitations.map((text) => `<li>${esc(text)}</li>`).join('')}</ul></section><section class="proposal-card"><div class="proposal-main"><span class="eyebrow">PROPOSED NEXT INVESTIGATION</span><h2>${esc(report.nextScope.title)}</h2><p>A starting scope to review. This is not a priced offer or a guarantee of feasibility.</p><ul>${report.nextScope.deliverables.map((text) => `<li>${icon('check')}${esc(text)}</li>`).join('')}</ul>${liveButton('Review scope & completion criteria ' + icon('arrow'), 'scope', 'text-link')}</div><div class="proposal-price"><span class="price-label">NO PURCHASE AVAILABLE</span><strong class="quote-pending">Not quoted</strong><span>Pricing and paid execution are not enabled.</span><button class="button secondary" disabled>Awaiting a reviewed quote</button><small>No payment details collected</small></div></section>` : `<section class="live-empty-report card">${icon('search')}<h2>Findings will appear here.</h2><p>Nothing has been assumed about ${esc(p.app)}. The assessment needs source material and a working analysis service before it can produce a report.</p></section>`}`;
  }
  function evidenceView(p: Project) {
    return `<section><div class="section-heading"><div><h2>A finding should have a trail.</h2><p>Saved REA output, bound to its source digest and analysis job.</p></div>${badge(`${p.evidence.length} records`, 'neutral')}</div>${p.evidence.map((e, i) => `<details class="evidence-detail" ${i === 0 ? 'open' : ''}><summary><span class="evidence-number">E${i + 1}</span><span><strong>${esc(e.kind)}</strong><small>${esc(p.files.find((f) => f.id === e.source_id)?.name || 'Source material removed')} · ${day(e.created)}</small></span>${badge('Tool output', 'blue')}${icon('down')}</summary><div><p>Evidence ID: ${esc(e.id)}<br/>Source SHA-256: <code>${esc(e.sha256)}</code></p><pre><code>${esc(JSON.stringify(e.content, null, 2))}</code></pre></div></details>`).join('') || `<div class="empty-state">${icon('file')}<h3>No evidence has been produced yet.</h3><p>Saved records appear as the analysis worker completes each source.</p></div>`}</section>`;
  }
  function filesView(p: Project) {
    return `<section><div class="section-heading"><div><h2>Source material</h2><p>Files are private to your account and are never executed as applications.</p></div>${badge(`${p.files.length} files`, 'neutral')}</div><div class="upload-zone">${icon('upload')}<h3>Add the source material this goal needs.</h3><p>Up to ${Math.floor(config.limits.maxFileBytes / 1048576)} MiB per file · ${config.limits.maxFiles} files per project.<br/>The free assessment inspects up to ${config.limits.analyzedFilesPerAssessment} files, with explicit coverage limits.</p><label class="button secondary file-picker">${icon('plus')} Choose files<input id="live-file-input" type="file" multiple ${busy || active(p) ? 'disabled' : ''}/></label><p>Files remain until you delete them or this project.<br/>Reference links are saved as context and are not fetched.</p></div>${p.files.length ? `<div class="file-list">${p.files.map((f) => `<div>${icon('file')}<span><strong>${esc(f.name)}</strong><small>${(f.bytes / 1048576).toFixed(2)} MiB · SHA-256 ${esc(f.sha256.slice(0, 16))}…</small></span><button class="icon-button" data-live="delete-file" data-id="${f.id}" aria-label="Delete ${esc(f.name)}" ${busy || active(p) ? 'disabled' : ''}>${icon('trash')}</button></div>`).join('')}</div>` : ''}<form class="link-form card" id="live-link-form"><label for="live-target-link">Reference link</label><p>Stored with the project. The service does not fetch this URL.</p><div><input type="url" id="live-target-link" name="link" value="${esc(p.link)}" placeholder="https://example.com/application" maxlength="2000"/><button class="button secondary" type="submit">Save link</button></div></form><div class="privacy-note">${icon('shield')}<p>Delete source files without deleting your saved findings. Reports retain evidence digests and tool output; delete the project to remove those records as well. Cancel an active assessment before changing its inputs.</p></div></section>`;
  }
  function chat(p: Project) {
    return `<aside class="chat-panel" aria-label="Investigation guidance"><div class="chat-heading"><span>${icon('spark')} Investigation context</span><button class="icon-button" data-live="chat" aria-label="Close chat">${icon('close')}</button></div><div class="chat-context">${mark()}<span>${esc(p.app)}<small>Your goal and evidence stay together</small></span></div><div class="chat-messages"><div class="message assistant"><span class="message-mark">${icon('spark')}</span><div><small>PROJECT CONTEXT</small><p>${esc(p.goal)}</p><p>${p.assessment ? 'Your report links each finding to evidence. Review those sources before deciding on further investigation.' : 'Add source material, then start the free initial assessment. REA will inspect it in an isolated workspace; Bedrock will summarize the resulting evidence.'}</p></div></div><div class="chat-suggestions">${liveButton('Review evidence', 'evidence', 'suggestion')}${liveButton('Refine my goal', 'goal', 'suggestion')}</div></div><div class="chat-unavailable">${icon('chat')}<p>Free-form AI chat is not connected yet. Use the project controls to refine your goal and review evidence.</p></div><p class="chat-footer">No scripted assistant replies are presented as live AI.</p></aside>`;
  }
  function workspace() {
    const p = current();
    if (!p) return projectsPage();
    return `<div class="workspace-title"><div><a class="back-link" href="#projects">Projects ${icon('chevron')}</a><div class="project-title">${mark()}<h1>${esc(p.app)}</h1>${badge('Application', 'neutral')}</div><p class="goal-line">${esc(p.goal)} <button class="inline-edit" data-live="goal">Edit goal</button></p></div><div class="workspace-tools">${liveButton(`${icon('download')} Export`, 'export', 'secondary small')}${liveButton(`${icon('chat')} ${chatOpen ? 'Hide' : 'Open'} chat`, 'chat', 'secondary small', `aria-expanded="${chatOpen}"`)}</div></div><div class="phase-track" aria-label="Investigation phases">${phases.map((phase, i) => `<button class="phase-step ${i === 0 ? (p.assessment ? 'done' : 'current') : ''}" data-live="phase" data-index="${i}"><span class="phase-dot">${i === 0 && p.assessment ? icon('check') : String(i).padStart(2, '0')}</span><span><small>PHASE ${i}${i === 0 ? ' · FREE' : ''}</small><strong>${phase}</strong></span>${i > 0 ? icon('lock') : ''}</button>`).join('')}</div><div class="investigation-layout ${chatOpen ? '' : 'chat-hidden'}"><div class="investigation-body"><div class="tabs" role="tablist" aria-label="Project views">${[
      ['overview', 'Overview'],
      ['evidence', 'Evidence'],
      ['files', 'Files & links'],
    ]
      .map(
        ([key, label]) =>
          `<button role="tab" id="live-tab-${key}" aria-selected="${tab === key}" aria-controls="live-project-panel" tabindex="${tab === key ? 0 : -1}" class="${tab === key ? 'active' : ''}" data-live="tab" data-tab="${key}">${label}${key === 'evidence' ? `<span>${p.evidence.length}</span>` : ''}</button>`
      )
      .join(
        ''
      )}<span class="saved-label">${icon('check')} Saved to your account</span></div><div id="live-project-panel" class="tab-content" role="tabpanel" aria-labelledby="live-tab-${tab}">${tab === 'overview' ? overview(p) : tab === 'evidence' ? evidenceView(p) : filesView(p)}</div></div>${chatOpen ? chat(p) : ''}</div>`;
  }
  function settings() {
    return `<div class="page-heading"><div><div class="eyebrow">YOUR WORKSPACE, YOUR CONTROL</div><h1>Settings</h1><p>Account, appearance, and source-material retention.</p></div></div><section class="settings-card card"><h2>Account</h2><p>${user ? `${esc(user.name)}<br/>${esc(user.email)}` : 'Sign in to manage your projects.'}</p>${liveButton(user ? 'Sign out' : 'Sign in', user ? 'logout' : 'login', 'secondary')}</section><section class="settings-card card"><div class="section-heading"><div><h2>Appearance</h2><p>Your preferred theme stays in this browser.</p></div>${liveButton(dark ? 'Switch to light' : 'Switch to dark', 'theme', 'secondary')}</div></section><section class="settings-card card"><h2>Data & retention</h2><p>Source files are retained until deleted. Removing a file keeps the findings and their evidence; deleting a project removes its source files, findings, evidence records, and job history from this service. Your account remains.</p>${projects.map((p) => `<div class="settings-project"><span>${esc(p.app)}</span>${liveButton('Delete project', 'delete-project', 'text-button danger', `data-id="${p.id}"`)}</div>`).join('')}</section>`;
  }
  function billing() {
    return `<div class="page-heading"><div><div class="eyebrow">NO SURPRISES</div><h1>Billing</h1><p>The initial assessment is free.</p></div>${badge('Payments not enabled', 'neutral')}</div><div class="billing-summary card"><div><small>TOTAL PURCHASES</small><h2>$0.00</h2></div><div>${icon('shield')}<span><strong>No payment methods collected</strong><small>Paid phases require reviewed scope, a price, and a real payment integration.</small></span></div></div><div class="empty-state card">${icon('billing')}<h3>No purchases to show.</h3><p>Assessment proposals are unpriced. There is no checkout in the live phase-zero service.</p></div>`;
  }
  function render() {
    const el = document.activeElement as HTMLInputElement | HTMLTextAreaElement | null;
    const focus =
      el?.id && app.contains(el)
        ? { id: el.id, value: el.value, start: el.selectionStart, end: el.selectionEnd }
        : null;
    document.documentElement.classList.toggle('dark', dark);
    app.innerHTML = shell(
      page === 'dashboard'
        ? dashboard()
        : page === 'projects'
          ? projectsPage()
          : page === 'workspace'
            ? workspace()
            : page === 'settings'
              ? settings()
              : billing()
    );
    if (focus) {
      const field = document.getElementById(focus.id) as HTMLInputElement | null;
      if (field) {
        field.value = focus.value;
        field.focus({ preventScroll: true });
        try {
          field.setSelectionRange(focus.start, focus.end);
        } catch {
          /* Selection is only available for text controls. */
        }
      }
    }
  }
  function intake() {
    modal(
      'What do you want to figure out?',
      `<p class="dialog-description">Start with any application and a goal. Add source material once the project is saved.</p><form id="live-intake-form"><label>Application<input name="app" value="${esc(draft.app)}" placeholder="e.g. Instagram or a desktop application" required maxlength="100" autofocus/></label><label>What would success look like?<textarea name="goal" rows="4" required maxlength="1000" placeholder="Describe the behavior or functionality you want to investigate.">${esc(draft.goal)}</textarea></label><button class="button primary full" type="submit">${user ? 'Save investigation' : 'Continue & save my investigation'} ${icon('arrow')}</button><p class="fine-print">Phase zero is free. No payment details required.</p></form>`
    );
  }
  function auth(register = false) {
    modal(
      register ? 'Keep your investigation together.' : 'Welcome back.',
      `<p class="dialog-description">${register ? `Your application and goal are saved in this browser. Create an account or sign in securely, then return to your investigation.` : 'Sign in securely to access your private saved investigations.'}</p><div class="privacy-note">${icon('shield')}<p>Secure sign-in is provided by Amazon Cognito, including email verification and account recovery.</p></div>${config.auth.configured ? liveButton('Continue to secure sign-in ' + icon('arrow'), 'cognito', 'primary full') : '<div class="service-notice"><p>Secure sign-in is being configured. Your draft remains saved; you can continue once setup is complete.</p></div>'}${draft.app ? liveButton('Discard investigation draft', 'discard-draft', 'text-button full') : ''}`
    );
  }
  async function createProject() {
    const result = await api<{ project: Project }>('/api/projects', {
      method: 'POST',
      headers: { 'X-Idempotency-Key': projectRequestId },
      body: JSON.stringify({ app: draft.app, goal: draft.goal }),
    });
    replaceProject(result.project);
    draft = { app: '', goal: '' };
    sessionStorage.removeItem('rea-project-draft');
    sessionStorage.removeItem('rea-project-request');
    projectRequestId = crypto.randomUUID();
    closeModal();
    nav('workspace', result.project.id);
    tab = 'files';
    render();
    toast('Project saved. Add source material to begin.');
  }
  async function exportReport(p: Project) {
    const report = await api(`/api/projects/${p.id}/report`);
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = `rea-${p.id}-assessment.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  document.addEventListener('click', async (event) => {
    const el = (event.target as HTMLElement).closest<HTMLElement>('[data-live]');
    if (!el) return;
    const action = el.dataset.live,
      p = current();
    try {
      switch (action) {
        case 'new':
          intake();
          break;
        case 'open':
          nav('workspace', el.dataset.id);
          break;
        case 'close':
          closeModal();
          break;
        case 'login':
          auth();
          break;
        case 'register':
          auth(true);
          break;
        case 'discard-draft':
          draft = { app: '', goal: '' };
          sessionStorage.removeItem('rea-project-draft');
          sessionStorage.removeItem('rea-project-request');
          projectRequestId = crypto.randomUUID();
          closeModal();
          break;
        case 'cognito':
          location.assign('/auth/login');
          break;
        case 'settings':
          nav('settings');
          break;
        case 'logout': {
          authEpoch += 1;
          const result = await api<{ logoutUrl: string }>('/api/auth/logout', { method: 'POST', body: '{}' });
          user = null;
          csrf = null;
          projects = [];
          activeId = '';
          closeModal();
          nav('dashboard');
          location.assign(result.logoutUrl);
          break;
        }
        case 'theme':
          dark = !dark;
          localStorage.setItem('rea-live-theme', dark ? 'dark' : 'light');
          render();
          break;
        case 'chat':
          chatOpen = !chatOpen;
          render();
          break;
        case 'tab':
          tab = el.dataset.tab || 'overview';
          if (tab === 'evidence') await loadEvidence();
          render();
          document.getElementById(`live-tab-${tab}`)?.focus();
          break;
        case 'files':
          tab = 'files';
          render();
          break;
        case 'evidence':
          closeModal();
          tab = 'evidence';
          await loadEvidence();
          render();
          break;
        case 'refresh':
          config = await api<ServiceConfig>('/api/config');
          await refresh();
          loadError = '';
          render();
          break;
        case 'start':
          if (p && !busy) {
            busy = true;
            render();
            replaceProject(
              (await api<{ project: Project }>(`/api/projects/${p.id}/assessment`, { method: 'POST', body: '{}' }))
                .project
            );
            busy = false;
            render();
          }
          break;
        case 'cancel':
          if (p) {
            replaceProject(
              (await api<{ project: Project }>(`/api/projects/${p.id}/assessment`, { method: 'DELETE' })).project
            );
            render();
          }
          break;
        case 'export':
          if (p) await exportReport(p);
          break;
        case 'goal':
          if (p)
            modal(
              'Refine the question.',
              `<p class="dialog-description">Updating the goal cancels an active assessment. Previous findings and evidence are retained and labeled as belonging to the earlier revision.</p><form id="live-goal-form"><label>Investigation goal<textarea name="goal" rows="4" maxlength="1000" required autofocus>${esc(p.goal)}</textarea></label><button class="button primary full" type="submit">Save goal</button></form>`
            );
          break;
        case 'delete-file':
          if (p)
            modal(
              'Delete this source file?',
              `<p class="dialog-description">The stored source bytes will be removed. Existing findings and evidence are retained.</p>${liveButton('Delete source file', 'confirm-delete-file', 'primary full', `data-id="${el.dataset.id}"`)}`
            );
          break;
        case 'confirm-delete-file':
          if (p) {
            replaceProject(
              (await api<{ project: Project }>(`/api/projects/${p.id}/files/${el.dataset.id}`, { method: 'DELETE' }))
                .project
            );
            closeModal();
            render();
          }
          break;
        case 'delete-project':
          modal(
            'Delete this investigation?',
            `<p class="dialog-description">This deletes the project’s source files, findings, evidence, and job history. Active work is cancelled. This cannot be undone.</p>${liveButton('Delete project', 'confirm-delete-project', 'primary full', `data-id="${el.dataset.id}"`)}`
          );
          break;
        case 'confirm-delete-project':
          await api(`/api/projects/${el.dataset.id}`, { method: 'DELETE' });
          projects = projects.filter((p) => p.id !== el.dataset.id);
          if (activeId === el.dataset.id) activeId = projects[0]?.id || '';
          closeModal();
          render();
          toast('Project data deleted.');
          break;
        case 'finding':
          if (p?.assessment) {
            const f = p.assessment.findings[Number(el.dataset.index)];
            modal(
              esc(f.title),
              `<p class="dialog-description">${esc(f.body)}</p>${badge(f.confidence === 'observed' ? 'Observed' : 'Inferred', 'blue')}<h3>Supporting evidence</h3><ul class="scope-list">${f.evidenceIds.map((id) => `<li>${icon('file')}<code>${esc(id)}</code></li>`).join('')}</ul>${liveButton('Review evidence ' + icon('arrow'), 'evidence', 'primary full')}`,
              true
            );
          }
          break;
        case 'scope':
          if (p?.assessment) {
            const s = p.assessment.nextScope;
            modal(
              esc(s.title),
              `${[
                ['Deliverables', s.deliverables],
                ['Completion criteria', s.completionCriteria],
                ['Exclusions', s.exclusions],
              ]
                .map(
                  ([title, items]) =>
                    `<h3>${title}</h3><ul class="scope-list">${(items as string[]).map((text) => `<li>${icon('check')}${esc(text)}</li>`).join('')}</ul>`
                )
                .join(
                  ''
                )}<div class="demo-checkout-note">${icon('help')}No price has been quoted. Paid execution and checkout are not enabled.</div>`,
              true
            );
          }
          break;
        case 'phase':
          if (Number(el.dataset.index) === 0) {
            tab = 'overview';
            render();
          } else
            modal(
              phases[Number(el.dataset.index)],
              `<p class="dialog-description">This later phase is not available yet. Your initial assessment will propose a scope, but no price or paid execution is enabled.</p>${liveButton('Back to assessment', 'close', 'secondary full')}`
            );
          break;
        case 'mobile':
          document.body.classList.add('nav-open');
          document.querySelector<HTMLElement>('.sidebar')!.inert = false;
          document.querySelector<HTMLElement>('.sidebar a')?.focus();
          break;
        case 'mobile-close':
          document.body.classList.remove('nav-open');
          render();
          break;
        case 'about':
          modal(
            'A real phase-zero workspace.',
            `<p class="dialog-description">Accounts, projects, source storage, and job status are served by the backend. Configured assessments run REA static tools in isolated containers and ask Bedrock to summarize their evidence.</p><p class="scope-copy">The service does not execute target applications or fetch reference links. Cognito handles sign-in, verification, and account recovery. Free-form AI chat, pricing, and paid phases are not connected.</p>${liveButton('Got it', 'close', 'primary full')}`
          );
          break;
      }
    } catch (error) {
      busy = false;
      render();
      toast(error instanceof Error ? error.message : 'Request failed.');
    }
  });
  document.addEventListener('submit', async (event) => {
    const form = event.target as HTMLFormElement;
    if (!form.id.startsWith('live-')) return;
    event.preventDefault();
    const data = new FormData(form),
      p = current();
    const submit = form.querySelector<HTMLButtonElement>('button[type=submit]');
    if (submit) submit.disabled = true;
    try {
      if (form.id === 'live-intake-form') {
        const nextDraft = { app: String(data.get('app')).trim(), goal: String(data.get('goal')).trim() };
        if (nextDraft.app !== draft.app || nextDraft.goal !== draft.goal) projectRequestId = crypto.randomUUID();
        draft = nextDraft;
        sessionStorage.setItem('rea-project-request', projectRequestId);
        if (!draft.app || !draft.goal) throw new Error('Enter an application and a goal.');
        sessionStorage.setItem('rea-project-draft', JSON.stringify(draft));
        if (user) await createProject();
        else auth(true);
      }
      if (form.id === 'live-goal-form' && p) {
        replaceProject(
          (
            await api<{ project: Project }>(`/api/projects/${p.id}/goal`, {
              method: 'PATCH',
              body: JSON.stringify({ goal: String(data.get('goal')).trim() }),
            })
          ).project
        );
        closeModal();
        render();
      }
      if (form.id === 'live-link-form' && p) {
        replaceProject(
          (
            await api<{ project: Project }>(`/api/projects/${p.id}/link`, {
              method: 'PUT',
              body: JSON.stringify({ link: String(data.get('link')).trim() }),
            })
          ).project
        );
        toast('Reference saved. This URL has not been fetched.');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Request failed.';
      const field = form.querySelector('#live-form-error');
      if (field) field.textContent = message;
      else toast(message);
    } finally {
      if (submit) submit.disabled = false;
    }
  });
  document.addEventListener('change', async (event) => {
    const input = event.target as HTMLInputElement,
      p = current();
    if (input.id !== 'live-file-input' || !input.files || !p || busy) return;
    const files = Array.from(input.files);
    if (files.some((f) => f.size === 0 || f.size > config.limits.maxFileBytes)) {
      toast(`Choose nonempty files up to ${Math.floor(config.limits.maxFileBytes / 1048576)} MiB.`);
      return;
    }
    if (p.files.length + files.length > config.limits.maxFiles) {
      toast('This upload exceeds the project file limit.');
      return;
    }
    busy = true;
    render();
    try {
      for (const file of files) {
        toast(`Saving ${file.name}…`);
        const result = await api<{ project: Project }>(`/api/projects/${p.id}/files`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/octet-stream', 'X-File-Name': encodeURIComponent(file.name) },
          body: file,
        });
        replaceProject(result.project);
      }
      toast('Source material saved. Start the assessment when you’re ready.');
    } catch (error) {
      toast(error instanceof Error ? error.message : 'Upload failed.');
    } finally {
      busy = false;
      render();
    }
  });
  document.addEventListener('input', (event) => {
    const input = event.target as HTMLInputElement;
    if (input.id === 'live-search') {
      search = input.value;
      render();
    }
  });
  document.addEventListener('keydown', (event) => {
    const target = event.target as HTMLElement;
    if (target.getAttribute('role') === 'tab' && ['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) {
      event.preventDefault();
      const tabs = ['overview', 'evidence', 'files'];
      tab =
        tabs[
          event.key === 'Home'
            ? 0
            : event.key === 'End'
              ? 2
              : (tabs.indexOf(tab) + (event.key === 'ArrowRight' ? 1 : 2)) % 3
        ];
      if (tab === 'evidence')
        void loadEvidence()
          .then(render)
          .catch((error) => toast(error.message));
      render();
      document.getElementById(`live-tab-${tab}`)?.focus();
    }
    if (event.key === 'Escape' && document.body.classList.contains('nav-open')) {
      document.body.classList.remove('nav-open');
      render();
    }
  });
  window.addEventListener('hashchange', () => {
    document.body.classList.remove('nav-open');
    parseRoute();
    render();
  });
  matchMedia('(max-width: 760px)').addEventListener('change', render);
  app.innerHTML = '<main class="page-main"><h1>Opening your workspace…</h1></main>';
  try {
    config = await api<ServiceConfig>('/api/config');
    const session = await api<{ user: User | null; csrf: string | null }>('/api/session');
    user = session.user;
    csrf = session.csrf;
    await refresh();
    if (user && draft.app && draft.goal) await createProject();
    else {
      parseRoute();
      render();
    }
  } catch (error) {
    app.innerHTML = `<main class="page-main"><h1>The workspace is unavailable.</h1><p>${esc(error instanceof Error ? error.message : 'The service could not be reached.')}</p><p>Reload once the backend is available. Demo findings have not been substituted.</p></main>`;
    return;
  }
  setInterval(async () => {
    if (!user || busy || document.hidden || !projects.some(active)) return;
    try {
      await refresh();
      if (page === 'workspace' && tab === 'evidence') await loadEvidence();
      loadError = '';
      render();
    } catch (error) {
      loadError = error instanceof Error ? error.message : 'Could not refresh projects.';
      render();
    }
  }, 3000);
}
