// Shared logic for the "get ready" clock (ADHD clock). Used by clock.html and dashboard.html.
// No dependencies on the rest of the dashboard, so it can be lifted into a standalone app later.
(function () {
  const DEFAULTS = {
    version: 2,           // bump when the meaning of the settings changes; older saved configs are then ignored
    afterMin: 0,          // keep the red phase this many minutes after school starts
    autoShow: true,       // dashboard switches to the clock during the morning window
    view: 'digital',      // 'digital' | 'analog'
    phases: [
      { id: 'green',  label: 'Gör dig redo',  before: 60, tasks: ['Klä på dig', 'Packa väskan'] },
      { id: 'yellow', label: 'Snart dags',    before: 40, tasks: ['Ät frukost'] },
      { id: 'orange', label: 'Skynda dig',    before: 30, tasks: ['Borsta tänderna', 'Kolla att du har allt'] },
      { id: 'red',    label: 'Gå nu!',        before: 20, tasks: ['Gå till skolan'] },
    ],
    // Phases count back from the school start. `before` = minutes before school start when the phase begins:
    // green 60-40, yellow 40-30, orange 30-20, red 20-0.
    // mode: 'auto' = first lesson in the schedule, 'manual' = fixed start time, 'off' = no schedule
    days: {
      1: { mode: 'auto', start: '08:10' }, 2: { mode: 'auto', start: '08:10' },
      3: { mode: 'auto', start: '08:10' }, 4: { mode: 'auto', start: '08:10' },
      5: { mode: 'auto', start: '08:10' },
      6: { mode: 'off', start: '09:00' }, 0: { mode: 'off', start: '09:00' },
    },
  };

  const COLORS = {
    green:  { bg: '#1f8a3d', fg: '#ffffff' },
    yellow: { bg: '#f2c500', fg: '#1a1a1a' },
    orange: { bg: '#e8650a', fg: '#1a1a1a' },
    red:    { bg: '#d62828', fg: '#ffffff' },
  };

  function clone(o) { return JSON.parse(JSON.stringify(o)); }
  function toMin(s) { const [h, m] = String(s || '').split(':').map(Number); return isFinite(h) && isFinite(m) ? h * 60 + m : null; }
  function fmt(min) { min = ((Math.round(min) % 1440) + 1440) % 1440; return String(Math.floor(min / 60)).padStart(2, '0') + ':' + String(min % 60).padStart(2, '0'); }

  // Merge a stored config over the defaults so new fields never break old saves.
  function normalize(raw) {
    const cfg = clone(DEFAULTS);
    if (!raw || typeof raw !== 'object' || raw.version !== DEFAULTS.version) return cfg;
    ['afterMin'].forEach(k => { if (isFinite(raw[k])) cfg[k] = Math.max(0, +raw[k]); });
    if (typeof raw.autoShow === 'boolean') cfg.autoShow = raw.autoShow;
    if (raw.view === 'digital' || raw.view === 'analog') cfg.view = raw.view;
    if (Array.isArray(raw.phases) && raw.phases.length === 4) {
      cfg.phases = cfg.phases.map((d, i) => {
        const p = raw.phases[i] || {};
        return {
          id: d.id,
          label: typeof p.label === 'string' && p.label.trim() ? p.label.trim() : d.label,
          before: isFinite(p.before) ? Math.max(1, +p.before) : d.before,
          tasks: Array.isArray(p.tasks) ? p.tasks.map(String).map(s => s.trim()).filter(Boolean) : d.tasks,
        };
      });
      // keep the phases in order green > yellow > orange > red (largest "before" first)
      for (let i = 1; i < cfg.phases.length; i++) {
        if (cfg.phases[i].before >= cfg.phases[i - 1].before) cfg.phases[i].before = Math.max(1, cfg.phases[i - 1].before - 1);
      }
    }
    if (raw.days && typeof raw.days === 'object') {
      for (let d = 0; d < 7; d++) {
        const r = raw.days[d]; if (!r) continue;
        if (['auto', 'manual', 'off'].includes(r.mode)) cfg.days[d].mode = r.mode;
        if (toMin(r.start) !== null) cfg.days[d].start = r.start;
      }
    }
    return cfg;
  }

  async function loadConfig() {
    try {
      const r = await fetch('clock_config.json?_=' + Date.now());
      if (r.ok) return normalize(await r.json());
    } catch {}
    try { return normalize(JSON.parse(localStorage.getItem('clockConfig'))); } catch {}
    return clone(DEFAULTS);
  }

  // Saves to the server (so it survives the kiosk's incognito browser) and to localStorage as a fallback.
  async function saveConfig(cfg) {
    try { localStorage.setItem('clockConfig', JSON.stringify(cfg)); } catch {}
    try {
      const r = await fetch('clock_config.json', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cfg) });
      return r.ok;
    } catch { return false; }
  }

  // School start (minutes since midnight) for a given date, or null when there is no schedule that day.
  // `data` is school_data.json (may be null); `dateStr` is YYYY-MM-DD.
  function startFor(date, dateStr, data, cfg) {
    const day = cfg.days[date.getDay()];
    if (!day || day.mode === 'off') return null;
    if (day.mode === 'manual') return toMin(day.start);
    const starts = ((data && data.events) || [])
      .filter(e => !e.allDay && e.kind === 'lesson' && typeof e.start === 'string' && e.start.startsWith(dateStr))
      .map(e => toMin(e.start.split(' ')[1]))
      .filter(m => m !== null);
    if (!starts.length) return null;
    return Math.min(...starts);
  }

  // Which phase are we in? Returns { state: 'none'|'before'|'active'|'done', phase, index, start, untilSchool, untilNext }
  function phaseInfo(nowMin, start, cfg) {
    if (start === null) return { state: 'none', start: null };
    const begins = cfg.phases.map(p => start - p.before);
    if (nowMin < begins[0]) return { state: 'before', start, startsAt: begins[0], untilStart: begins[0] - nowMin, untilSchool: start - nowMin };
    if (nowMin >= start + cfg.afterMin) return { state: 'done', start };
    let index = 0;
    begins.forEach((b, i) => { if (nowMin >= b) index = i; });
    const nextBegin = index + 1 < begins.length ? begins[index + 1] : start + cfg.afterMin;
    return { state: 'active', phase: cfg.phases[index], index, start, untilSchool: start - nowMin, untilNext: nextBegin - nowMin };
  }

  window.ClockCore = { DEFAULTS, COLORS, clone, toMin, fmt, normalize, loadConfig, saveConfig, startFor, phaseInfo };
})();
