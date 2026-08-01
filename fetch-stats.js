/**
 * Runs inside GitHub Actions (Node 20, global fetch).
 *
 * Reads your GitHub stats — INCLUDING private repositories — using a Personal
 * Access Token kept in repository secrets, then writes ./data.json.
 *
 * Optionally also merges GitLab activity (INCLUDING private projects) into the
 * same graph when a GITLAB_TOKEN (scope: read_api) is set; skipped if it isn't.
 *
 * SECURITY: data.json is committed to your repo and served publicly by GitHub
 * Pages, so it must contain NUMBERS ONLY. Never write private repo names,
 * descriptions, or any code into it. Tokens never leave the Action runner.
 */

// --- Local convenience: if a .env file sits next to this script, load it.
//     In GitHub Actions there is no .env, so the real repo secrets are used.
//     Real environment variables always win over .env values. ---
(function loadDotEnv() {
  try {
    const fs = require('fs');
    const path = require('path');
    const envPath = path.join(__dirname, '.env');
    if (!fs.existsSync(envPath)) return;
    for (const line of fs.readFileSync(envPath, 'utf8').split(/\r?\n/)) {
      if (line.trim().startsWith('#')) continue;
      const m = line.match(/^\s*([A-Za-z0-9_]+)\s*=\s*(.*?)\s*$/);
      if (!m) continue;
      const key = m[1];
      const val = m[2].replace(/^["']|["']$/g, '');
      if (!(key in process.env)) process.env[key] = val;
    }
  } catch { /* ignore — fall back to real env vars */ }
})();

const TOKEN = process.env.STATS_TOKEN;
const LOGIN = process.env.GH_LOGIN;

if (!TOKEN || !LOGIN) {
  console.error('Missing STATS_TOKEN or GH_LOGIN environment variables.');
  process.exit(1);
}

const QUERY = `
query($login: String!) {
  user(login: $login) {
    createdAt
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount date } }
      }
    }
    publicRepos:  repositories(privacy: PUBLIC,  ownerAffiliations: OWNER) { totalCount }
    privateRepos: repositories(privacy: PRIVATE, ownerAffiliations: OWNER) { totalCount }
    repositories(ownerAffiliations: OWNER, first: 100, orderBy: {field: STARGAZERS, direction: DESC}) {
      nodes {
        stargazerCount
        isFork
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}`;

async function main() {
  const res = await fetch('https://api.github.com/graphql', {
    method: 'POST',
    headers: {
      Authorization: `bearer ${TOKEN}`,
      'Content-Type': 'application/json',
      'User-Agent': 'resume-stats-action',
    },
    body: JSON.stringify({ query: QUERY, variables: { login: LOGIN } }),
  });

  const json = await res.json();
  if (json.errors) {
    console.error('GraphQL errors:', JSON.stringify(json.errors, null, 2));
    process.exit(1);
  }

  const u = json.data.user;
  const c = u.contributionsCollection;
  const repoNodes = u.repositories.nodes || [];
  const totalStars = repoNodes.reduce((s, r) => s + r.stargazerCount, 0);

  // Language breakdown by bytes across non-fork repos — INCLUDES private repos.
  // Only language NAMES + byte counts are recorded (no repo names or code), so data.json stays safe to publish.
  const langBytes = {};
  for (const r of repoNodes) {
    if (r.isFork) continue;
    for (const e of (r.languages && r.languages.edges) || []) {
      langBytes[e.node.name] = (langBytes[e.node.name] || 0) + e.size;
    }
  }

  // Recent activity from the contribution calendar — INCLUDES private contributions.
  const weeks = c.contributionCalendar.weeks || [];
  const last12 = weeks.slice(-12);
  const activityWeeks = last12.map((w) =>
    w.contributionDays.reduce((s, d) => s + d.contributionCount, 0));
  // Date span of each of the 12 buckets — lets us drop GitLab activity into the same weeks.
  const weekRanges = last12.map((w) => ({
    start: w.contributionDays[0].date,
    end:   w.contributionDays[w.contributionDays.length - 1].date,
  }));
  const now = Date.now();
  let last90 = 0, lastDate = null;
  for (const day of weeks.flatMap((w) => w.contributionDays)) {
    const t = new Date(day.date + 'T00:00:00Z').getTime();
    if ((now - t) / 86400000 <= 90) last90 += day.contributionCount;
    if (day.contributionCount > 0) lastDate = day.date; // chronological → ends on latest active day
  }

  // ---------- Optional: merge GitLab activity (INCLUDES private) into the same graph ----------
  // Runs only when GITLAB_TOKEN is set (scope: read_api). Only numbers reach data.json —
  // no project names or code — so it stays safe to publish.
  let gitlab = null;
  if (process.env.GITLAB_TOKEN) {
    try {
      gitlab = await mergeGitLab({
        token: process.env.GITLAB_TOKEN,
        host:  (process.env.GITLAB_HOST || 'https://gitlab.com').replace(/\/+$/, ''),
        weekRanges,
        activityWeeks,
        onActivity: (dateStr, count) => {
          const t = new Date(dateStr + 'T00:00:00Z').getTime();
          if ((now - t) / 86400000 <= 90) last90 += count;
          if (count > 0 && (!lastDate || dateStr > lastDate)) lastDate = dateStr;
        },
      });
      console.log('GitLab merged:', gitlab);
    } catch (e) {
      console.warn('GitLab merge skipped:', e.message);
    }
  }

  const languages = Object.entries(langBytes)
    .sort((a, b) => b[1] - a[1])
    .map(([name, bytes]) => ({ name, bytes }));

  // ---------- Per-year commit counts (GitHub incl. private, + optional GitLab) ----------
  // Powers the year-filterable commit counter on the page. GitHub commits come from
  // contributionsCollection per calendar year; GitLab commits are summed from push events.
  // Only NUMBERS are recorded, so data.json stays safe to publish.
  let contributionsByYear = [];
  try {
    contributionsByYear = await commitsByYear(TOKEN, LOGIN, u.createdAt);
    if (process.env.GITLAB_TOKEN && contributionsByYear.length) {
      const glHost = (process.env.GITLAB_HOST || 'https://gitlab.com').replace(/\/+$/, '');
      const glByYear = await gitlabCommitsByYear(process.env.GITLAB_TOKEN, glHost, contributionsByYear.map((y) => y.year));
      for (const y of contributionsByYear) y.gitlab = glByYear[y.year] || 0;
    }
    contributionsByYear = trimYears(contributionsByYear);
    console.log('Per-year commits:', contributionsByYear);
  } catch (e) {
    console.warn('Per-year commits skipped:', e.message);
  }

  const out = {
    generatedAt:             new Date().toISOString(),
    totalContributionsYear:  c.contributionCalendar.totalContributions, // GitHub, incl. private
    commitContributionsYear: c.totalCommitContributions,
    privateContributions:    c.restrictedContributionsCount,
    publicRepos:             u.publicRepos.totalCount,
    privateRepos:            u.privateRepos.totalCount,
    totalRepos:              u.publicRepos.totalCount + u.privateRepos.totalCount,
    totalStars,
    languages,                                                          // GitHub bytes, incl. private repos
    activity: {                                                         // GitHub + GitLab, incl. private
      weeks:    activityWeeks,
      total:    activityWeeks.reduce((a, b) => a + b, 0),
      last90,
      lastDate,
    },
    contributionsByYear,   // [{year, commits, contributions, private, gitlab}] — GitHub incl. private + GitLab commits
    sources: gitlab ? ['github', 'gitlab'] : ['github'],
    gitlab,   // { projects, stars, contributions12w } when a GitLab token is set, else null
  };

  const fs = require('fs');
  const outJson = JSON.stringify(out, null, 2);
  fs.writeFileSync('data.json', outJson);
  // Also emit data.js (window.__STATS__) so index.html works when opened directly (file://):
  // a <script src> loads under file://, but fetch('./data.json') is blocked there.
  fs.writeFileSync('data.js', 'window.__STATS__ = ' + outJson + ';\n');
  console.log('Wrote data.json + data.js');
}

async function glFetch(host, token, path) {
  const res = await fetch(`${host}/api/v4${path}`, {
    headers: { Authorization: `Bearer ${token}`, 'User-Agent': 'resume-stats-action' },
  });
  if (!res.ok) throw new Error(`GitLab ${path} -> HTTP ${res.status}`);
  return res.json();
}

// Pulls the GitLab token-owner's events (INCLUDES private projects) and drops their commit
// counts into the same 12-week buckets as GitHub; also tallies owned projects + stars.
async function mergeGitLab({ token, host, weekRanges, activityWeeks, onActivity }) {
  let contributions12w = 0;

  if (weekRanges.length) {
    const after = weekRanges[0].start; // YYYY-MM-DD — only fetch events inside the window
    const bucketOf = (d) => {
      for (let i = 0; i < weekRanges.length; i++) {
        if (d >= weekRanges[i].start && d <= weekRanges[i].end) return i;
      }
      return -1;
    };
    for (let page = 1; page <= 20; page++) {
      const events = await glFetch(host, token, `/events?after=${after}&per_page=100&page=${page}`);
      if (!Array.isArray(events) || events.length === 0) break;
      for (const ev of events) {
        const d = (ev.created_at || '').slice(0, 10);
        if (!d) continue;
        const count = ev.push_data ? (ev.push_data.commit_count || 1) : 1; // commits per push, else 1
        const b = bucketOf(d);
        if (b >= 0) { activityWeeks[b] += count; contributions12w += count; }
        onActivity(d, count);
      }
      if (events.length < 100) break;
    }
  }

  // Owned projects (INCLUDES private) -> combined counts, split by visibility.
  const projects = [];
  for (let page = 1; page <= 10; page++) {
    const batch = await glFetch(host, token, `/projects?owned=true&per_page=100&page=${page}`);
    if (!Array.isArray(batch) || batch.length === 0) break;
    projects.push(...batch);
    if (batch.length < 100) break;
  }
  const publicProjects = projects.filter((p) => p.visibility === 'public').length;

  return {
    projects: projects.length,
    publicProjects,
    privateProjects: projects.length - publicProjects, // private + internal
    stars: projects.reduce((s, p) => s + (p.star_count || 0), 0),
    contributions12w,
  };
}

// ---------- Per-year commit helpers ----------
async function ghGraphQL(token, query, variables) {
  const res = await fetch('https://api.github.com/graphql', {
    method: 'POST',
    headers: {
      Authorization: `bearer ${token}`,
      'Content-Type': 'application/json',
      'User-Agent': 'resume-stats-action',
    },
    body: JSON.stringify({ query, variables }),
  });
  const json = await res.json();
  if (json.errors) throw new Error('GraphQL: ' + JSON.stringify(json.errors));
  return json.data;
}

// One aliased GraphQL request pulls every calendar year at once (incl. private commits).
async function commitsByYear(token, login, createdAtIso) {
  const now = new Date();
  const created = new Date(createdAtIso);
  const startYear = created.getFullYear();
  const endYear = now.getFullYear();

  const years = [];
  for (let y = startYear; y <= endYear; y++) years.push(y);

  const parts = years.map((y) => {
    // First year starts at account creation; current year ends "now" (GitHub rejects future dates).
    const from = y === startYear ? created.toISOString() : `${y}-01-01T00:00:00.000Z`;
    const to   = y === endYear   ? now.toISOString()     : `${y}-12-31T23:59:59.000Z`;
    return `y${y}: contributionsCollection(from: "${from}", to: "${to}") {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar { totalContributions }
    }`;
  }).join('\n');

  const data = await ghGraphQL(token, `query($login: String!) { user(login: $login) { ${parts} } }`, { login });
  const u = data.user;
  return years.map((y) => {
    const c = u[`y${y}`];
    return {
      year: y,
      commits:       c.totalCommitContributions,               // GitHub commits, incl. private
      contributions: c.contributionCalendar.totalContributions, // all contribution types, incl. private
      private:       c.restrictedContributionsCount,
      gitlab:        0,
    };
  });
}

// Sums GitLab push commits into calendar-year buckets (INCLUDES private projects).
async function gitlabCommitsByYear(token, host, years) {
  const byYear = {};
  years.forEach((y) => { byYear[y] = 0; });
  const minYear = Math.min(...years);
  const after = `${minYear - 1}-12-31`; // exclusive lower bound → events from minYear onward

  for (let page = 1; page <= 100; page++) {
    let events;
    try { events = await glFetch(host, token, `/events?after=${after}&per_page=100&page=${page}`); }
    catch (e) { break; }
    if (!Array.isArray(events) || events.length === 0) break;
    for (const ev of events) {
      const y = Number((ev.created_at || '').slice(0, 4));
      if (!(y in byYear)) continue;
      if (ev.push_data && ev.push_data.commit_count) byYear[y] += ev.push_data.commit_count; // commits only
    }
    if (events.length < 100) break;
  }
  return byYear;
}

// Drops leading/trailing years with zero activity so the chart starts at the first real commit.
function trimYears(list) {
  const active = list.filter((y) => (y.commits + (y.gitlab || 0)) > 0);
  if (!active.length) return list;
  const first = active[0].year;
  const last = active[active.length - 1].year;
  return list.filter((y) => y.year >= first && y.year <= last);
}

main().catch((err) => { console.error(err); process.exit(1); });
