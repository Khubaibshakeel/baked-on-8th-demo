/* Baked on 8th — demo site behaviour. Everything is progressive: pages read fine without this file. */
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const root = document.documentElement;
  // ?still = screenshot mode for the pitch pack: final states, no motion, no demo-notes button
  const still = new URLSearchParams(location.search).has('still');
  // pitch screenshots only, with ?still: &now=2026-11-04T14:20 fixes the Nashville clock, &check=f6,r5,s2 ticks
  // planner inputs, &cards=illus keeps the cake cards on their drawings
  const shot = still ? new URLSearchParams(location.search) : new URLSearchParams();
  if (still) {
    root.classList.add('still');
    const target = new URLSearchParams(location.search).get('still');
    // headless capture can't paint scrolled positions reliably, so drop the sections above the target instead
    const el = target && document.getElementById(target);
    const sec = el && el.closest('main > section, main > div');
    if (sec) while (sec.previousElementSibling) sec.previousElementSibling.remove();
  }
  const reduce = still || matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---------- Shop hours: content/hours.json, written into each page by the build (#shop-hours) ----------
  const TZ = 'America/Chicago';
  const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const FALLBACK = { rows: [{ days: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'], opens: '08:00', closes: '19:00', online_cutoff: '18:00' }, { days: ['Sun'], opens: '10:00', closes: '16:00', online_cutoff: '15:00' }], closures: [] };
  let SHOP = FALLBACK;
  try { SHOP = JSON.parse($('#shop-hours')?.textContent || 'null') || FALLBACK; } catch { /* keep the fallback */ }
  const secs = (t) => { const [h, m] = t.split(':').map(Number); return h * 3600 + m * 60; };
  const fmtT = (s) => { const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60); return `${h % 12 || 12}${m ? ':' + String(m).padStart(2, '0') : ''}${h < 12 ? 'am' : 'pm'}`; };
  const nashNow = () => {
    const fixed = shot.get('now');
    if (fixed) {
      const [d, t = '12:00'] = fixed.split('T'), [h, m] = t.split(':').map(Number);
      return { day: DAYS[new Date(`${d}T12:00:00Z`).getUTCDay()], sec: h * 3600 + m * 60, ymd: d };
    }
    const p = Object.fromEntries(new Intl.DateTimeFormat('en-US', { timeZone: TZ, weekday: 'short', year: 'numeric', month: '2-digit', day: '2-digit', hour: 'numeric', minute: 'numeric', second: 'numeric', hourCycle: 'h23' }).formatToParts(new Date()).map((x) => [x.type, x.value]));
    return { day: p.weekday, sec: +p.hour * 3600 + +p.minute * 60 + +p.second, ymd: `${p.year}-${p.month}-${p.day}` };
  };
  // a Nashville calendar date k days from ymd, as { ymd, day, label }
  const addDays = (ymd, k) => {
    const d = new Date(`${ymd}T12:00:00Z`); d.setUTCDate(d.getUTCDate() + k);
    return { ymd: d.toISOString().slice(0, 10), day: DAYS[d.getUTCDay()], label: d.toLocaleDateString('en-US', { timeZone: 'UTC', weekday: 'short', month: 'short', day: 'numeric' }) };
  };
  const closureOn = (ymd) => SHOP.closures.find((c) => c.date === ymd);
  // that day's hours in seconds, or null when the shop is shut (no hours that weekday, or a listed closure)
  const hoursOn = (day, ymd) => {
    const r = SHOP.rows.find((x) => x.days.includes(day));
    return r && !closureOn(ymd) ? { open: secs(r.opens), close: secs(r.closes), cut: secs(r.online_cutoff) } : null;
  };
  const nextOpening = (n) => {
    const today = hoursOn(n.day, n.ymd);
    if (today && n.sec < today.open) return fmtT(today.open);
    for (let k = 1; k < 30; k++) {
      const d = addDays(n.ymd, k), h = hoursOn(d.day, d.ymd);
      if (h) return `${fmtT(h.open)} ${k === 1 ? 'tomorrow' : k < 7 ? { Sun: 'Sunday', Mon: 'Monday', Tue: 'Tuesday', Wed: 'Wednesday', Thu: 'Thursday', Fri: 'Friday', Sat: 'Saturday' }[d.day] : d.label}`;
    }
    return 'soon';
  };
  // same-day ordering is open only before today's online cutoff, on a day the shop is open (holiday closures included).
  // Past that, never promise a pickup day: the ordering site shows the next available time.
  const sameDayOpen = () => { const n = nashNow(), h = hoursOn(n.day, n.ymd); return !!h && n.sec < h.cut; };
  const sameDayLine = () => (sameDayOpen() ? 'Order it online for pickup today.' : 'Order online to see the next available pickup time.');
  window.BO8 = { shop: SHOP };

  // ---------- Sprinkle texture shared by strips ----------
  {
    const cols = ['#9FCDEB', '#F6CF6E', '#F3B0BE', '#A8D8B6', '#D65158', '#FFFFFF'];
    let seed = 11; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    let s = '';
    for (let i = 0; i < 30; i++) {
      const x = 6 + rnd() * 208, y = 7 + rnd() * 20;
      s += `<rect x='${(x - 5).toFixed(1)}' y='${(y - 1.7).toFixed(1)}' width='10' height='3.4' rx='1.7' fill='${cols[i % 6]}' transform='rotate(${(rnd() * 180) | 0} ${x.toFixed(1)} ${y.toFixed(1)})'/>`;
    }
    root.style.setProperty('--sprinkles', `url("data:image/svg+xml,${encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' width='220' height='34'>${s}</svg>`)}")`);
  }

  // ---------- Header + mobile nav ----------
  const header = $('.site-header');
  const onScroll = () => header && header.classList.toggle('is-scrolled', scrollY > 8);
  addEventListener('scroll', onScroll, { passive: true }); onScroll();

  const mnav = $('#mobile-nav'), openBtn = $('.menu-btn');
  if (mnav && openBtn) {
    const closeBtn = $('.close', mnav);
    // a modal: while open, everything else on the page is inert and Tab cycles inside the menu
    const behind = [...document.body.children].filter((el) => el !== mnav && el.tagName !== 'SCRIPT');
    const setOpen = (open) => {
      mnav.classList.toggle('is-open', open);
      mnav.setAttribute('aria-hidden', String(!open));
      openBtn.setAttribute('aria-expanded', String(open));
      document.body.style.overflow = open ? 'hidden' : '';
      document.body.classList.toggle('nav-open', open);
      behind.forEach((el) => { el.inert = open; });
      (open ? closeBtn : openBtn).focus();
    };
    openBtn.addEventListener('click', () => setOpen(true));
    closeBtn.addEventListener('click', () => setOpen(false));
    $$('a', mnav).forEach((a) => a.addEventListener('click', () => setOpen(false)));
    addEventListener('keydown', (e) => {
      if (!mnav.classList.contains('is-open')) return;
      if (e.key === 'Escape') setOpen(false);
      if (e.key === 'Tab') {
        const f = $$('a, button', mnav), i = f.indexOf(document.activeElement);
        e.preventDefault();
        f[(i + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus();
      }
    });
    addEventListener('resize', () => { if (innerWidth > 1100 && mnav.classList.contains('is-open')) setOpen(false); });
  }

  // ---------- Entrance + scroll reveals ----------
  const ready = () => root.classList.add('is-ready');
  requestAnimationFrame(() => requestAnimationFrame(ready));
  setTimeout(ready, 150); // rAF pauses in background tabs; never leave the hero hidden

  const revealEls = $$('.reveal, .reveal-img, .pop, .mascot-pop');
  if (reduce || !('IntersectionObserver' in window)) {
    revealEls.forEach((el) => el.classList.add('is-in'));
  } else {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); } });
    }, { threshold: 0.14, rootMargin: '0px 0px -6% 0px' });
    revealEls.forEach((el) => io.observe(el));
    // Safety net: anything still hidden after load and in view gets revealed
    addEventListener('load', () => setTimeout(() => revealEls.forEach((el) => {
      const r = el.getBoundingClientRect(); if (r.top < innerHeight && r.bottom > 0) el.classList.add('is-in');
    }), 1200));
  }

  // ---------- Parallax (desktop pointer only) ----------
  const px = $$('[data-parallax]');
  if (px.length && !reduce && matchMedia('(hover: hover) and (min-width: 901px)').matches) {
    let ticking = false;
    const run = () => {
      ticking = false;
      px.forEach((el) => {
        const r = el.getBoundingClientRect();
        const mid = r.top + r.height / 2 - innerHeight / 2;
        el.style.transform = `translate3d(0, ${(-mid * +el.dataset.parallax).toFixed(1)}px, 0)`;
      });
    };
    addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(run); } }, { passive: true });
    run();
  }

  // ---------- Open/closed status, hours highlight and the cake clock ----------
  const statusEl = $('[data-status]');
  const clock = $('[data-clock]');
  const cakeSvg = clock && $('svg', clock);
  if (cakeSvg) {
    // top-down sprinkle cake drawn once
    const cols = ['#9FCDEB', '#F6CF6E', '#F3B0BE', '#A8D8B6', '#D65158'];
    let seed = 42; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    let o = `<circle cx='200' cy='200' r='196' fill='#F3B0BE' stroke='#4A2C2A' stroke-width='5'/><circle cx='200' cy='200' r='168' fill='#F8C9D3'/>`;
    for (let i = 0; i < 26; i++) {
      const a = (i / 26) * Math.PI * 2, x = 200 + Math.cos(a) * 178, y = 200 + Math.sin(a) * 178;
      o += `<circle cx='${x.toFixed(1)}' cy='${y.toFixed(1)}' r='18' fill='#FFF6E4' stroke='#4A2C2A' stroke-width='3'/><path d='M${(x - 8).toFixed(1)},${y.toFixed(1)} a8,8 0 1 1 8,8' fill='none' stroke='#E5D2B0' stroke-width='3'/>`;
    }
    for (let i = 0; i < 110; i++) {
      const r = 22 + Math.sqrt(rnd()) * 136, a = rnd() * Math.PI * 2, x = 200 + Math.cos(a) * r, y = 200 + Math.sin(a) * r;
      o += `<rect x='${(x - 6).toFixed(1)}' y='${(y - 2).toFixed(1)}' width='12' height='4' rx='2' fill='${cols[i % 5]}' transform='rotate(${(rnd() * 180) | 0} ${x.toFixed(1)} ${y.toFixed(1)})'/>`;
    }
    for (let i = 0; i < 12; i++) { // slice lines are decoration; the eaten wedge is the share of today's order window already gone
      const a = (i / 12) * Math.PI * 2 - Math.PI / 2;
      o += `<line x1='200' y1='200' x2='${(200 + Math.cos(a) * 160).toFixed(1)}' y2='${(200 + Math.sin(a) * 160).toFixed(1)}' stroke='#E59AAE' stroke-width='2' opacity='.7'/>`;
    }
    cakeSvg.innerHTML = o;
  }
  const ctas = $$('[data-cta="sameday"]');
  const noHours = !SHOP.rows || !SHOP.rows.length;
  // no hours saved: say nothing about open/closed rather than "Closed" forever
  if (noHours) { if (statusEl) statusEl.hidden = true; if (clock) $$('.clock, .clock-note, .clock-mascot').forEach((el) => { el.hidden = true; }); }
  const tickClock = () => {
    if (noHours) return;
    const n = nashNow(), h = hoursOn(n.day, n.ymd), closure = closureOn(n.ymd);
    const isOpen = !!h && n.sec >= h.open && n.sec < h.close;
    const canOrderToday = !!h && n.sec < h.cut;
    // after the cutoff (or on a closed day) nothing may promise "today"
    ctas.forEach((a) => { const l = $('[data-cta-label]', a); if (l && !a.dataset.ctaHeld) l.textContent = canOrderToday ? 'Order for today' : 'Order online'; });
    if (statusEl) {
      statusEl.classList.toggle('closed', !isOpen);
      $('span', statusEl).textContent = closure ? `Closed today for ${closure.message} · opens ${nextOpening(n)}`
        : isOpen ? `Open now · until ${fmtT(h.close)} today` : `Closed now · opens ${nextOpening(n)}`;
    }
    if (clock) {
      const cake = $('.cake', clock), k = $('.k', clock), t = $('.t', clock), s = $('.s', clock);
      if (canOrderToday) {
        const left = h.cut - n.sec, hh = Math.floor(left / 3600), m = Math.floor((left % 3600) / 60), sc = left % 60;
        k.textContent = 'Order within';
        t.classList.remove('word');
        t.textContent = hh ? `${hh}h ${String(m).padStart(2, '0')}m` : `${m}m ${String(sc).padStart(2, '0')}s`;
        s.textContent = `for pickup by ${fmtT(h.close)}`;
        const eaten = n.sec <= h.open ? 0 : ((n.sec - h.open) / (h.cut - h.open)) * 360;
        cake.style.setProperty('--eaten', `${eaten.toFixed(2)}deg`);
        clock.setAttribute('aria-label', `Same-day ordering: ${t.textContent} left to order online for pickup today.`);
      } else {
        // no promise about next-day pickup: Square's own wording on that isn't confirmed
        k.textContent = closure ? 'Closed today' : 'Today’s cutoff';
        t.classList.add('word');
        t.textContent = closure ? closure.message : 'Passed';
        s.textContent = isOpen ? `Store open until ${fmtT(h.close)}` : `Opens ${nextOpening(n)}`;
        cake.style.setProperty('--eaten', '0deg');
        clock.classList.add('is-after');
        const say = $('[data-mascot-say]');
        if (say) say.textContent = isOpen ? `Walk-ins till ${fmtT(h.close)}!` : /tomorrow/.test(nextOpening(n)) ? 'See you tomorrow!' : 'See you soon!';
        clock.setAttribute('aria-label', closure ? `Closed today for ${closure.message}. ${s.textContent}.` : `Today’s online order cutoff has passed. ${s.textContent}.`);
      }
      if (canOrderToday) clock.classList.remove('is-after');
    }
    $$('[data-hours] li[data-day]').forEach((li) => li.classList.toggle('today', !closure && li.dataset.day.split(',').includes(n.day)));
    $$('[data-sameday-when]').forEach((el) => { el.textContent = canOrderToday ? 'Order it online for pickup today.' : 'Order online to see the next available pickup time.'; });
    const callBtn = $('.action-bar a.call');
    if (callBtn) {
      let sub = $('small', callBtn);
      if (!isOpen && !sub) { sub = document.createElement('small'); callBtn.append(sub); }
      if (sub) { sub.textContent = isOpen ? '' : `opens ${nextOpening(n).split(' ')[0]}`; sub.hidden = isOpen; }
      callBtn.setAttribute('aria-label', isOpen ? 'Call the shop' : `Call the shop (opens ${nextOpening(n)})`);
    }
    // closures coming up in the next six weeks join the hours list
    $$('[data-hours] li[data-closure]').forEach((li) => {
      const d = li.dataset.closure, soon = d >= n.ymd && d <= addDays(n.ymd, 42).ymd;
      li.hidden = !soon;
      if (soon) { $('span', li).textContent = d === n.ymd ? 'Today' : addDays(d, 0).label; li.classList.toggle('today', d === n.ymd); }
    });
  };
  if (statusEl || clock || ctas.length || $('[data-hours]')) { tickClock(); setInterval(tickClock, 1000); }

  // ---------- Cake cards: real photos with a small drawing sticker; a photo that fails hands the card to the drawing ----------
  $$('.cake-card').forEach((card) => {
    const ph = $('.v-photo', card), st = $('.cake-sticker', card);
    if (!ph) return;
    if (still) { ph.loading = 'eager'; ph.decoding = 'sync'; } // screenshots: paint the photo in the same frame it loads
    const shown = () => card.classList.add('has-photo');
    const failed = () => {
      ph.remove(); card.classList.add('no-photo');
      if (st) { st.alt = `${$('h3', card).textContent} cake (drawing)`; st.removeAttribute('aria-hidden'); }
    };
    if (ph.complete) (ph.naturalWidth ? shown() : failed());
    else { ph.addEventListener('load', shown, { once: true }); ph.addEventListener('error', failed, { once: true }); }
  });

  // ---------- Horizontal rails: arrow buttons for mouse and keyboard; swipe still works on touch ----------
  $$('.cake-rail, .rail').forEach((rail, i) => {
    rail.setAttribute('tabindex', '0');
    rail.setAttribute('role', 'region');
    if (!rail.hasAttribute('aria-label')) rail.setAttribute('aria-label', 'Scrollable list');
    const ctrl = document.createElement('div');
    ctrl.className = 'rail-ctrl';
    ctrl.innerHTML = `<button type="button" aria-label="Scroll back">${icon('left')}</button><button type="button" aria-label="Scroll forward">${icon('right')}</button>`;
    rail.before(ctrl);
    const [prev, next] = $$('button', ctrl);
    const step = () => (rail.firstElementChild ? rail.firstElementChild.getBoundingClientRect().width + 22 : rail.clientWidth * 0.8);
    // smooth where supported; if the browser doesn't animate it (some embedded/background views), jump instead
    const go = (dir) => {
      const from = rail.scrollLeft, d = dir * step();
      rail.scrollBy({ left: d, behavior: reduce ? 'auto' : 'smooth' });
      setTimeout(() => { if (Math.abs(rail.scrollLeft - from) < 2) rail.scrollBy({ left: d, behavior: 'auto' }); sync(); }, 450);
      setTimeout(sync, 900);
    };
    prev.addEventListener('click', () => go(-1));
    next.addEventListener('click', () => go(1));
    const sync = () => {
      const max = rail.scrollWidth - rail.clientWidth;
      ctrl.classList.toggle('is-active', max > 4);
      prev.disabled = rail.scrollLeft <= 2;
      next.disabled = rail.scrollLeft >= max - 2;
    };
    rail.addEventListener('scroll', sync, { passive: true });
    addEventListener('resize', sync);
    addEventListener('load', sync);
    sync();
  });

  // ---------- Lightbox ----------
  const groups = {};
  $$('[data-lightbox]').forEach((el) => (groups[el.dataset.lightbox] ||= []).push(el));
  if (Object.keys(groups).length) {
    const lb = document.createElement('div');
    lb.className = 'lightbox'; lb.setAttribute('role', 'dialog'); lb.setAttribute('aria-modal', 'true'); lb.setAttribute('aria-label', 'Photo viewer');
    lb.innerHTML = `<img alt=""><button class="lb-close" aria-label="Close">${icon('x')}</button><button class="lb-prev" aria-label="Previous photo">${icon('left')}</button><button class="lb-next" aria-label="Next photo">${icon('right')}</button><span class="lb-count"></span>`;
    document.body.append(lb);
    const img = $('img', lb); let list = [], idx = 0, opener = null;
    const show = (i) => {
      idx = (i + list.length) % list.length; const el = list[idx];
      img.style.opacity = 0;
      const n = new Image(); n.src = el.dataset.full; n.decode().catch(() => {}).finally(() => { img.src = el.dataset.full; img.alt = $('img', el).alt; img.style.opacity = 1; });
      $('.lb-count', lb).textContent = `${idx + 1} / ${list.length}`;
    };
    const close = () => { lb.classList.remove('is-open'); document.body.style.overflow = ''; opener && opener.focus(); };
    Object.values(groups).forEach((g) => g.forEach((el, i) => el.addEventListener('click', () => {
      list = g; opener = el; show(i); lb.classList.add('is-open'); document.body.style.overflow = 'hidden'; $('.lb-close', lb).focus();
    })));
    $('.lb-close', lb).addEventListener('click', close);
    $('.lb-prev', lb).addEventListener('click', () => show(idx - 1));
    $('.lb-next', lb).addEventListener('click', () => show(idx + 1));
    lb.addEventListener('click', (e) => { if (e.target === lb) close(); });
    // swipe left/right on touch screens
    let sx = null, sy = 0;
    img.addEventListener('pointerdown', (e) => { sx = e.clientX; sy = e.clientY; });
    img.addEventListener('pointerup', (e) => {
      if (sx === null) return;
      const dx = e.clientX - sx, dy = e.clientY - sy; sx = null;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) show(idx + (dx < 0 ? 1 : -1));
    });
    addEventListener('keydown', (e) => {
      if (!lb.classList.contains('is-open')) return;
      if (e.key === 'Escape') close(); if (e.key === 'ArrowRight') show(idx + 1); if (e.key === 'ArrowLeft') show(idx - 1);
      if (e.key === 'Tab') { const f = $$('button', lb); const i = f.indexOf(document.activeElement); e.preventDefault(); f[(i + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus(); }
    });
  }

  // ---------- Map: load the Google embed only when asked (no third-party cookies until then) ----------
  $$('[data-map]').forEach((m) => $('button', m)?.addEventListener('click', () => {
    m.innerHTML = `<iframe title="Map to Baked on 8th, 1512 8th Ave S, Nashville" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" src="https://www.google.com/maps?q=Baked+on+8th,+1512+8th+Ave+S,+Nashville,+TN+37203&output=embed"></iframe>`;
  }));

  // ---------- Menu: phones open only the first treat group; today's case hides itself after 3 days ----------
  if (matchMedia('(max-width: 760px)').matches) $$('.menu-group').slice(1).forEach((d) => d.removeAttribute('open'));
  $$('[data-case-date]').forEach((el) => { if (el.dataset.caseDate < addDays(nashNow().ymd, -3).ymd) el.hidden = true; });

  // ---------- Events: split upcoming vs past by today's date in Nashville ----------
  const evRoot = $('[data-events]');
  if (evRoot) {
    const today = nashNow().ymd;
    const items = $$('[data-event-date]', evRoot);
    const up = $('[data-upcoming]'), past = $('[data-past]');
    items.sort((a, b) => a.dataset.eventDate.localeCompare(b.dataset.eventDate));
    items.forEach((el) => {
      const isPast = el.dataset.eventDate < today;
      el.classList.toggle('past', isPast);
      $('.when-label', el).textContent = isPast ? 'Past event' : (el.dataset.eventDate === today ? 'Today' : 'Upcoming');
      (isPast ? past : up).append(el);
    });
    [...past.children].reverse().forEach((c) => past.append(c)); // most recent first
    // nothing coming up: open on the most recent event ("Last time") rather than an empty state
    const lastWrap = $('[data-last-wrap]');
    if (!up.children.length && past.children.length && lastWrap) {
      $('[data-last]', lastWrap).append(past.firstElementChild);
      lastWrap.hidden = false;
    }
    $('[data-upcoming-empty]').hidden = up.children.length > 0;
    if (!up.children.length && $('#up-h')) $('#up-h').textContent = 'Events';
    $('[data-past-wrap]').hidden = past.children.length === 0;
  }

  // a small bar above the phone action bar, for a number that would otherwise be screens away
  const peekBar = (bar, target) => {
    let targetVisible = false, has = false;
    const sync = () => { bar.hidden = !has || targetVisible; };
    if ('IntersectionObserver' in window) new IntersectionObserver(([en]) => { targetVisible = en.isIntersecting; sync(); }).observe(target);
    return (text) => { has = !!text; if (text) $('[data-peek-text]', bar).textContent = text; sync(); };
  };

  // ---------- Custom cake planner (content/custom-cakes.json) ----------
  const planner = $('[data-planner]');
  if (planner) {
    const out = $('[data-planner-summary]');
    const peekEl = $('[data-planner-peek]');
    const peek = peekEl ? peekBar(peekEl, out) : () => {};
    $$('input[name=size]', planner).forEach((x) => { x.dataset.short = $(`label[for="${x.id}"] b`, planner)?.textContent || x.value; });
    let SAMEDAY = { sizes: [], cakes: [] };
    try { SAMEDAY = JSON.parse(planner.dataset.sameday || '{}'); SAMEDAY.sizes ||= []; SAMEDAY.cakes ||= []; } catch { /* no offer */ }
    const upd = () => {
      const fl = $('input[name=flavor]:checked', planner), fr = $('input[name=frosting]:checked', planner), sz = $('input[name=size]:checked', planner), gf = $('input[name=gf]', planner);
      $('[data-sum=flavor]', out).textContent = fl ? fl.value + (gf.checked && fl.dataset.gf ? ' (gluten-friendly)' : '') : 'Pick a flavor';
      $('[data-sum=frosting]', out).textContent = fr ? fr.value : 'Pick a frosting';
      $('[data-sum=size]', out).textContent = sz ? `${sz.value} · feeds ${sz.dataset.feeds}` : 'Pick a size';
      $('[data-sum=price]', out).textContent = sz ? `$${sz.dataset.price}` : '—';
      gf.disabled = !(fl && fl.dataset.gf);
      if (gf.disabled) gf.checked = false;
      $('[data-gf-note]', planner).textContent = fl && !fl.dataset.gf ? `${fl.value} isn’t offered gluten-friendly.` : '';
      const dye = $('[data-dye-note]', planner);
      const dyeable = $$('input[name=frosting][data-dye]', planner).map((x) => x.value.toLowerCase());
      dye.textContent = fr && !fr.dataset.dye && dyeable.length ? `Only ${dyeable.join(' and ')} can be dyed custom colors.` : '';
      const done = fl && fr && sz;
      $('[data-call-script]', out).hidden = !done;
      // "an 8″", "an 11″": the article follows the number's sound
      if (done) $('[data-script]', out).textContent = `${/^(8|11|18)\b|^8/.test(sz.value) ? 'an' : 'a'} ${sz.value} ${fl.value.toLowerCase()}${gf.checked ? ' (gluten-friendly)' : ''} cake with ${fr.value.toLowerCase()}.`;
      // a standard same-day cake (its usual frosting, a same-day size, not gluten-friendly) can be ordered online today
      const match = done && !gf.checked && SAMEDAY.sizes.includes(sz.dataset.short) && SAMEDAY.cakes.find((c) => c.flavor === fl.value && c.frosting === fr.value);
      const offer = $('[data-sameday-offer]', out);
      if (offer) { offer.hidden = !match; if (match) { $('b', offer).textContent = `This one’s on our same-day menu (${match.name}).`; $('[data-sameday-when]', offer).textContent = sameDayLine(); } }
      // phones: "Red velvet · 8″ · from $68" stays in reach while choosing
      const bits = [fl ? fl.value : (fr ? fr.value : ''), sz ? sz.dataset.short : ''].filter(Boolean);
      peek(fl || fr || sz ? `${bits.join(' · ')}${sz ? ` · from $${sz.dataset.price}` : ' · pick a size for a price'}` : '');
    };
    (shot.get('check') || '').split(',').filter(Boolean).forEach((id) => { const el = document.getElementById(id); if (el) el.checked = true; });
    planner.addEventListener('change', upd); upd();

    // phone bar: while the planner is on screen its main button is the phone call that places a custom order
    const bar = $('[data-planner-cta]');
    if (bar && 'IntersectionObserver' in window) {
      const sq = bar.getAttribute('href'), normal = bar.innerHTML;
      new IntersectionObserver(([en]) => {
        if (en.isIntersecting) {
          bar.dataset.ctaHeld = '1'; bar.href = bar.dataset.plannerCta; bar.parentElement.classList.add('planner-mode');
          bar.innerHTML = `${icon('phone', 18)} <span>Call to order</span>`;
        } else if (bar.dataset.ctaHeld) {
          delete bar.dataset.ctaHeld; bar.href = sq; bar.innerHTML = normal; bar.parentElement.classList.remove('planner-mode');
          tickClock();
        }
      }, { rootMargin: '0px 0px -30% 0px' }).observe(planner);
    }
  }

  // phone bar on Weddings: once the inquiry form is on screen, the main button is the phone call instead
  const formBar = $('[data-form-cta]'), wform = $('[data-wedding-form]');
  if (formBar && wform && 'IntersectionObserver' in window) {
    const normal = formBar.innerHTML, href = formBar.getAttribute('href');
    new IntersectionObserver(([en]) => {
      const on = en.isIntersecting;
      formBar.href = on ? formBar.dataset.formCta : href;
      formBar.innerHTML = on ? `${icon('phone', 18)} <span>Call</span>` : normal;
      formBar.parentElement.classList.toggle('planner-mode', on);
    }, { rootMargin: '0px 0px -30% 0px' }).observe(wform);
  }

  // ---------- Wedding inquiry: validated, then sent by the visitor from their own email (no form service yet) ----------
  const form = $('[data-wedding-form]');
  if (form) {
    const status = $('.form-status', form);
    const est = $('[data-estimate]'), inlineEst = $('[data-inline-estimate]');
    const fields = $$('[data-field]', form);
    const field = (n) => form.elements[n];
    // wedding prices come from content/weddings.json via the form's data attributes
    const PER = +form.dataset.perServing || 6, DELIVERY = form.dataset.delivery || '75', PHONE_HOURS = form.dataset.phoneHours || 'Mon–Fri, 8am–3pm';
    const updEst = () => {
      const g = Math.max(0, parseInt(field('guests').value, 10) || 0);
      const d = field('delivery').value === 'Yes';
      const total = `$${(g * PER).toLocaleString('en-US')}`;
      est.textContent = g ? total : '—';
      $('[data-estimate-extra]').textContent = !g ? 'Enter a guest count to see a starting price.' : `${g} servings × $${PER.toFixed(2)}${d ? `, plus delivery from $${DELIVERY}` : ''}.`;
      // phones: the estimate sits right under the guest count, where people are typing
      if (inlineEst) inlineEst.textContent = g ? `~${g} guests · from ${total}${d ? ` + delivery from $${DELIVERY}` : ''}` : '';
    };
    form.addEventListener('input', updEst); updEst();
    // within two weeks: a nudge to call, not a policy
    const dateHint = $('[data-date-hint]', form);
    const updDate = () => { const v = field('date').value; if (dateHint) dateHint.textContent = v && v <= addDays(nashNow().ymd, 14).ymd ? 'Short notice? Call us at 615-933-1100 to check availability.' : ''; };
    field('date').addEventListener('change', updDate); field('date').addEventListener('input', updDate);
    // earliest date is tomorrow in Nashville, not tomorrow in UTC (which blocked "tomorrow" after ~7pm there)
    const minDate = addDays(nashNow().ymd, 1).ymd;
    field('date').min = minDate;
    const check = (wrap) => {
      const el = $('input, textarea, select', wrap); let msg = '';
      const v = el.value.trim();
      if (el.required && !v) msg = wrap.dataset.required || 'Please fill this in.';
      else if (el.type === 'email' && v && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v)) msg = 'Please enter a valid email address.';
      else if (el.type === 'tel' && v && (!/^\+?[\d\s().-]+$/.test(v) || v.replace(/\D/g, '').length < 7 || v.replace(/\D/g, '').length > 15)) msg = el.required ? 'Please enter a valid phone number so we can call you.' : 'Please enter a phone number (7 to 15 digits; a + for international is fine).';
      else if (el.type === 'date' && v && v < minDate) msg = 'Please choose a date in the future.';
      else if (el.type === 'number' && v && (+v < 1 || +v > 1000)) msg = 'Please enter a guest count between 1 and 1000.';
      $('.err', wrap).textContent = msg;
      wrap.toggleAttribute('data-invalid', !!msg);
      el.setAttribute('aria-invalid', String(!!msg));
      return !msg;
    };
    const DRAFT = 'bo8-wedding-draft';
    const saveDraft = () => {
      try {
        const d = {}; [...form.elements].forEach((el) => { if (!el.name) return; if (el.type === 'checkbox') { (d[el.name] ||= []); if (el.checked) d[el.name].push(el.value); } else d[el.name] = el.value; });
        d._saved = Date.now(); localStorage.setItem(DRAFT, JSON.stringify(d));
      } catch { /* private mode or storage blocked: the form still works */ }
    };
    try {
      let d = JSON.parse(localStorage.getItem(DRAFT) || 'null');
      // a draft holds names, email and phone on this device: forget it after 30 days (it's cleared on send too)
      if (d && !(Date.now() - d._saved < 30 * 864e5)) { localStorage.removeItem(DRAFT); d = null; }
      if (d) [...form.elements].forEach((el) => { if (!el.name || !(el.name in d)) return; if (el.type === 'checkbox') el.checked = d[el.name].includes(el.value); else el.value = d[el.name]; });
    } catch { /* ignore a broken draft */ }
    // "Phone call" as the best way to reach you makes Phone required; back to Email, it's optional again
    const phoneWrap = field('phone').closest('[data-field]');
    const updPhoneReq = () => {
      const need = field('contact').value === 'Phone call';
      field('phone').required = need;
      field('phone').setAttribute('aria-required', String(need));
      const star = $('[data-phone-req]', form); if (star) star.hidden = !need;
      if (need) phoneWrap.dataset.required = 'Please enter a valid phone number so we can call you.';
      else { delete phoneWrap.dataset.required; if (phoneWrap.hasAttribute('data-invalid')) check(phoneWrap); }
    };
    field('contact').addEventListener('change', updPhoneReq);
    updEst(); updDate(); updPhoneReq();
    form.addEventListener('input', saveDraft); form.addEventListener('change', saveDraft);
    fields.forEach((w) => $('input, textarea, select', w).addEventListener('blur', () => w.hasAttribute('data-touched') || $('input, textarea, select', w).value ? (w.setAttribute('data-touched', ''), check(w)) : null));
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const bad = fields.filter((w) => !check(w));
      status.className = 'form-status';
      if (bad.length) {
        status.classList.add('show', 'error');
        status.innerHTML = `<h3>A couple of details are missing</h3><p>Please check the ${bad.length === 1 ? 'highlighted field' : `${bad.length} highlighted fields`}.</p>`;
        $('input, textarea, select', bad[0]).focus();
        return;
      }
      const v = (n) => field(n).value.trim();
      const flavors = $$('input[name=flavors]:checked', form).map((c) => c.value).join(', ') || 'Not sure yet';
      const body = [
        'Hi Baked on 8th,', '', 'We’d like to ask about a wedding cake.', '',
        `Names: ${v('names')}`, `Email: ${v('email')}`, `Phone: ${v('phone') || '—'}`,
        `Wedding date: ${v('date')}`, `Venue / area: ${v('venue') || '—'}`, `Guests to serve: ${v('guests')}`,
        `Delivery needed: ${v('delivery')}`, `Flavors we like: ${flavors}`, `Best way to reach us: ${v('contact')}`, '',
        'Design ideas:', v('notes') || '—', '', 'Thank you!'
      ].join('\n');
      const subject = `Wedding cake inquiry – ${v('date')} – ${v('names')}`;
      const href = `mailto:info@bakedon8th.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      try { localStorage.removeItem(DRAFT); } catch { /* nothing saved */ }
      // Form service hook: with Netlify Forms this becomes a real submit and a "Thanks, we've got it" message.
      status.classList.add('show', 'info');
      status.innerHTML = `<h3>Your inquiry is ready to send</h3>
        <p>Send it to <b>info@bakedon8th.com</b> one of two ways: open it in your email app, or copy it and paste it into Gmail or any other email.</p>
        <p class="send-row"><a class="btn" href="${href}" data-open-mail>${icon('mail', 18)} Open email app</a><button type="button" class="btn" data-copy>${icon('copy', 18)}<span>Copy my inquiry</span></button></p>
        <p class="small copy-note" data-copy-note aria-live="polite"></p>
        <details><summary>See what you’ll send</summary><pre>${body.replace(/[&<]/g, (c) => ({ '&': '&amp;', '<': '&lt;' }[c]))}</pre></details>
        <p class="small" style="margin:12px 0 0">Prefer to talk? Call <a class="link" href="tel:+16159331100">615-933-1100</a> (consultations ${PHONE_HOURS}).</p>`;
      $('[data-copy]', status).addEventListener('click', async () => {
        const note = $('[data-copy-note]', status);
        try { await navigator.clipboard.writeText(`To: info@bakedon8th.com\nSubject: ${subject}\n\n${body}`); note.textContent = 'Copied. Paste it into a new email to info@bakedon8th.com.'; }
        catch { note.textContent = 'Copying didn’t work here. Open “See what you’ll send” and select the text.'; }
      });
      status.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'nearest' });
      $('[data-open-mail]', status).focus({ preventScroll: true });
    });
  }


  // ---------- Review notes (demo only): questions for the owners, then where the page's facts come from ----------
  const noted = $$('[data-note]');
  const sources = [...new Set($$('[data-source]').flatMap((el) => el.dataset.source.split('; ')))];
  // ?clean hides the demo notes for a live walkthrough (animations stay on)
  if ((noted.length || sources.length) && !new URLSearchParams(location.search).has('clean')) {
    const escH = (t) => t.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
    noted.forEach((el) => { const f = document.createElement('span'); f.className = 'note-flag'; f.textContent = el.dataset.note; el.after(f); });
    const btn = document.createElement('button');
    btn.className = 'review-toggle'; btn.type = 'button'; btn.setAttribute('aria-expanded', 'false');
    btn.setAttribute('aria-label', `Demo review notes: ${noted.length} to confirm`);
    btn.innerHTML = `<span class="rt-long">Demo · review notes</span><span class="rt-short" aria-hidden="true">Notes</span> <b>${noted.length}</b>`;
    const panel = document.createElement('div');
    panel.className = 'notes-panel'; panel.id = 'notes-panel';
    panel.innerHTML = (noted.length ? `<h4>To confirm with Baked on 8th (this page)</h4><ol>${noted.map((n) => `<li>${escH(n.dataset.note)}</li>`).join('')}</ol>` : '')
      + (sources.length ? `<h4>Where this page's facts come from</h4><ul>${sources.map((x) => `<li>${escH(x)}</li>`).join('')}</ul>` : '');
    btn.setAttribute('aria-controls', 'notes-panel');
    btn.addEventListener('click', () => { const on = document.body.classList.toggle('show-notes'); btn.setAttribute('aria-expanded', String(on)); });
    document.body.append(btn, panel);
  }

  // ---------- Soft page transitions (skipped where the browser does cross-document view transitions) ----------
  if (!reduce && !('onpagereveal' in window)) {
    document.addEventListener('click', (e) => {
      const a = e.target.closest('a');
      if (!a || e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || a.target || a.hasAttribute('download')) return;
      const u = new URL(a.href, location.href);
      if (u.origin !== location.origin || (u.pathname === location.pathname && u.hash) || !/\.html$|\/$/.test(u.pathname)) return;
      e.preventDefault(); document.body.classList.add('is-leaving');
      setTimeout(() => (location.href = a.href), 220);
    });
    addEventListener('pageshow', () => document.body.classList.remove('is-leaving'));
  }

  function icon(n, w = 22) {
    const d = {
      x: 'M6 6l12 12M18 6L6 18', left: 'M15 6l-6 6 6 6', right: 'M9 6l6 6-6 6',
      mail: 'M3 5h18v14H3zM3 7l9 6 9-6', copy: 'M8 8h12v12H8zM4 16V4h12',
      phone: 'M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2',
    }[n];
    return `<svg viewBox="0 0 24 24" width="${w}" height="${w}" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${d}"/></svg>`;
  }
})();
