#!/usr/bin/env python3
"""Lila's new hits: a record shop you walk around to find new music on Spotify.

ONE-TIME SETUP (Mac)
  1. Open Terminal and type:  python3   (with a space after it)
  2. Drag this file from Finder into the Terminal window.
  3. Type:  --install   (with a space before it) and press Enter.
  4. If macOS asks whether Terminal can access your Desktop, click Allow.
  This saves "Lila's new hits" to your Desktop. Because your Mac makes that copy itself,
  macOS does not show the "Apple could not verify" warning for it. You can then delete
  the file you downloaded.

EVERY TIME AFTER
  Double-click "Lila's new hits" on your Desktop. The shop opens in your browser.
  Keep the small Terminal window open while you use it, and close it when you are done.
  Double-clicking again while it is running just reopens the shop.

OTHER WAY TO RUN IT
  python3 lilas_new_hits.py      (needs Python 3; no extra packages)
"""

import http.server
import json
import ssl
import sys
import threading
import urllib.error
import urllib.request
import webbrowser

PORT = 8080  # must match the redirect URI saved in the Spotify developer dashboard

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lila's new hits</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@400;500;700;900&display=swap" rel="stylesheet">
<style>
  :root {
    --page: #EADBC0;
    --paper: #F6EEDD;
    --cream: #EFE3CB;
    --line: #CBB591;
    --ink: #2B2733;
    --ink-soft: #6A5E52;
    --rust: #B8432A;
    --rust-dark: #9A3720;
    --orange: #D4512E;
    --slate: #3E5A6B;
    --wood: #A87445;
    --wood-dark: #6E4A2E;
    --wood-edge: #8A5D38;
  }
  * { box-sizing: border-box; }
  html { background: var(--page); }
  body {
    margin: 0;
    font-family: "Zen Maru Gothic", ui-rounded, system-ui, sans-serif;
    font-size: 17px; line-height: 1.5; color: var(--ink);
    -webkit-font-smoothing: antialiased;
  }
  [hidden] { display: none !important; }
  a { color: var(--rust); }
  button, input { font: inherit; color: inherit; }
  :focus-visible { outline: 3px solid var(--orange); outline-offset: 3px; }

  main { max-width: 1000px; margin: 0 auto; padding: 22px 20px 60px; }
  .stage { position: relative; }
  canvas { display: block; width: 100%; height: auto; aspect-ratio: 5 / 3; border-radius: 6px; background: var(--ink); cursor: pointer; touch-action: manipulation; }
  #bagbtn { position: absolute; top: 14px; right: 14px; }
  canvas:focus-visible { outline: 2px solid var(--orange); outline-offset: 4px; }

  .btn { background: var(--rust); color: var(--paper); border: 0; border-radius: 999px; padding: 11px 24px; font-weight: 700; cursor: pointer; }
  .btn:hover { background: var(--rust-dark); }
  .btn:disabled { background: var(--line); color: var(--ink-soft); cursor: default; }
  .btn.quiet { background: none; color: var(--ink); box-shadow: inset 0 0 0 2px var(--ink); }
  .btn.quiet:hover { background: rgba(43, 39, 51, 0.06); }
  .link { background: none; border: 0; padding: 0; color: var(--ink-soft); text-decoration: underline; cursor: pointer; font-size: 0.92rem; }
  .link:hover { color: var(--ink); }

  .hint { color: var(--ink-soft); margin: 14px 2px 0; font-size: 0.95rem; }
  .status { font-weight: 700; min-height: 1.5em; margin: 8px 2px; }
  .status.error { color: var(--rust); }
  .pulse::after { content: ""; display: inline-block; width: 9px; height: 9px; margin-left: 10px; border-radius: 50%; background: var(--orange); animation: pulse 1s ease-in-out infinite alternate; }
  @keyframes pulse { from { opacity: 0.2; } to { opacity: 1; } }

  .nowalk { display: flex; flex-wrap: wrap; gap: 6px 18px; align-items: center; margin-top: 4px; color: var(--ink-soft); font-size: 0.92rem; }
  .nowalk .who { margin-left: auto; }

  .setup { background: var(--paper); border: 1.5px solid var(--line); border-radius: 6px; padding: 26px 28px; margin: 20px 0 0; max-width: 640px; }
  .setup h2 { font-size: 1.3rem; font-weight: 900; margin: 0 0 6px; }
  .setup p, .setup ol { color: var(--ink-soft); margin: 0 0 18px; }
  .setup ol { padding-left: 1.2em; }
  .setup .row { display: flex; flex-wrap: wrap; gap: 14px; align-items: end; }
  .setup label { display: grid; gap: 6px; font-size: 0.9rem; color: var(--ink-soft); }
  .setup input { background: #FFFBF2; border: 1.5px solid var(--line); border-radius: 6px; padding: 10px 12px; min-width: min(340px, 100%); color: var(--ink); }

  /* ---------- Crate, listening station, bag ---------- */
  dialog { border: 0; border-radius: 8px; padding: 0; background: var(--paper); color: var(--ink); width: min(980px, 94vw); max-height: 92vh; overflow: auto; }
  dialog#station, dialog#bag { width: min(760px, 94vw); }
  dialog::backdrop { background: rgba(43, 39, 51, 0.6); }
  .cratepanel { padding: 30px 34px 34px; }
  .cratepanel h2 { font-size: 1.7rem; font-weight: 900; margin: 0 0 4px; }
  .cratepanel h2 span { font-weight: 500; color: var(--ink-soft); }
  .cratepanel p { color: var(--ink-soft); margin: 0 0 22px; }
  .binwrap { position: relative; background: var(--wood-dark); border-radius: 4px; margin-bottom: 24px; }
  .binwrap::after { content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 40px; background: var(--wood); border-top: 4px solid var(--wood-edge); border-radius: 0 0 4px 4px; pointer-events: none; z-index: 3;
    background-image: linear-gradient(90deg, transparent 0 calc(50% - 30px), #C9A46A calc(50% - 30px) calc(50% + 30px), transparent calc(50% + 30px)); background-size: 100% 12px; background-repeat: no-repeat; background-position: 0 12px; }
  .bin { display: flex; padding: 30px 30px 0 24px; overflow-x: auto; scrollbar-width: thin; }
  .record { flex: 0 0 auto; width: 176px; height: 176px; margin-right: -12px; padding: 0; border: 0; border-radius: 2px; background: var(--slate); cursor: pointer; overflow: hidden; position: relative;
    transform: rotate(var(--tilt, 0deg)); transition: transform 0.18s ease-out; box-shadow: -4px 0 0 rgba(43, 39, 51, 0.3); }
  .record:hover, .record:focus-visible { transform: translateY(-18px) rotate(0deg); z-index: 2; }
  .record img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .record .blank { display: flex; align-items: center; justify-content: center; height: 100%; padding: 12px; color: var(--paper); font-weight: 700; line-height: 1.15; text-align: center; }
  .record.bagged::before { content: "In your bag"; position: absolute; top: 8px; left: 8px; background: var(--orange); color: var(--paper); font-size: 0.72rem; font-weight: 700; padding: 3px 9px; border-radius: 999px; z-index: 1; }

  .station { display: grid; grid-template-columns: 300px 1fr; gap: 10px 30px; padding: 34px; }
  .sleevewrap { position: relative; width: 210px; height: 210px; }
  .sleeve { position: absolute; inset: 0; border-radius: 2px; overflow: hidden; background: var(--slate); z-index: 1; box-shadow: 0 6px 0 rgba(43, 39, 51, 0.12); }
  .sleeve img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .sleeve .blank { display: flex; align-items: center; justify-content: center; height: 100%; padding: 14px; color: var(--paper); font-weight: 700; text-align: center; }
  .disc { position: absolute; top: 8px; left: 8px; width: 194px; height: 194px; border-radius: 50%;
    background: repeating-radial-gradient(circle, transparent 0 3px, rgba(255, 255, 255, 0.06) 3px 4px), radial-gradient(circle, var(--paper) 0 3%, var(--orange) 3.5% 17%, #1E1B26 17.5%);
    transform: translateX(48%); }
  dialog[open] .disc { animation: slideout 0.6s 0.1s cubic-bezier(0.2, 0.8, 0.3, 1) both; }
  @keyframes slideout { from { transform: translateX(0); } to { transform: translateX(48%); } }
  .station h2 { font-size: 1.9rem; font-weight: 900; line-height: 1.05; margin: 0 0 8px; }
  .station .artist { font-size: 1.15rem; font-weight: 700; margin: 0 0 6px; }
  .station .meta { color: var(--ink-soft); margin: 0 0 4px; font-size: 0.95rem; }
  .station iframe { width: 100%; height: 152px; border: 0; border-radius: 12px; margin: 16px 0 6px; background: var(--cream); }
  .actions { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; margin-top: 12px; }
  .bagpanel { padding: 30px 34px 34px; }
  .bagpanel h2 { font-size: 1.7rem; font-weight: 900; margin: 0 0 14px; }
  .bagpanel ul { list-style: none; margin: 0 0 22px; padding: 0; }
  .bagpanel li { display: grid; grid-template-columns: 52px 1fr auto; gap: 14px; align-items: center; padding: 10px 0; border-top: 1.5px solid var(--line); }
  .bagpanel li:last-child { border-bottom: 1.5px solid var(--line); }
  .bagpanel li img, .bagpanel li .noart { width: 52px; height: 52px; border-radius: 2px; object-fit: cover; background: var(--slate); display: block; }
  .bagpanel .t { font-weight: 700; line-height: 1.2; }
  .bagpanel .a { color: var(--ink-soft); font-size: 0.92rem; }
  .dest { border: 1.5px solid var(--line); border-radius: 6px; padding: 12px 18px 16px; margin: 0 0 16px; }
  .dest legend { font-weight: 700; padding: 0 6px; }
  .dest .opt { display: flex; gap: 10px; align-items: center; margin: 8px 0 4px; }
  .dest input[type=radio] { width: 18px; height: 18px; margin: 0; accent-color: var(--rust); }
  .dest input[type=text], .dest select { display: block; margin: 4px 0 8px 28px; width: calc(100% - 28px); padding: 9px 10px; border: 1.5px solid var(--line); border-radius: 6px; background: #FFFBF2; color: var(--ink); font: inherit; }
  .dest select:disabled { color: var(--ink-soft); }
  .dest .note { margin: 6px 0 0 28px; color: var(--ink-soft); font-size: 0.92rem; }

  @media (max-width: 680px) {
    .station { grid-template-columns: 1fr; padding: 24px; }
    .sleevewrap { width: 170px; height: 170px; }
    .disc { width: 156px; height: 156px; }
    .record { width: 128px; height: 128px; }
    .cratepanel, .bagpanel { padding: 22px; }
  }
  @media (prefers-reduced-motion: reduce) {
    .pulse::after, dialog[open] .disc { animation: none; }
    .record { transition: none; }
  }
</style>
</head>
<body>
<main>
  <div class="stage">
    <canvas id="world" width="960" height="576" tabindex="0" aria-label="A record shop you can walk around. Use the arrow keys to walk, or use the links below the picture."></canvas>
    <button class="btn" id="bagbtn" hidden>Bag (0)</button>
  </div>
  <p class="hint" id="hint"></p>
  <p class="status" id="status" role="status" aria-live="polite"></p>

  <div class="nowalk" id="nowalk" hidden>
    <span>Without walking:</span>
    <span id="jump"></span>
    <button class="link" id="redeliver">Ask for a new delivery</button>
    <button class="link" id="forget">Bring back artists I have already seen</button>
    <button class="link" id="changekey">Change Last.fm key</button>
    <button class="link" id="logout">Disconnect Spotify</button>
    <span class="who" id="who"></span>
  </div>

  <div class="setup" id="step-spotify" hidden>
    <h2>Connect Spotify to open the shop</h2>
    <p>The shop reads your top artists, top songs, and recent plays to decide what to stock, and can save a private playlist. Nothing leaves this computer except requests to Spotify and Last.fm.</p>
    <button class="btn" id="login">Connect Spotify</button>
  </div>

  <div class="setup" id="step-lastfm" hidden>
    <h2>Add a Last.fm key</h2>
    <p>Spotify no longer shares its own recommendations, so similar artists come from Last.fm. The key is free.</p>
    <ol>
      <li>Open <a href="https://www.last.fm/api/account/create" target="_blank" rel="noopener">last.fm/api/account/create</a> and sign in or make an account.</li>
      <li>Type any application name and submit.</li>
      <li>Copy the API key (not the shared secret) and paste it here.</li>
    </ol>
    <div class="row">
      <label>Last.fm API key
        <input type="text" id="lfkey" autocomplete="off" spellcheck="false">
      </label>
      <button class="btn" id="savekey">Save key</button>
    </div>
  </div>
</main>

<dialog id="cratedlg" aria-labelledby="cr-title">
  <div class="cratepanel">
    <h2 id="cr-title"></h2>
    <p id="cr-sub">Artists you have not played. Pull a record out to hear it.</p>
    <div class="binwrap"><div class="bin" id="cr-bin"></div></div>
    <button class="btn quiet" id="cr-close">Step back</button>
  </div>
</dialog>

<dialog id="station" aria-labelledby="st-title">
  <div class="station">
    <div class="sleevewrap"><div class="disc"></div><div class="sleeve" id="st-sleeve"></div></div>
    <div>
      <h2 id="st-title"></h2>
      <p class="artist" id="st-artist"></p>
      <p class="meta" id="st-album"></p>
      <p class="meta" id="st-why"></p>
      <iframe id="st-player" title="Spotify player" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"></iframe>
      <div class="actions">
        <button class="btn" id="st-bag">Put in my bag</button>
        <button class="btn quiet" id="st-back">Put it back</button>
        <a id="st-open" target="_blank" rel="noopener">Open in Spotify</a>
      </div>
    </div>
  </div>
</dialog>

<dialog id="bag" aria-labelledby="bag-title">
  <div class="bagpanel">
    <h2 id="bag-title">Your bag</h2>
    <p id="bag-empty">Your bag is empty. Walk up to a crate, pull a record out, and put it in here.</p>
    <ul id="bag-list"></ul>
    <fieldset class="dest" id="dest">
      <legend>Where should these songs go?</legend>
      <label class="opt"><input type="radio" name="dest" value="new" checked> A new playlist</label>
      <input type="text" id="newname" aria-label="Name for the new playlist">
      <label class="opt"><input type="radio" name="dest" value="existing" id="dest-existing"> One of my playlists</label>
      <select id="plsel" aria-label="Choose one of your playlists" disabled></select>
      <p class="note" id="reconnect" hidden>To add songs to your own playlists, Spotify needs your permission to see and edit them. <button class="link" id="reconnectbtn">Reconnect Spotify</button> You will come back to the street, and your bag stays packed.</p>
    </fieldset>
    <p class="status" id="bag-status" role="status" aria-live="polite"></p>
    <div class="actions">
      <button class="btn" id="checkout">Save to playlist</button>
      <button class="btn quiet" id="bag-close">Keep browsing</button>
    </div>
  </div>
</dialog>

<script>
const CLIENT_ID = 'ca63e815a9774105b474f5b67ac013d4';
const REDIRECT_URI = 'http://127.0.0.1:8080/callback';
const SCOPES = 'user-top-read user-read-recently-played playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public';
const PLAYLIST_SCOPES = ['playlist-read-private', 'playlist-modify-private', 'playlist-modify-public'];
const CRATES = 10;
const PER_CRATE = 5;

// Spotify's sign-in only returns to 127.0.0.1, and saved settings are per address.
if (location.hostname === 'localhost') {
  location.replace('http://127.0.0.1:' + location.port + location.pathname + location.search);
}

const $ = id => document.getElementById(id);
const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch {} },
  del(k) { try { localStorage.removeItem(k); } catch {} },
  json(k, fallback) { try { return JSON.parse(localStorage.getItem(k)) || fallback; } catch { return fallback; } },
};
const arr = x => Array.isArray(x) ? x : (x ? [x] : []);
const norm = s => String(s || '').toLowerCase().normalize('NFKD')
  .replace(/[̀-ͯ]/g, '').replace(/&/g, 'and').replace(/^the\s+/, '').replace(/[^a-z0-9]/g, '');
const clean = s => String(s || '').replace(/["':]/g, ' ').replace(/\s+/g, ' ').trim();
const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
const today = () => { const d = new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); };
const niceDate = () => new Date().toLocaleDateString(undefined, { month: 'short', day: 'numeric' });

let stock = store.json('stock', null);
let bag = store.json('bag', []);
let busy = false;
let current = null;

function setStatus(id, text, kind) {
  const el = $(id);
  el.textContent = text || '';
  el.className = 'status' + (kind ? ' ' + kind : '');
}

/* ---------- Spotify sign-in (PKCE, no secret) ---------- */

function randomString(n) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  return Array.from(crypto.getRandomValues(new Uint8Array(n)), b => chars[b % chars.length]).join('');
}

async function login() {
  const verifier = randomString(64);
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier));
  const challenge = btoa(String.fromCharCode(...new Uint8Array(digest)))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  const state = randomString(16);
  store.set('pkce_verifier', verifier);
  store.set('pkce_state', state);
  location.href = 'https://accounts.spotify.com/authorize?' + new URLSearchParams({
    client_id: CLIENT_ID, response_type: 'code', redirect_uri: REDIRECT_URI, scope: SCOPES,
    code_challenge_method: 'S256', code_challenge: challenge, state,
  });
}

async function tokenRequest(params) {
  const r = await fetch('https://accounts.spotify.com/api/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ client_id: CLIENT_ID, ...params }),
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error_description || j.error || 'Spotify sign-in failed.');
  store.set('sp_access', j.access_token);
  if (j.scope) store.set('sp_scope', j.scope);
  if (j.refresh_token) store.set('sp_refresh', j.refresh_token);
  store.set('sp_expires', String(Date.now() + ((j.expires_in || 3600) - 60) * 1000));
}

function signOut() {
  ['sp_access', 'sp_refresh', 'sp_expires', 'sp_scope', 'pkce_verifier', 'pkce_state'].forEach(store.del);
  playlists = null; meId = null;
}

async function refresh() {
  const token = store.get('sp_refresh');
  const fail = msg => { signOut(); goOutside(); const e = new Error(msg); e.auth = true; return e; };
  if (!token) throw fail('Connect Spotify again to continue.');
  try { await tokenRequest({ grant_type: 'refresh_token', refresh_token: token }); }
  catch { throw fail('Your Spotify connection expired. Connect Spotify again.'); }
}

async function spotify(path, opts = {}, attempt = 0) {
  if (Date.now() > Number(store.get('sp_expires') || 0)) await refresh();
  const r = await fetch('https://api.spotify.com/v1' + path, {
    method: opts.method || 'GET',
    headers: {
      Authorization: 'Bearer ' + store.get('sp_access'),
      ...(opts.body ? { 'Content-Type': 'application/json' } : {}),
    },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (r.status === 401 && attempt === 0) { await refresh(); return spotify(path, opts, 1); }
  if (r.status === 429) {
    const wait = Number(r.headers.get('Retry-After')) || 3;
    if (wait > 30 || attempt >= 3) {
      const e = new Error('Spotify is limiting requests right now. Try again in ' + Math.ceil(Math.max(wait, 60) / 60) + ' minutes.');
      e.limited = true;
      throw e;
    }
    await new Promise(res => setTimeout(res, wait * 1000));
    return spotify(path, opts, attempt + 1);
  }
  const text = await r.text();
  let j = null;
  try { j = text ? JSON.parse(text) : null; } catch {}
  if (!r.ok) {
    let msg = (j && j.error && j.error.message) || ('Spotify returned error ' + r.status + '.');
    if (r.status === 403) msg += ' If this keeps happening, open your app in the Spotify developer dashboard and add your own Spotify email under User Management.';
    const e = new Error(msg);
    e.status = r.status;
    throw e;
  }
  return j;
}

/* ---------- Last.fm ---------- */

let lastfmViaLocal = false;

async function lastfm(params) {
  const qs = new URLSearchParams({ ...params, api_key: store.get('lastfm_key') || '', format: 'json' }).toString();
  let r;
  if (!lastfmViaLocal) {
    try { r = await fetch('https://ws.audioscrobbler.com/2.0/?' + qs); }
    catch { lastfmViaLocal = true; }
  }
  if (lastfmViaLocal) {
    try { r = await fetch('/lastfm?' + qs); }
    catch { throw new Error('Could not reach Last.fm. Check your internet connection.'); }
  }
  const j = await r.json().catch(() => null);
  if (!j) throw new Error('Last.fm sent back something unreadable. Try again.');
  if (j.error === -1) throw new Error(j.message || 'Could not reach Last.fm.');
  if (j.error) {
    const e = new Error(j.message || 'Last.fm error ' + j.error);
    e.code = j.error;
    throw e;
  }
  return j;
}

/* ---------- Stocking the shop ---------- */

function toRecord(t, seed, filed) {
  const imgs = (t.album && t.album.images) || [];
  return {
    id: t.id, uri: t.uri, name: t.name,
    artists: t.artists.map(a => a.name).join(', '),
    album: (t.album && t.album.name) || '',
    year: ((t.album && t.album.release_date) || '').slice(0, 4),
    img: (imgs[1] || imgs[0] || {}).url || '',
    url: (t.external_urls && t.external_urls.spotify) || 'https://open.spotify.com/track/' + t.id,
    because: seed,
    filed: filed || 'if you play ' + seed,
  };
}

async function findRecord(name, knownTracks, taken) {
  let favourites = [];
  try {
    const j = await lastfm({ method: 'artist.gettoptracks', artist: name, limit: 10, autocorrect: 1 });
    favourites = arr(j.toptracks && j.toptracks.track).map(t => norm(t.name));
  } catch {}
  const res = await spotify('/search?type=track&limit=10&q=' + encodeURIComponent('artist:' + clean(name)));
  const items = arr(res && res.tracks && res.tracks.items).filter(t => t && t.uri && !knownTracks.has(t.id)
    && !taken.has(t.uri) && t.artists.some(a => norm(a.name) === norm(name)));
  if (!items.length) return null;
  for (const f of favourites) {
    const hit = items.find(t => norm(t.name) === f);
    if (hit) return hit;
  }
  return items[0];
}

const GENRES = [
  { key: 'daftpunk', label: 'Daft Punk', title: 'Sounds like ', tags: ['french house', 'filter house'], like: ['Daft Punk'] },
  { key: 'oldies', label: 'Oldies', tags: ['oldies', '60s', '50s'] },
  { key: 'baladas', label: 'Baladas', tags: ['balada', 'bolero', 'balada romantica'], like: ['José José'] },
  { key: 'latinafro', label: 'Latin/Afro House', tags: ['afro house', 'afrohouse', 'latin house', 'tribal house'] },
];
const TOTAL_CRATES = CRATES + GENRES.length;

async function genreCandidates(g) {
  const soft = e => { if (!e.code) throw e; return []; };
  const tagged = Promise.all((g.tags || []).map(tag => lastfm({ method: 'tag.gettopartists', tag, limit: 50, page: 1 + Math.floor(Math.random() * 2) })
    .then(j => arr(j.topartists && j.topartists.artist).map(a => a.name)).catch(soft)));
  const similar = Promise.all((g.like || []).map(name => lastfm({ method: 'artist.getsimilar', artist: name, limit: 60, autocorrect: 1 })
    .then(j => arr(j.similarartists && j.similarartists.artist).map(a => a.name)).catch(soft)));
  // Alternate between "sounds like" artists and genre-tag artists so neither crowds out the other.
  const a = shuffle((await similar).flat()), b = shuffle((await tagged).flat()), out = [];
  for (let i = 0; i < Math.max(a.length, b.length); i++) { if (a[i]) out.push(a[i]); if (b[i]) out.push(b[i]); }
  return out;
}

// Turns a ranked list of candidate artists into up to five records, one song per artist.
async function fillCrate(cands, ctx2) {
  const { knownTracks, taken, stocked, seen, seed, filed } = ctx2;
  const records = [];
  for (let i = 0; i < cands.length && records.length < PER_CRATE; i += 3) {
    const found = await Promise.all(cands.slice(i, i + 3).map(async c => {
      try { return { c, t: await findRecord(c.name, knownTracks, taken) }; }
      catch (e) { if (e.auth || e.limited) throw e; return { c, t: null }; }
    }));
    for (const f of found) {
      if (!f.t || taken.has(f.t.uri) || records.length >= PER_CRATE) continue;
      taken.add(f.t.uri);
      stocked.add(f.c.key);
      seen.add(f.c.key);
      records.push(toRecord(f.t, seed, filed));
    }
  }
  return records;
}

async function deliver() {
  if (busy) return;
  busy = true;
  $('redeliver').disabled = true;
  if ($('cratedlg').open) $('cratedlg').close();
  stock = { v: 5, date: today(), crates: [], genres: [] };
  renderJump();
  try {
    setStatus('status', 'Checking what you have been playing', 'pulse');
    const empty = () => ({ items: [] });
    const [aShort, aMid, aLong, tShort, tMid, recent] = await Promise.all([
      spotify('/me/top/artists?limit=50&time_range=short_term'),
      spotify('/me/top/artists?limit=50&time_range=medium_term').catch(empty),
      spotify('/me/top/artists?limit=50&time_range=long_term').catch(empty),
      spotify('/me/top/tracks?limit=50&time_range=short_term').catch(empty),
      spotify('/me/top/tracks?limit=50&time_range=medium_term').catch(empty),
      spotify('/me/player/recently-played?limit=50').catch(empty),
    ]);

    const known = new Set();
    const knownTracks = new Set();
    const names = o => arr(o && o.items).map(a => a.name);
    [aShort, aMid, aLong].forEach(o => names(o).forEach(n => known.add(norm(n))));
    [tShort, tMid].forEach(o => arr(o && o.items).forEach(t => { knownTracks.add(t.id); t.artists.forEach(a => known.add(norm(a.name))); }));
    const recentArtists = [];
    arr(recent && recent.items).forEach(p => {
      if (!p.track) return;
      knownTracks.add(p.track.id);
      p.track.artists.forEach(a => known.add(norm(a.name)));
      if (p.track.artists[0]) recentArtists.push(p.track.artists[0].name);
    });

    // One crate per artist you play: mostly recent favourites, plus two long-standing ones.
    const seeds = [];
    const add = (list, n) => { for (const name of list) { if (n <= 0) break; if (!seeds.some(s => norm(s) === norm(name))) { seeds.push(name); n--; } } };
    add(shuffle(names(aShort).slice(0, 15)), 5);
    add(shuffle(names(aMid).slice(0, 20)), 3);
    add(shuffle(names(aLong).slice(0, 20)), 2);
    add(shuffle([...names(aShort), ...names(aMid), ...names(aLong), ...recentArtists]), CRATES + 4 - seeds.length);

    const seen = new Set(store.json('seen_artists', []));
    const stocked = new Set();
    const taken = new Set();
    let keyRejected = false;
    const save = () => { store.set('stock', JSON.stringify(stock)); store.set('seen_artists', JSON.stringify([...seen].slice(-1200))); renderJump(); };
    const progress = () => setStatus('status', 'Unpacking today\'s delivery: crate ' + Math.min(TOTAL_CRATES, stock.crates.length + stock.genres.length + 1) + ' of ' + TOTAL_CRATES, 'pulse');

    for (const seed of seeds) {
      if (stock.crates.length >= CRATES) break;
      progress();
      let j;
      try { j = await lastfm({ method: 'artist.getsimilar', artist: seed, limit: 60, autocorrect: 1 }); }
      catch (e) { if (!e.code) throw e; if (e.code === 10 || e.code === 26) keyRejected = true; continue; }
      let cands = arr(j.similarartists && j.similarartists.artist)
        .map(a => ({ name: a.name, key: norm(a.name), match: Number(a.match) || 0 }))
        .filter(c => c.key && !known.has(c.key) && !stocked.has(c.key));
      const unseen = cands.filter(c => !seen.has(c.key));
      if (unseen.length >= PER_CRATE) cands = unseen;
      cands = cands.map(c => ({ ...c, rank: c.match * (0.7 + Math.random() * 0.6) })).sort((a, b) => b.rank - a.rank).slice(0, PER_CRATE * 3);
      const records = await fillCrate(cands, { knownTracks, taken, stocked, seen, seed, filed: 'if you play ' + seed });
      if (records.length) { stock.crates.push({ seed, records }); save(); }
    }

    if (keyRejected && !stock.crates.length) {
      store.del('lastfm_key');
      goOutside();
      setStatus('status', 'Last.fm did not accept that key. Paste it again.', 'error');
      return;
    }

    // Genre crates: artists Last.fm listeners tag with each genre, minus anyone you already play.
    for (const g of GENRES) {
      progress();
      const skip = new Set(GENRES.flatMap(x => x.like || []).map(norm));
      const uniq = new Map();
      (await genreCandidates(g)).forEach(n => { const key = norm(n); if (key && !uniq.has(key) && !known.has(key) && !stocked.has(key) && !skip.has(key)) uniq.set(key, { name: n, key }); });
      let cands = [...uniq.values()];
      const unseen = cands.filter(c => !seen.has(c.key));
      if (unseen.length >= PER_CRATE) cands = unseen;
      cands = cands.slice(0, PER_CRATE * 3);
      const records = await fillCrate(cands, { knownTracks, taken, stocked, seen, seed: g.label, filed: g.title ? 'sounds like ' + g.label : 'the ' + g.label + ' crate' });
      if (records.length) { stock.genres.push({ seed: g.label, genre: g.key, title: g.title, records }); save(); }
    }

    if (!stock.crates.length && !stock.genres.length) {
      setStatus('status', 'Nothing new turned up. Select "Bring back artists I have already seen" and ask for a new delivery.', 'error');
      return;
    }
    describeStock();
  } catch (e) {
    if (e.auth) setStatus('status', e.message, 'error');
    else setStatus('status', (e.message || 'Something went wrong.') + (stock.crates.length + stock.genres.length ? ' The crates that arrived are on the floor.' : ' Walk to the delivery boxes to try again.'), 'error');
  } finally {
    busy = false;
    $('redeliver').disabled = false;
  }
}

const allCrates = () => stock ? [...(stock.crates || []), ...(stock.genres || [])] : [];

function describeStock() {
  const all = allCrates();
  const n = all.reduce((s, c) => s + c.records.length, 0);
  setStatus('status', n ? 'Delivery of ' + niceDate() + ': ' + n + ' records by artists you have not played, in ' + all.length + ' crates.' : '');
}

/* ---------- Crate, listening station, bag ---------- */

const SLEEVE_COLOURS = ['#B5452F', '#3E5A6B', '#6E4A2E'];
const sleeveColour = rec => SLEEVE_COLOURS[rec.name.length % SLEEVE_COLOURS.length];

function cover(rec) {
  if (rec.img) {
    const img = document.createElement('img');
    img.src = rec.img; img.alt = ''; img.loading = 'lazy';
    return img;
  }
  const d = document.createElement('div');
  d.className = 'blank';
  d.style.background = sleeveColour(rec);
  d.textContent = rec.artists;
  return d;
}

function openCrate(crate) {
  if (!crate) return;
  stopWalking();
  const pre = document.createElement('span');
  pre.textContent = crate.genre ? (crate.title || 'Genre crate: ') : 'If you play ';
  $('cr-title').replaceChildren(pre, crate.seed);
  $('cr-sub').textContent = crate.title ? 'Artists with a sound like ' + crate.seed + ' that you have not played. Pull a record out to hear it.'
    : crate.genre ? 'Artists in this genre you have not played. Pull a record out to hear it.' : 'Artists you have not played. Pull a record out to hear it.';
  const bin = $('cr-bin');
  bin.replaceChildren();
  crate.records.forEach((rec, n) => {
    const b = document.createElement('button');
    b.className = 'record';
    b.dataset.id = rec.id;
    b.style.setProperty('--tilt', ((rec.name.length + n * 7) % 7 - 3) * 0.7 + 'deg');
    b.setAttribute('aria-label', rec.name + ' by ' + rec.artists + '. Pull it out to listen.');
    b.append(cover(rec));
    b.addEventListener('click', () => openStation(rec));
    bin.append(b);
  });
  markBagged();
  if (!$('cratedlg').open) $('cratedlg').showModal();
  const first = bin.querySelector('.record');
  if (first) first.focus({ preventScroll: true });
}

function renderJump() {
  const box = $('jump');
  box.replaceChildren();
  allCrates().forEach(c => {
    const b = document.createElement('button');
    b.className = 'link';
    b.textContent = c.seed;
    b.setAttribute('aria-label', (c.genre ? 'Open the ' + c.seed + ' crate' : 'Open the crate for ' + c.seed));
    b.addEventListener('click', () => openCrate(c));
    box.append(b, ' ');
  });
}

function markBagged() {
  const ids = new Set(bag.map(r => r.id));
  document.querySelectorAll('.record').forEach(b => b.classList.toggle('bagged', ids.has(b.dataset.id)));
  $('bagbtn').textContent = 'Bag (' + bag.length + ')';
}

function openStation(rec) {
  current = rec;
  $('st-sleeve').replaceChildren(cover(rec));
  $('st-title').textContent = rec.name;
  $('st-artist').textContent = rec.artists;
  $('st-album').textContent = [rec.album, rec.year].filter(Boolean).join(', ');
  $('st-why').textContent = 'Filed under: ' + (rec.filed || 'if you play ' + rec.because);
  $('st-player').src = 'https://open.spotify.com/embed/track/' + encodeURIComponent(rec.id);
  $('st-open').href = rec.url;
  updateStationButton();
  $('station').showModal();
}

function updateStationButton() {
  const inBag = current && bag.some(r => r.id === current.id);
  $('st-bag').textContent = inBag ? 'Take out of my bag' : 'Put in my bag';
}

function toggleBag(rec) {
  const i = bag.findIndex(r => r.id === rec.id);
  if (i >= 0) bag.splice(i, 1); else bag.push(rec);
  store.set('bag', JSON.stringify(bag));
  markBagged();
}

function openBag() {
  stopWalking();
  setStatus('bag-status', '');
  renderBag();
  if (!$('bag').open) $('bag').showModal();
}

let playlists = null;
let meId = null;
const hasPlaylistAccess = () => { const s = (store.get('sp_scope') || '').split(' '); return PLAYLIST_SCOPES.every(n => s.includes(n)); };
const destMode = () => (document.querySelector('input[name=dest]:checked') || {}).value;

function renderBag() {
  const list = $('bag-list');
  list.replaceChildren();
  bag.forEach(rec => {
    const li = document.createElement('li');
    let art;
    if (rec.img) { art = document.createElement('img'); art.src = rec.img; art.alt = ''; }
    else { art = document.createElement('div'); art.className = 'noart'; }
    const info = document.createElement('div');
    const t = document.createElement('div'); t.className = 't'; t.textContent = rec.name;
    const a = document.createElement('div'); a.className = 'a'; a.textContent = rec.artists;
    info.append(t, a);
    const out = document.createElement('button');
    out.className = 'link';
    out.textContent = 'Take out';
    out.setAttribute('aria-label', 'Take ' + rec.name + ' out of my bag');
    out.addEventListener('click', () => { toggleBag(rec); renderBag(); });
    li.append(art, info, out);
    list.append(li);
  });
  const has = bag.length > 0;
  $('bag-empty').hidden = has;
  $('dest').hidden = !has;
  $('checkout').hidden = !has;
  $('checkout').disabled = false;
  if (!$('newname').value) $('newname').value = 'New hits, ' + niceDate();
  const access = hasPlaylistAccess();
  $('reconnect').hidden = access;
  $('dest-existing').disabled = !access;
  $('plsel').hidden = !access;
  if (!access && destMode() === 'existing') document.querySelector('input[name=dest][value=new]').checked = true;
  syncDest();
  if (has && access && !playlists) loadPlaylists();
}

function syncDest() {
  const existing = destMode() === 'existing';
  $('newname').disabled = existing;
  $('plsel').disabled = !existing || !playlists || !playlists.length;
  $('checkout').textContent = existing ? 'Add to this playlist' : 'Save to a new playlist';
}

function fillSelect(message) {
  const sel = $('plsel');
  sel.replaceChildren();
  if (message) { const o = document.createElement('option'); o.textContent = message; sel.append(o); syncDest(); return; }
  const last = store.get('last_playlist');
  playlists.forEach(pl => {
    const o = document.createElement('option');
    o.value = pl.id;
    const total = pl.items && typeof pl.items.total === 'number' ? pl.items.total : pl.tracks && typeof pl.tracks.total === 'number' ? pl.tracks.total : null;
    o.textContent = pl.name + (total === null ? '' : ' (' + total + (total === 1 ? ' song)' : ' songs)'));
    if (pl.id === last) o.selected = true;
    sel.append(o);
  });
  syncDest();
}

async function loadPlaylists() {
  fillSelect('Loading your playlists');
  try {
    if (!meId) meId = (await spotify('/me')).id;
    const all = [];
    for (let offset = 0; offset < 1000; offset += 50) {
      const j = await spotify('/me/playlists?limit=50&offset=' + offset);
      const items = arr(j && j.items).filter(Boolean);
      all.push(...items);
      if (!j || !j.next || items.length < 50) break;
    }
    playlists = all.filter(pl => (pl.owner && pl.owner.id === meId) || pl.collaborative);
    if (playlists.length) fillSelect();
    else fillSelect('You have no playlists you can add songs to');
  } catch (e) {
    playlists = null;
    fillSelect('Could not load your playlists');
    if (e.status === 401 || e.status === 403) { store.del('sp_scope'); $('reconnect').hidden = false; }
    setStatus('bag-status', e.message || 'Could not load your playlists.', 'error');
  }
}

async function addItems(id, uris) {
  for (let i = 0; i < uris.length; i += 100) {
    const body = { uris: uris.slice(i, i + 100) };
    try { await spotify('/playlists/' + id + '/items', { method: 'POST', body }); }
    catch (e) { if (e.status !== 404) throw e; await spotify('/playlists/' + id + '/tracks', { method: 'POST', body }); }
  }
}

// Songs already in the playlist are skipped. Reads up to 1,000 songs; if that fails, adds everything.
async function alreadyIn(id) {
  const have = new Set();
  try {
    for (let offset = 0; offset < 1000; offset += 100) {
      const j = await spotify('/playlists/' + id + '/items?limit=100&offset=' + offset);
      const items = arr(j && j.items);
      items.forEach(x => { const t = x && (x.item || x.track); if (t && t.uri) have.add(t.uri); });
      if (!j || !j.next || items.length < 100) break;
    }
  } catch (e) { if (e.auth || e.limited) throw e; }
  return have;
}

function playlistLink(pl) {
  const link = document.createElement('a');
  link.href = (pl.external_urls && pl.external_urls.spotify) || 'https://open.spotify.com/playlist/' + pl.id;
  link.target = '_blank'; link.rel = 'noopener';
  link.textContent = 'Open it in Spotify';
  return link;
}

function emptyBag() {
  bag = [];
  store.set('bag', '[]');
  markBagged();
  renderBag();
  $('bag-empty').hidden = true;
}

async function checkout() {
  if (!bag.length) return;
  const existing = destMode() === 'existing';
  const uris = bag.map(r => r.uri);
  $('checkout').disabled = true;
  try {
    if (existing) {
      const pl = (playlists || []).find(x => x.id === $('plsel').value);
      if (!pl) { setStatus('bag-status', 'Choose a playlist first.', 'error'); $('checkout').disabled = false; return; }
      setStatus('bag-status', 'Adding to "' + pl.name + '"', 'pulse');
      const have = await alreadyIn(pl.id);
      const fresh = uris.filter(u => !have.has(u));
      if (fresh.length) await addItems(pl.id, fresh);
      store.set('last_playlist', pl.id);
      if (pl.items && typeof pl.items.total === 'number') pl.items.total += fresh.length;
      else if (pl.tracks && typeof pl.tracks.total === 'number') pl.tracks.total += fresh.length;
      const skipped = uris.length - fresh.length;
      const msg = fresh.length
        ? 'Added ' + fresh.length + (fresh.length === 1 ? ' song' : ' songs') + ' to "' + pl.name + '".' + (skipped ? ' ' + skipped + ' ' + (skipped === 1 ? 'was' : 'were') + ' already in it.' : '') + ' '
        : 'All of these songs were already in "' + pl.name + '". ';
      emptyBag();
      fillSelect();
      $('bag-status').className = 'status';
      $('bag-status').replaceChildren(msg, playlistLink(pl));
    } else {
      const name = $('newname').value.trim() || 'New hits, ' + niceDate();
      setStatus('bag-status', 'Saving to a new playlist', 'pulse');
      const pl = await spotify('/me/playlists', {
        method: 'POST',
        body: { name, description: 'Picked up at Lila\'s new hits: artists I had not played yet.', public: false },
      });
      await addItems(pl.id, uris);
      if (playlists) playlists.unshift({ ...pl, items: { total: uris.length } });
      emptyBag();
      $('newname').value = '';
      $('bag-status').className = 'status';
      $('bag-status').replaceChildren('Saved to a new playlist called "' + pl.name + '". ', playlistLink(pl));
    }
  } catch (e) {
    setStatus('bag-status', 'Not saved. ' + (e.message || ''), 'error');
    $('checkout').disabled = false;
  }
}

/* ---------- The world you walk around (side view) ---------- */

const W = 960, H = 576;
const C = {
  paper: '#F6EEDD', cream: '#EFE3CB', creamShade: '#D8C5A2', wall: '#E9D5AF', wallTop: '#DCC398',
  ink: '#2B2733', navy: '#262433', slate: '#3E5A6B', slateDark: '#35505F', teal: '#5D7F8C', mist: '#A9B8B0',
  wood: '#A87445', woodDark: '#6E4A2E', woodDeep: '#4A3122', woodLight: '#C28E5C',
  orange: '#D4512E', rust: '#B8432A', red: '#B5452F', brass: '#C9A46A', card: '#F3E9D2', chalk: '#2F3A38',
  skin: '#F2D4B8', skinShade: '#E0B898', hair: '#2A2227', floor: '#B4885C', floorDark: '#A07750',
  pave: '#CDBB9C', road: '#6B6370', box: '#C9A46A', boxDark: '#B08B55',
};
const FONT = '"Zen Maru Gothic", ui-rounded, system-ui, sans-serif';
const canvas = $('world');
const ctx = canvas.getContext('2d');
const still = matchMedia('(prefers-reduced-motion: reduce)').matches;

const SHOP_W = 3990;
const FEET = { street: 522, shop: 526 };
const DOOR = { kind: 'door', x: 592, w: 120 };
const EXIT = { kind: 'exit', x: 34, w: 108 };
const COUNTER = { kind: 'counter', x: 160, w: 240 };
const BINS = Array.from({ length: CRATES }, (_, i) => 540 + i * 220).map(cx => ({ kind: 'crate', x: cx - 90, w: 180 }));
const GENRE_BINS = [2840, 3060, 3280, 3500].map(cx => ({ kind: 'genre', x: cx - 90, w: 180 }));
const GENRE_SIGN = { x: 3170 };
const BOXES = { kind: 'boxes', x: 3620, w: 138 };
const WINDOW = { x: 3800, y: 34, w: 170, h: 276 };
const LAMPS = [330, 760, 1180, 1600, 2020, 2440, 2720, 2950, 3390, 3690];

const game = { scene: 'street', p: { x: 200, dir: 1, moving: false, step: 0 }, keys: new Set(), target: null, pending: null, active: null, quiet: false, cam: 0, fade: 0, fading: null, t: 0 };
window.__game = game;

function stopWalking() { game.keys.clear(); game.target = null; game.pending = null; }
const ready = () => !!store.get('sp_refresh') && !!store.get('lastfm_key');
const freshStock = () => !!(stock && stock.v === 5 && stock.date === today() && allCrates().length);
const camFor = x => game.scene === 'shop' ? Math.min(SHOP_W - W, Math.max(0, x - W / 2)) : 0;

function interactables() {
  if (game.scene === 'street') {
    return [{ ...DOOR, go: tryEnter, label: () => ready() ? 'Go inside'
      : store.get('sp_refresh') ? 'Closed. Add a Last.fm key below to open it' : 'Closed. Connect Spotify below to open it' }];
  }
  const list = [
    { ...EXIT, go: () => switchScene('street', { x: DOOR.x + DOOR.w / 2, dir: 1 }), label: () => 'Step outside' },
    { ...COUNTER, go: openBag, label: () => 'Open your bag (' + bag.length + ')' },
  ];
  BINS.forEach((b, i) => {
    const c = stock && stock.crates && stock.crates[i];
    if (c) list.push({ ...b, i, go: () => openCrate(c), label: () => 'Flip through: if you play ' + c.seed });
  });
  GENRE_BINS.forEach((b, i) => {
    const c = stock && stock.genres && stock.genres[i];
    if (c) list.push({ ...b, i, go: () => openCrate(c), label: () => c.title ? 'Flip through: sounds like ' + c.seed : 'Flip through the ' + c.seed + ' crate' });
  });
  if (!busy) list.push({ ...BOXES, go: deliver, label: () => 'Ask for a new delivery' });
  return list;
}

function bounds() { return game.scene === 'street' ? { x1: 40, x2: 920 } : { x1: 60, x2: SHOP_W - 40 }; }

function switchScene(to, place) {
  if (game.fading) return;
  stopWalking();
  const swap = () => {
    game.scene = to;
    Object.assign(game.p, place, { moving: false });
    game.cam = camFor(game.p.x);
    game.active = null;
    game.quiet = true;
    syncChrome();
    if (to === 'shop') arriveInShop();
  };
  if (still) { swap(); return; }
  game.fading = { t: 0, swap, done: false };
}

function arriveInShop() {
  showWho();
  if (freshStock()) { renderJump(); describeStock(); }
  else deliver();
}

function tryEnter() {
  if (!ready()) {
    setStatus('status', store.get('sp_refresh') ? 'The shop is closed. Add a Last.fm key below to open it.' : 'The shop is closed. Connect Spotify below to open it.');
    stopWalking();
    return;
  }
  setStatus('status', '');
  switchScene('shop', { x: 104, dir: 1 });
}

function goOutside() {
  ['station', 'cratedlg', 'bag'].forEach(id => { if ($(id).open) $(id).close(); });
  if (game.scene !== 'street') {
    game.fading = null;
    stopWalking();
    game.scene = 'street';
    Object.assign(game.p, { x: DOOR.x + DOOR.w / 2, dir: 1, moving: false });
    game.cam = 0;
    game.quiet = true;
  }
  syncChrome();
}

function syncChrome() {
  const inside = game.scene === 'shop';
  const connected = !!store.get('sp_refresh');
  const hasKey = !!store.get('lastfm_key');
  $('bagbtn').hidden = !inside;
  $('nowalk').hidden = !inside;
  $('step-spotify').hidden = inside || connected;
  $('step-lastfm').hidden = inside || !connected || hasKey;
  $('hint').textContent = inside
    ? 'Walk with the arrow keys or A and D. Stop at a crate and press E, or click it. Genre crates are past the crates for your artists. The counter holds your bag, and the door on the left leads outside.'
    : 'Walk with the arrow keys or A and D, or click where you want to go. At the door, press E or the up arrow to go in.';
  markBagged();
}

/* ---------- Movement ---------- */

const motes = Array.from({ length: 48 }, (_, i) => {
  const r = seeded(300 + i);
  return { x: WINDOW.x - 480 + r() * 650, y: 40 + r() * 500, vx: -5 - r() * 7, vy: (r() - 0.5) * 5, r: 0.8 + r() * 1.7, a: 0.25 + r() * 0.45, ph: r() * 6 };
});

function update(dt) {
  const p = game.p;
  game.t += dt;
  if (game.fading) {
    const f = game.fading;
    f.t += dt / 0.3;
    if (!f.done && f.t >= 1) { f.swap(); f.done = true; }
    game.fade = f.t < 1 ? f.t : Math.max(0, 2 - f.t);
    if (f.t >= 2) { game.fading = null; game.fade = 0; }
    if (!f.done) return;
  }
  let dx = 0;
  if (game.keys.has('left')) dx -= 1;
  if (game.keys.has('right')) dx += 1;
  if (dx) { game.target = null; game.pending = null; }
  else if (game.target !== null) {
    const d = game.target - p.x;
    if (Math.abs(d) < 4) {
      p.x = game.target;
      const go = game.pending;
      game.target = null; game.pending = null;
      p.moving = false;
      if (go) { game.quiet = false; go(); }
      return;
    }
    dx = Math.sign(d);
  }
  const b = bounds();
  let moved = 0;
  if (dx) {
    const nx = Math.min(b.x2, Math.max(b.x1, p.x + dx * 270 * dt));
    moved = Math.abs(nx - p.x);
    p.x = nx;
    p.dir = dx;
  }
  p.moving = moved > 0.05;
  if (p.moving) { p.step += dt * 10; game.quiet = false; }

  game.active = null;
  if (!game.quiet) {
    let best = Infinity;
    interactables().forEach(o => {
      if (p.x < o.x - 16 || p.x > o.x + o.w + 16) return;
      const d = Math.abs(p.x - (o.x + o.w / 2));
      if (d < best) { best = d; game.active = o; }
    });
  }
  game.cam += (camFor(p.x) - game.cam) * Math.min(1, dt * 6);

  if (game.scene === 'shop' && !still) {
    motes.forEach(m => {
      m.x += m.vx * dt;
      m.y += (m.vy + Math.sin(game.t * 0.8 + m.ph) * 4) * dt;
      if (m.x < WINDOW.x - 480) { m.x = WINDOW.x + 170; m.y = 40 + Math.random() * 500; }
      if (m.y < 30) m.y = 540; else if (m.y > 545) m.y = 40;
    });
  }
}

/* ---------- Drawing helpers ---------- */

function seeded(seed) { let s = seed; return () => (s = (s * 16807) % 2147483647) / 2147483647; }

function rr(x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}
function box(x, y, w, h, fill, r) { ctx.fillStyle = fill; if (r) { rr(x, y, w, h, r); ctx.fill(); } else ctx.fillRect(x, y, w, h); }
function circle(x, y, r, fill) { ctx.fillStyle = fill; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill(); }
function ellipse(x, y, rx, ry, fill) { ctx.fillStyle = fill; ctx.beginPath(); ctx.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2); ctx.fill(); }
function poly(pts, fill) { ctx.fillStyle = fill; ctx.beginPath(); pts.forEach((pt, i) => i ? ctx.lineTo(pt[0], pt[1]) : ctx.moveTo(pt[0], pt[1])); ctx.closePath(); ctx.fill(); }
function text(s, x, y, size, weight, fill, align) {
  ctx.font = weight + ' ' + size + 'px ' + FONT;
  ctx.fillStyle = fill; ctx.textAlign = align || 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(s, x, y);
}
function fit(s, max, size, weight) {
  ctx.font = weight + ' ' + size + 'px ' + FONT;
  if (ctx.measureText(s).width <= max) return s;
  while (s.length > 1 && ctx.measureText(s + '…').width > max) s = s.slice(0, -1);
  return s.trimEnd() + '…';
}
function outline(x, y, w, h) {
  ctx.strokeStyle = C.orange; ctx.lineWidth = 3; ctx.setLineDash([8, 6]);
  rr(x, y, w, h, 8); ctx.stroke(); ctx.setLineDash([]);
}

const TONES = [C.red, C.cream, C.slate, C.navy, C.brass, C.teal, '#8C6A5A', C.orange, '#E2D2B0', '#7C8A6A'];
function sleeve(x, y, w, h, s) {
  box(x, y, w, h, s.c);
  ctx.save();
  ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip();
  const cx = x + w / 2, cy = y + h / 2;
  if (s.m === 0) circle(cx, cy, w * 0.3, s.c2);
  else if (s.m === 1) { for (let i = 0; i < 4; i++) box(x, y + h * (0.18 + i * 0.2), w, h * 0.08, s.c2); }
  else if (s.m === 2) poly([[x, y + h], [x + w, y + h * 0.3], [x + w, y + h]], s.c2);
  else if (s.m === 3) { box(x + w * 0.15, y + h * 0.18, w * 0.7, h * 0.08, s.c2); box(x + w * 0.15, y + h * 0.32, w * 0.45, h * 0.06, s.c2); box(x + w * 0.15, y + h * 0.55, w * 0.32, h * 0.3, s.c2); }
  else { circle(cx, cy, w * 0.36, s.c2); circle(cx, cy, w * 0.22, s.c); circle(cx, cy, w * 0.08, s.c2); }
  ctx.restore();
  box(x, y, 2, h, 'rgba(43,39,51,0.18)');
}
function makeSleeve(r) {
  const c = TONES[Math.floor(r() * TONES.length)];
  let c2 = TONES[Math.floor(r() * TONES.length)];
  if (c2 === c) c2 = c === C.cream ? C.navy : C.cream;
  return { c, c2, m: Math.floor(r() * 5) };
}

// Face-out records on the back wall, fixed so the shop looks the same every visit.
const WALL_RECORDS = (() => {
  const r = seeded(11), out = [];
  [44, 122, 200].forEach(top => {
    for (let x = 436; x < WINDOW.x - 34; x += 56) {
      if (r() < 0.1) continue;
      out.push({ x: x + r() * 3, y: top + 4 + r() * 4, w: 50, h: 58, ...makeSleeve(r) });
    }
  });
  return out;
})();
const WINDOW_RECORDS = (() => {
  const r = seeded(5), out = [];
  [282, 334].forEach(top => { for (let x = 204; x < 540; x += 28) if (r() > 0.15) out.push({ x, y: top - 26 + r() * 3, w: 22, h: 26, ...makeSleeve(r) }); });
  return out;
})();

const art = new Map();
function artFor(rec) {
  if (!rec.img) return null;
  let im = art.get(rec.img);
  if (!im) { im = new Image(); im.src = rec.img; art.set(rec.img, im); }
  return im.complete && im.naturalWidth ? im : null;
}

const grain = (() => {
  const c = document.createElement('canvas');
  c.width = c.height = 180;
  const g = c.getContext('2d');
  const d = g.createImageData(180, 180);
  for (let i = 0; i < d.data.length; i += 4) { const v = Math.random() * 255; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; }
  g.putImageData(d, 0, 0);
  return c;
})();
let grainPattern = null;

/* ---------- The girl ---------- */

function drawGirl(x, feet, dir, step, moving, browsing) {
  const p = game.p;
  ctx.save();
  ctx.translate(x, feet);
  ellipse(0, 0, 24, 5, 'rgba(43,39,51,0.24)');
  ctx.scale(dir * 0.86, 0.86);
  const sw = moving ? Math.sin(step) : 0;
  const bob = moving ? -Math.abs(Math.cos(step)) * 2.5 : Math.sin(game.t * 1.6) * 0.6;
  const leg = (hx, ang, skin, shoe) => {
    ctx.save(); ctx.translate(hx, -50); ctx.rotate(ang);
    box(-4, 0, 8, 46, skin, 3);
    box(-5, 42, 15, 8, shoe, 3);
    ctx.restore();
  };
  const arm = (ang, back) => {
    ctx.save(); ctx.translate(back ? -5 : 1, -146 + bob); ctx.rotate(ang);
    box(-5, 0, 10, 30, back ? C.creamShade : C.cream, 5);
    box(-4, 27, 8, 13, back ? C.skinShade : C.skin, 4);
    ctx.restore();
  };
  leg(-3, -sw * 0.4, C.skinShade, '#1E1B26');
  if (!browsing) arm(-sw * 0.45, true);
  leg(3, sw * 0.4, C.skin, C.navy);
  ctx.translate(0, bob);
  // skirt
  ctx.fillStyle = C.navy;
  ctx.beginPath(); ctx.moveTo(-14, -106); ctx.lineTo(13, -106); ctx.lineTo(25, -46); ctx.quadraticCurveTo(0, -41, -26, -46); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = '#1A1822'; ctx.lineWidth = 1.5;
  [-5, 5].forEach(o => { ctx.beginPath(); ctx.moveTo(o * 0.6, -100); ctx.lineTo(o * 1.8, -48); ctx.stroke(); });
  // blouse
  box(-15, -153, 30, 52, C.cream, 9);
  ctx.save(); rr(-15, -153, 30, 52, 9); ctx.clip(); box(-15, -153, 9, 52, C.creamShade); ctx.restore();
  box(-14, -106, 28, 4, '#1A1822', 2);
  poly([[1, -153], [9, -153], [5, -143]], C.paper);
  box(-2, -161, 8, 10, C.skinShade, 2);
  if (browsing) {
    ctx.save(); ctx.translate(3, -147); ctx.rotate(-0.95); box(-5, 0, 10, 26, C.cream, 5); ctx.restore();
    box(16, -136, 16, 8, C.skin, 4);
    box(22, -158, 6, 28, C.slate, 1);
    box(27, -158, 3, 28, C.orange, 1);
  } else arm(sw * 0.45, false);
  // head
  const hy = -177;
  circle(-1, hy, 18, C.hair);
  box(-19, hy, 30, 23, C.hair, 6);
  ellipse(6, hy + 4, 11, 13, C.skin);
  ctx.fillStyle = C.hair;
  ctx.beginPath(); ctx.moveTo(-6, hy - 17); ctx.quadraticCurveTo(14, hy - 21, 18, hy - 4);
  ctx.lineTo(13, hy - 5); ctx.lineTo(10, hy - 10); ctx.lineTo(6, hy - 4); ctx.lineTo(2, hy - 11); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = C.hair; ctx.lineWidth = 1.7;
  ctx.beginPath(); ctx.arc(11.5, hy + 2, 3, 0.25, Math.PI - 0.25); ctx.stroke();
  ellipse(11, hy + 9, 3.5, 2, 'rgba(212,81,46,0.3)');
  ctx.strokeStyle = C.orange; ctx.lineWidth = 4;
  ctx.beginPath(); ctx.arc(-2, hy + 2, 21, -2.55, -0.62); ctx.stroke();
  circle(-2, hy + 3, 9, C.orange);
  circle(-2, hy + 3, 4.5, C.rust);
  ctx.restore();
}

/* ---------- The street ---------- */

function drawStreet() {
  let g = ctx.createLinearGradient(0, 0, 0, 440);
  g.addColorStop(0, '#EDC487'); g.addColorStop(1, '#F6E4BF');
  box(0, 0, W, 440, g);
  g = ctx.createRadialGradient(880, 40, 10, 880, 40, 320);
  g.addColorStop(0, 'rgba(255,244,214,0.95)'); g.addColorStop(1, 'rgba(255,244,214,0)');
  box(0, 0, W, 440, g);
  const far = seeded(3);
  for (let x = -20; x < W; x += 70 + far() * 50) box(x, 170 + far() * 80, 60 + far() * 50, 300, 'rgba(169,184,176,0.55)');
  const near = seeded(9);
  for (let x = -40; x < W; x += 90 + near() * 60) box(x, 230 + near() * 60, 80 + near() * 40, 300, 'rgba(93,127,140,0.38)');
  // pole and wires
  box(86, 30, 9, 412, '#4A3F45');
  box(56, 62, 70, 6, '#4A3F45');
  ctx.strokeStyle = 'rgba(74,63,69,0.75)'; ctx.lineWidth = 1.5;
  [[58, 64, 960, 34], [124, 64, 960, 92], [90, 66, 960, 62]].forEach(([a, b, c, d]) => {
    ctx.beginPath(); ctx.moveTo(a, b); ctx.quadraticCurveTo((a + c) / 2, Math.max(b, d) + 34, c, d); ctx.stroke();
  });
  // building
  g = ctx.createLinearGradient(150, 0, 850, 0);
  g.addColorStop(0, C.wallTop); g.addColorStop(1, '#F0DFBD');
  box(150, 70, 700, 372, g);
  box(140, 58, 720, 16, C.woodDeep);
  box(150, 74, 700, 6, C.woodDark);
  box(228, 94, 544, 68, '#3B2A22', 6);
  ctx.strokeStyle = C.woodLight; ctx.lineWidth = 2; rr(236, 102, 528, 52, 4); ctx.stroke();
  text('Lila\'s new hits', 500, 129, 40, 900, C.paper);
  // awning
  box(166, 176, 668, 10, C.woodDeep);
  const sw = 668 / 19;
  for (let i = 0; i < 19; i++) {
    const x = 166 + i * sw, fill = i % 2 ? C.cream : C.orange;
    box(x, 186, sw + 0.5, 36, fill);
    ctx.fillStyle = fill; ctx.beginPath(); ctx.arc(x + sw / 2, 222, sw / 2, 0, Math.PI); ctx.fill();
  }
  box(166, 186, 668, 6, 'rgba(74,49,34,0.18)');
  box(166, 240, 668, 12, 'rgba(74,49,34,0.14)');
  // shop window
  box(184, 246, 382, 194, C.woodDeep, 3);
  g = ctx.createLinearGradient(0, 256, 0, 430);
  g.addColorStop(0, '#E9BC74'); g.addColorStop(1, '#C48A4E');
  box(194, 256, 362, 176, g);
  [282, 334].forEach(y => box(194, y, 362, 4, 'rgba(74,49,34,0.55)'));
  WINDOW_RECORDS.forEach(s => sleeve(s.x, s.y, s.w, s.h, s));
  g = ctx.createRadialGradient(300, 258, 4, 300, 258, 150);
  g.addColorStop(0, 'rgba(255,228,170,0.55)'); g.addColorStop(1, 'rgba(255,228,170,0)');
  box(194, 256, 362, 176, g);
  [[214, C.red, 0, C.cream], [304, C.cream, 4, C.navy], [404, C.slate, 1, C.brass]].forEach(([x, c, m, c2], i) => {
    circle(x + 62, 392, 28, '#1E1B26'); circle(x + 62, 392, 9, i === 1 ? C.orange : C.cream);
    sleeve(x, 360, 64, 64, { c, c2, m });
  });
  ctx.fillStyle = 'rgba(255,250,236,0.2)';
  [[230, 60], [330, 26], [470, 46]].forEach(([x, w]) => { ctx.beginPath(); ctx.moveTo(x, 256); ctx.lineTo(x + w, 256); ctx.lineTo(x + w - 110, 432); ctx.lineTo(x - 110, 432); ctx.closePath(); ctx.fill(); });
  box(178, 430, 394, 12, C.woodLight);
  // door
  box(592, 244, 120, 198, C.woodDeep, 2);
  box(602, 254, 100, 188, C.slate);
  box(602, 254, 8, 188, C.slateDark);
  g = ctx.createLinearGradient(0, 266, 0, 358);
  g.addColorStop(0, '#EDC27C'); g.addColorStop(1, '#C99050');
  box(614, 266, 76, 92, g, 2);
  box(608, 410, 88, 24, C.slateDark, 2);
  circle(690, 366, 5, C.brass);
  ctx.strokeStyle = C.woodDeep; ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.moveTo(630, 276); ctx.lineTo(652, 266); ctx.lineTo(674, 276); ctx.stroke();
  box(622, 276, 60, 24, C.card, 3);
  text(ready() ? 'Open' : 'Closed', 652, 289, 13, 700, ready() ? C.rust : C.ink);
  if (game.active && game.active.kind === 'door') outline(586, 238, 132, 210);
  box(586, 440, 132, 8, '#B3A386');
  // plant
  [[738, 392, 16, 26], [752, 380, 12, 30], [726, 384, 11, 22], [745, 398, 14, 16]].forEach(([x, y, rx, ry], i) => ellipse(x, y, rx, ry, i % 2 ? '#56684A' : '#6F7F5A'));
  poly([[722, 408], [764, 408], [758, 442], [728, 442]], '#9A5A3A');
  box(720, 404, 46, 7, '#7E4630', 2);
  // pavement and road
  box(0, 442, W, 98, C.pave);
  box(0, 442, W, 5, 'rgba(74,49,34,0.12)');
  for (let x = 40; x < W; x += 96) box(x, 447, 2, 93, 'rgba(74,49,34,0.1)');
  box(0, 490, W, 2, 'rgba(74,49,34,0.08)');
  box(0, 540, W, 8, '#A8987C');
  box(0, 548, W, 28, C.road);
  for (let x = 20; x < W; x += 110) box(x, 560, 54, 4, '#D9CBB0');
}

function drawBoard() {
  const x = 800, y = 452;
  ellipse(x, y + 18, 34, 6, 'rgba(43,39,51,0.2)');
  poly([[x - 30, y + 16], [x - 20, y - 70], [x - 14, y - 70], [x - 22, y + 16]], C.woodDeep);
  poly([[x + 30, y + 16], [x + 20, y - 70], [x + 14, y - 70], [x + 22, y + 16]], C.woodDeep);
  box(x - 30, y - 74, 60, 70, C.woodDark, 3);
  box(x - 25, y - 69, 50, 60, C.chalk, 2);
  const lines = freshStock() ? ['Still in', 'stock'] : ['New stock', 'today'];
  lines.forEach((l, i) => text(l, x, y - 52 + i * 20, 12, 700, '#EDE6D6'));
}

/* ---------- Inside the shop ---------- */

function drawRoom() {
  let g = ctx.createLinearGradient(0, 0, 0, 320);
  g.addColorStop(0, C.wallTop); g.addColorStop(1, C.wall);
  box(0, 0, SHOP_W, 320, g);
  g = ctx.createRadialGradient(WINDOW.x + 85, 170, 20, WINDOW.x + 85, 170, 760);
  g.addColorStop(0, 'rgba(250,230,180,0.75)'); g.addColorStop(1, 'rgba(250,230,180,0)');
  box(0, 0, SHOP_W, 320, g);
  box(0, 0, SHOP_W, 20, C.woodDeep);
  box(0, 20, SHOP_W, 4, C.woodDark);
  // shelves of face-out records
  const shelfW = WINDOW.x - 22 - 428;
  [44, 122, 200].forEach(top => { box(428, top + 66, shelfW, 9, C.woodDark); box(428, top + 66, shelfW, 3, C.woodLight); });
  WALL_RECORDS.forEach(s => sleeve(s.x, s.y, s.w, s.h, s));
  // chalkboard
  box(168, 46, 238, 196, C.woodDark, 4);
  box(177, 55, 220, 178, C.chalk, 2);
  const crates = freshStock() ? allCrates() : [];
  const n = crates.reduce((s, c) => s + c.records.length, 0);
  text('Today\'s delivery', 287, 86, 19, 700, '#EDE6D6');
  ctx.strokeStyle = 'rgba(237,230,214,0.5)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(207, 104); ctx.lineTo(367, 104); ctx.stroke();
  text(busy ? 'Unpacking' : n ? n + ' new records' : 'Nothing yet', 287, 140, 22, 900, C.brass);
  text(n ? 'in ' + crates.length + ' crates' : '', 287, 170, 15, 500, '#EDE6D6');
  text(niceDate(), 287, 206, 15, 500, 'rgba(237,230,214,0.75)');
  // wainscot
  box(0, 318, SHOP_W, 82, C.wood);
  for (let x = 12; x < SHOP_W; x += 26) box(x, 326, 2, 74, 'rgba(74,49,34,0.28)');
  box(0, 314, SHOP_W, 8, C.woodDark);
  // way out
  box(34, 144, 108, 260, C.woodDeep, 2);
  box(42, 152, 92, 252, C.slate);
  g = ctx.createLinearGradient(0, 164, 0, 262);
  g.addColorStop(0, '#F6DCA8'); g.addColorStop(1, '#E3B878');
  box(54, 164, 68, 98, g, 2);
  box(54, 222, 68, 40, 'rgba(93,127,140,0.45)');
  box(48, 300, 80, 10, C.brass, 3);
  box(60, 116, 56, 22, C.card, 3);
  text('Way out', 88, 127, 12, 700, C.ink);
  // window
  box(WINDOW.x - 8, WINDOW.y - 8, WINDOW.w + 16, WINDOW.h + 16, C.woodDark, 3);
  g = ctx.createLinearGradient(0, WINDOW.y, 0, WINDOW.y + WINDOW.h);
  g.addColorStop(0, '#FBEFCB'); g.addColorStop(1, '#F1CC8C');
  box(WINDOW.x, WINDOW.y, WINDOW.w, WINDOW.h, g);
  const tr = seeded(21);
  for (let x = WINDOW.x; x < WINDOW.x + WINDOW.w; x += 30) box(x, WINDOW.y + 170 + tr() * 40, 26, 120, 'rgba(93,127,140,0.3)');
  box(WINDOW.x + WINDOW.w / 2 - 3, WINDOW.y, 6, WINDOW.h, C.woodDark);
  [92, 184].forEach(o => box(WINDOW.x, WINDOW.y + o - 3, WINDOW.w, 6, C.woodDark));
  box(WINDOW.x - 14, WINDOW.y + WINDOW.h + 6, WINDOW.w + 28, 12, C.woodLight);
  const px = WINDOW.x + 62;
  poly([[px, 302], [px + 26, 302], [px + 22, 318], [px + 4, 318]], '#9A5A3A');
  [[px + 6, 292, 8, 12], [px + 20, 288, 7, 14], [px + 13, 284, 6, 12]].forEach(([x, y, rx, ry], i) => ellipse(x, y, rx, ry, i % 2 ? '#56684A' : '#6F7F5A'));
  // baseboard and floor
  box(0, 400, SHOP_W, 12, C.woodDeep);
  for (let r = 0, y = 412; y < H; r++, y += 22) {
    box(0, y, SHOP_W, 22, r % 2 ? C.floorDark : C.floor);
    for (let x = (r * 97) % 160; x < SHOP_W; x += 160) box(x, y, 2, 22, 'rgba(74,49,34,0.22)');
  }
  // sunlight on the floor
  ctx.fillStyle = 'rgba(250,226,170,0.32)';
  [[WINDOW.x + 18, 36], [WINDOW.x + 88, 36]].forEach(([x, w]) => { ctx.beginPath(); ctx.moveTo(x - 210, 412); ctx.lineTo(x - 210 + w + 40, 412); ctx.lineTo(x - 300 + w + 40, H); ctx.lineTo(x - 330, H); ctx.closePath(); ctx.fill(); });
}

function drawLamps() {
  LAMPS.forEach(x => {
    box(x - 1, 20, 2, 30, C.woodDeep);
    poly([[x - 9, 48], [x + 9, 48], [x + 26, 74], [x - 26, 74]], C.rust);
    poly([[x - 9, 48], [x + 9, 48], [x + 3, 52], [x - 3, 52]], C.orange);
    ellipse(x, 74, 26, 4, '#F9D891');
  });
}

function drawLampGlow() {
  ctx.save();
  ctx.globalCompositeOperation = 'screen';
  LAMPS.forEach(x => {
    const g = ctx.createRadialGradient(x, 80, 4, x, 120, 220);
    g.addColorStop(0, 'rgba(255,214,150,0.5)'); g.addColorStop(1, 'rgba(255,214,150,0)');
    poly([[x - 26, 74], [x + 26, 74], [x + 200, 420], [x - 200, 420]], g);
  });
  [WINDOW.x + 10, WINDOW.x + 92].forEach(x => {
    const g = ctx.createLinearGradient(x, 60, x - 340, 560);
    g.addColorStop(0, 'rgba(255,232,180,0.4)'); g.addColorStop(1, 'rgba(255,232,180,0.04)');
    poly([[x, WINDOW.y + 6], [x + 70, WINDOW.y + 6], [x - 230, H], [x - 380, H]], g);
  });
  ctx.restore();
  if (!still) motes.forEach(m => { ctx.globalAlpha = m.a * (0.6 + 0.4 * Math.sin(game.t * 1.3 + m.ph)); circle(m.x, m.y, m.r, '#FFF3D6'); });
  ctx.globalAlpha = 1;
}

function divider(label, cx, active, genre) {
  const s = fit(label, genre ? 172 : 150, genre ? 16 : 14, genre ? 900 : 700);
  ctx.font = (genre ? '900 16px ' : '700 14px ') + FONT;
  const w = ctx.measureText(s).width + (genre ? 34 : 26);
  box(cx - w / 2, 258, w, 40, active ? C.orange : genre ? C.slate : C.card, 5);
  box(cx - w / 2, 290, w, 8, 'rgba(43,39,51,0.08)');
  text(s, cx, 275, genre ? 16 : 14, genre ? 900 : 700, active || genre ? C.paper : C.ink);
}

function drawGenreSign() {
  const x = GENRE_SIGN.x;
  ctx.strokeStyle = C.woodDeep; ctx.lineWidth = 2;
  [-70, 70].forEach(o => { ctx.beginPath(); ctx.moveTo(x + o, 20); ctx.lineTo(x + o, 92); ctx.stroke(); });
  box(x - 96, 90, 192, 44, C.woodDeep, 5);
  ctx.strokeStyle = C.woodLight; ctx.lineWidth = 1.5; rr(x - 89, 96, 178, 32, 3); ctx.stroke();
  text('Explore a genre', x, 113, 17, 900, C.paper);
}

function drawBin(b, crate, active, genre) {
  const { x, w } = b, cx = x + w / 2;
  ellipse(cx, 486, w / 2 + 6, 7, 'rgba(43,39,51,0.2)');
  box(x + 12, 430, 10, 56, C.woodDeep);
  box(x + w - 22, 430, 10, 56, C.woodDeep);
  box(x + 8, 470, w - 16, 6, C.woodDark);
  if (crate) divider(crate.seed, cx, active, genre);
  box(x + 4, 344, w - 8, 10, C.woodDeep);
  if (crate) {
    const n = crate.records.length;
    crate.records.forEach((rec, i) => {
      const rx = x + 10 + i * ((w - 86) / Math.max(1, n - 1)), ry = 300 + (i % 2) * 9;
      const im = artFor(rec);
      ctx.save();
      ctx.translate(rx + 33, ry + 40);
      ctx.rotate(((i * 7) % 5 - 2) * 0.025);
      box(-35, -40, 3, 80, 'rgba(43,39,51,0.35)');
      if (im) ctx.drawImage(im, -33, -40, 66, 80);
      else box(-33, -40, 66, 80, sleeveColour(rec));
      ctx.restore();
    });
  }
  box(x, 352, w, 82, C.wood, 2);
  box(x, 352, w, 6, C.woodLight);
  box(x, 380, w, 2, 'rgba(74,49,34,0.3)');
  box(x, 406, w, 2, 'rgba(74,49,34,0.3)');
  box(x, 352, 6, 82, 'rgba(74,49,34,0.25)');
  box(cx - 24, 386, 48, 15, C.brass, 2);
  if (active) outline(x - 6, 252, w + 12, 238);
}

function drawCounter(active) {
  const { x, w } = COUNTER;
  ellipse(x + w / 2, 488, w / 2 + 8, 7, 'rgba(43,39,51,0.2)');
  box(x + 18, 324, 72, 44, C.slate, 4);
  box(x + 26, 312, 46, 16, C.teal, 2);
  for (let i = 0; i < 3; i++) for (let j = 0; j < 4; j++) box(x + 28 + j * 14, 336 + i * 9, 10, 5, C.cream, 1);
  box(x + 98, 330, 32, 38, C.card, 2);
  ctx.strokeStyle = C.woodDark; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(x + 114, 330, 9, Math.PI, 0); ctx.stroke();
  box(x + 142, 352, 82, 16, C.woodDeep, 3);
  ellipse(x + 182, 352, 32, 7, '#1E1B26');
  ellipse(x + 182, 352, 9, 2.5, C.orange);
  box(x - 4, 366, w + 8, 14, C.woodLight, 3);
  box(x, 380, w, 106, C.woodDark, 2);
  [x + 14, x + 90, x + 166].forEach(px => { box(px, 394, 62, 78, C.wood, 3); box(px, 394, 62, 4, 'rgba(255,240,210,0.2)'); });
  box(x + w / 2 - 66, 418, 132, 30, C.card, 4);
  text('Bag and checkout', x + w / 2, 433, 13, 700, active ? C.rust : C.ink);
  if (active) outline(x - 10, 300, w + 20, 194);
}

function drawBoxes(active) {
  const { x, w } = BOXES;
  ellipse(x + w / 2, 488, w / 2 + 6, 7, 'rgba(43,39,51,0.2)');
  box(x, 402, 78, 84, C.box, 2); box(x + 34, 402, 10, 84, C.paper);
  box(x + 66, 424, 72, 62, C.boxDark, 2); box(x + 96, 424, 10, 62, C.paper);
  box(x + 16, 350, 72, 52, C.boxDark, 2); box(x + 46, 350, 10, 52, C.paper);
  box(x + 26, 446, 60, 24, C.card, 3);
  text(busy ? 'Unpacking' : 'Deliveries', x + 56, 458, 12, 700, active ? C.rust : C.ink);
  if (active) outline(x - 8, 342, w + 16, 152);
}

function drawPrompt() {
  const a = game.active;
  if (!a || game.fading) return;
  const label = fit(a.label(), 560, 17, 700);
  ctx.font = '700 17px ' + FONT;
  const w = ctx.measureText(label).width + 78, x = W / 2 - w / 2, y = 30;
  box(x, y, w, 42, 'rgba(43,39,51,0.9)', 21);
  box(x + 8, y + 8, 30, 26, C.orange, 7);
  text('E', x + 23, y + 22, 16, 900, C.paper);
  text(label, x + 50, y + 22, 17, 700, C.paper, 'left');
}

function draw() {
  ctx.setTransform(canvas.width / W, 0, 0, canvas.height / H, 0, 0);
  const p = game.p;
  const browsing = !p.moving && !!game.active && (game.active.kind === 'crate' || game.active.kind === 'genre');
  if (game.scene === 'street') {
    drawStreet();
    drawBoard();
    drawGirl(p.x, FEET.street, p.dir, p.step, p.moving, false);
  } else {
    ctx.save();
    ctx.translate(-Math.round(game.cam), 0);
    drawRoom();
    drawLamps();
    drawGenreSign();
    const a = game.active;
    drawCounter(!!a && a.kind === 'counter');
    BINS.forEach((b, i) => drawBin(b, stock && stock.crates && stock.crates[i], !!a && a.kind === 'crate' && a.i === i));
    GENRE_BINS.forEach((b, i) => drawBin(b, stock && stock.genres && stock.genres[i], !!a && a.kind === 'genre' && a.i === i, true));
    drawBoxes(!!a && a.kind === 'boxes');
    if (a && a.kind === 'exit') outline(28, 110, 120, 300);
    drawGirl(p.x, FEET.shop, p.dir, p.step, p.moving, browsing);
    drawLampGlow();
    ctx.restore();
  }
  // film grain and a soft vignette, like the light in an old photo
  if (!grainPattern) grainPattern = ctx.createPattern(grain, 'repeat');
  ctx.save();
  ctx.globalAlpha = 0.07; ctx.globalCompositeOperation = 'overlay';
  ctx.fillStyle = grainPattern; ctx.fillRect(0, 0, W, H);
  ctx.restore();
  const v = ctx.createRadialGradient(W / 2, H / 2, H * 0.42, W / 2, H / 2, W * 0.72);
  v.addColorStop(0, 'rgba(43,39,51,0)'); v.addColorStop(1, 'rgba(43,39,51,0.32)');
  box(0, 0, W, H, v);
  drawPrompt();
  if (game.fade > 0) { ctx.globalAlpha = Math.min(1, game.fade); box(0, 0, W, H, C.ink); ctx.globalAlpha = 1; }
}

function resize() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const w = Math.round(canvas.clientWidth * dpr) || W;
  if (canvas.width !== w) { canvas.width = w; canvas.height = Math.round(w * H / W); }
}

let lastTime = 0;
function frame(t) {
  const dt = Math.min(0.05, (t - lastTime) / 1000 || 0);
  lastTime = t;
  resize();
  if (!document.querySelector('dialog[open]')) update(dt);
  draw();
  requestAnimationFrame(frame);
}

/* ---------- Controls ---------- */

const MOVE = { ArrowLeft: 'left', a: 'left', A: 'left', ArrowRight: 'right', d: 'right', D: 'right' };
const ACT = new Set(['e', 'E', 'ArrowUp', 'w', 'W']);
window.addEventListener('keydown', e => {
  if (document.querySelector('dialog[open]') || e.metaKey || e.ctrlKey || e.altKey) return;
  const tag = e.target.tagName;
  if (tag === 'INPUT' || tag === 'TEXTAREA') return;
  if (MOVE[e.key]) { game.keys.add(MOVE[e.key]); e.preventDefault(); return; }
  const onButton = tag === 'BUTTON' || tag === 'A';
  if (ACT.has(e.key) || ((e.key === 'Enter' || e.key === ' ') && !onButton)) {
    if (e.key === 'ArrowUp' || e.key === ' ') e.preventDefault();
    if (game.active && !game.fading) { const go = game.active.go; stopWalking(); go(); }
  }
});
window.addEventListener('keyup', e => { if (MOVE[e.key]) game.keys.delete(MOVE[e.key]); });
window.addEventListener('blur', () => game.keys.clear());

canvas.addEventListener('click', e => {
  if (game.fading) return;
  const r = canvas.getBoundingClientRect();
  const x = (e.clientX - r.left) * W / r.width, y = (e.clientY - r.top) * H / r.height;
  const wx = x + game.cam;
  const b = bounds();
  const hit = interactables().find(o => wx > o.x - 8 && wx < o.x + o.w + 8 && y > 100 && y < 500);
  const clamp = v => Math.min(b.x2, Math.max(b.x1, v));
  game.target = clamp(hit ? hit.x + hit.w / 2 : wx);
  game.pending = hit ? hit.go : null;
});

/* ---------- Setup and start ---------- */

async function saveKey() {
  const key = $('lfkey').value.trim();
  if (!/^[0-9a-f]{32}$/i.test(key)) {
    setStatus('status', 'A Last.fm API key is 32 letters and numbers. Check that you copied the API key and not the shared secret.', 'error');
    return;
  }
  store.set('lastfm_key', key);
  setStatus('status', 'Checking the key', 'pulse');
  try {
    await lastfm({ method: 'artist.getsimilar', artist: 'Radiohead', limit: 1 });
    setStatus('status', 'The shop is open. Walk to the door and go in.');
    syncChrome();
  } catch (e) {
    store.del('lastfm_key');
    setStatus('status', e.code ? 'Last.fm did not accept that key. Copy it again and paste it here.' : e.message, 'error');
  }
}

async function showWho() {
  try {
    const me = await spotify('/me');
    meId = me.id;
    $('who').textContent = 'Connected as ' + (me.display_name || me.id);
  } catch {}
}

async function start() {
  const q = new URLSearchParams(location.search);
  if (q.has('code') || q.has('error')) {
    history.replaceState(null, '', '/');
    if (q.has('error')) {
      setStatus('status', 'Spotify was not connected (' + q.get('error') + '). Select Connect Spotify to try again.', 'error');
    } else if (q.get('state') !== store.get('pkce_state') || !store.get('pkce_verifier')) {
      setStatus('status', 'That sign-in could not be verified. Select Connect Spotify to try again.', 'error');
    } else {
      setStatus('status', 'Connecting Spotify', 'pulse');
      try {
        await tokenRequest({ grant_type: 'authorization_code', code: q.get('code'), redirect_uri: REDIRECT_URI, code_verifier: store.get('pkce_verifier') });
        setStatus('status', '');
      } catch (e) {
        setStatus('status', e.message, 'error');
      }
      store.del('pkce_verifier');
      store.del('pkce_state');
    }
  }
  syncChrome();
  requestAnimationFrame(frame);
}

$('login').addEventListener('click', login);
$('savekey').addEventListener('click', saveKey);
$('lfkey').addEventListener('keydown', e => { if (e.key === 'Enter') saveKey(); });
$('redeliver').addEventListener('click', deliver);
$('logout').addEventListener('click', () => { signOut(); setStatus('status', ''); goOutside(); });
$('changekey').addEventListener('click', () => { store.del('lastfm_key'); setStatus('status', ''); goOutside(); });
$('forget').addEventListener('click', () => { store.del('seen_artists'); setStatus('status', 'Artists you have seen here before can turn up again in the next delivery.'); });
$('bagbtn').addEventListener('click', openBag);
$('bag-close').addEventListener('click', () => $('bag').close());
$('checkout').addEventListener('click', checkout);
document.querySelectorAll('input[name=dest]').forEach(r => r.addEventListener('change', () => { syncDest(); if (destMode() === 'existing' && !playlists) loadPlaylists(); }));
$('reconnectbtn').addEventListener('click', login);
$('cr-close').addEventListener('click', () => $('cratedlg').close());
$('st-bag').addEventListener('click', () => { if (current) { toggleBag(current); updateStationButton(); } });
$('st-back').addEventListener('click', () => $('station').close());
$('station').addEventListener('close', () => { $('st-player').src = 'about:blank'; });
['station', 'bag', 'cratedlg'].forEach(id => { const d = $(id); d.addEventListener('click', e => { if (e.target === d) d.close(); }); d.addEventListener('close', () => { game.keys.clear(); if (!document.querySelector('dialog[open]')) canvas.focus({ preventScroll: true }); }); });
start();
</script>
</body>
</html>
"""


def fetch_lastfm(query):
    url = "https://ws.audioscrobbler.com/2.0/?" + query
    req = urllib.request.Request(url, headers={"User-Agent": "lilas-new-hits/1.0"})
    try:
        return urllib.request.urlopen(req, timeout=20)
    except urllib.error.URLError as err:
        if not isinstance(getattr(err, "reason", None), ssl.SSLError):
            raise
        import certifi  # some Python installs on macOS ship without certificates
        ctx = ssl.create_default_context(cafile=certifi.where())
        return urllib.request.urlopen(req, timeout=20, context=ctx)


class Handler(http.server.BaseHTTPRequestHandler):
    def reply(self, status, ctype, body):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path, _, query = self.path.partition("?")
        if path in ("/", "/callback", "/index.html"):
            self.reply(200, "text/html; charset=utf-8", PAGE.encode("utf-8"))
        elif path == "/lastfm":
            try:
                with fetch_lastfm(query) as res:
                    self.reply(200, "application/json", res.read())
            except urllib.error.HTTPError as err:
                self.reply(200, "application/json", err.read() or b'{"error":-1,"message":"Last.fm error"}')
            except Exception as err:
                msg = json.dumps({"error": -1, "message": "Could not reach Last.fm: %s" % err})
                self.reply(200, "application/json", msg.encode("utf-8"))
        else:
            self.reply(404, "text/plain; charset=utf-8", b"Not found")

    def log_message(self, *args):
        pass


def install():
    """Write a double-clickable copy of this file to the Desktop.
    A file created on this Mac is not marked as downloaded, so macOS does not block it."""
    import os, pathlib, subprocess
    me = pathlib.Path(__file__).resolve()
    source = me.read_bytes()
    name = "Lila's new hits.command"
    for folder in (pathlib.Path.home() / "Desktop", pathlib.Path.home()):
        dest = folder / name
        try:
            if dest.exists() and dest.resolve() == me:
                break
            dest.write_bytes(source)
            os.chmod(dest, 0o755)
            break
        except OSError:
            continue
    else:
        sys.exit("Could not save the shop to your Desktop or home folder.")
    try:
        subprocess.run(["xattr", "-d", "com.apple.quarantine", str(dest)], capture_output=True)
    except OSError:
        pass
    print("Done. Double-click \"Lila's new hits\" %s to open the shop." % ("on your Desktop" if dest.parent.name == "Desktop" else "in your home folder"))
    print("You can delete the file you downloaded, and close this window.")


def main():
    if "--install" in sys.argv:
        install()
        return
    url = "http://127.0.0.1:%d" % PORT
    try:
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        # Already open in another window: just bring the shop up again.
        try:
            with urllib.request.urlopen(url + "/", timeout=3) as res:
                if b"new hits" in res.read(4000):
                    print("Lila's new hits is already running. Opening it in your browser.")
                    webbrowser.open(url)
                    return
        except Exception:
            pass
        sys.exit("Something else on this computer is using port %d. Restart the computer and try again." % PORT)
    print("Lila's new hits is open at " + url)
    print("Keep this window open while you use the shop. Close it (or press Control+C) when you are done.")
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
