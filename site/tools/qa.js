// Layout QA for the current page: run in the browser console (or inject) at any viewport size.
// Reports horizontal overflow, off-screen elements, clipped text, small tap targets, distorted or broken images.
(() => {
  // show every animated element in its final state so measurements are of the real layout
  const st = document.createElement('style');
  st.textContent = '*{transition:none!important;animation:none!important}';
  document.head.appendChild(st);
  document.querySelectorAll('.reveal,.reveal-img,.pop').forEach((e) => e.classList.add('is-in'));
  document.documentElement.classList.add('is-ready');

  const W = document.documentElement.clientWidth;
  const scrollers = '.cake-rail, .rail, .phone-rail, .subnav .wrap, .form-status pre, .notes-panel, .lightbox, .mobile-nav, [hidden]';
  const visible = (el) => { const s = getComputedStyle(el); const r = el.getBoundingClientRect(); return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0 && !el.closest('[hidden], .mobile-nav:not(.is-open), .lightbox:not(.is-open), .sr-only, .skip'); };
  const name = (el) => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '') + (el.textContent.trim() ? ` "${el.textContent.trim().replace(/\s+/g, ' ').slice(0, 28)}"` : '');
  const all = [...document.querySelectorAll('body *')].filter(visible);

  const offscreen = all.filter((el) => !el.closest(scrollers) && getComputedStyle(el).position !== 'fixed' && (() => { const r = el.getBoundingClientRect(); return r.right > W + 1 || r.left < -1; })()).map(name);

  const clipped = all.filter((el) => /^(H1|H2|H3|P|A|BUTTON|LABEL|SPAN|B|DD|LI)$/.test(el.tagName) && el.children.length < 4 && el.textContent.trim() && el.scrollWidth > el.clientWidth + 2 && getComputedStyle(el).overflowX !== 'visible').map(name);
  const textOverflow = all.filter((el) => /^(H1|H2|H3)$/.test(el.tagName) && !el.closest(scrollers)).filter((el) => { const r = el.getBoundingClientRect(); return [...el.querySelectorAll('*')].concat(el).some((c) => c.getBoundingClientRect().right > Math.min(W, r.right + 4) + 1); }).map(name);

  const small = all.filter((el) => el.matches('a, button, input:not([type=radio]):not([type=checkbox]), select, textarea, .chip label') && getComputedStyle(el).display !== 'inline' && !el.closest('p, li, dd, .crumbs, .footer-grid')).filter((el) => { const r = el.getBoundingClientRect(); return r.height < 43.5 || r.width < 43.5; }).map((el) => `${name(el)} ${Math.round(el.getBoundingClientRect().width)}x${Math.round(el.getBoundingClientRect().height)}`);

  const imgs = [...document.images].filter(visible);
  const distorted = imgs.filter((i) => i.naturalWidth && ['fill', ''].includes(getComputedStyle(i).objectFit) && Math.abs(i.clientWidth / i.clientHeight - i.naturalWidth / i.naturalHeight) > 0.03 * (i.naturalWidth / i.naturalHeight)).map((i) => i.src.split('/').pop());
  const broken = [...document.images].filter((i) => i.getAttribute('src') && i.complete && i.naturalWidth === 0).map((i) => i.src.split('/').pop());

  // fixed bars must not cover the last piece of content
  const bar = document.querySelector('.action-bar');
  const barH = bar && getComputedStyle(bar).display !== 'none' ? bar.offsetHeight : 0;
  const bodyPad = parseFloat(getComputedStyle(document.body).paddingBottom);

  return {
    viewport: `${innerWidth}x${innerHeight}`,
    hOverflow: document.documentElement.scrollWidth > W + 1 ? document.documentElement.scrollWidth - W : 0,
    offscreen: offscreen.slice(0, 8), clipped: clipped.slice(0, 8), headingOverflow: textOverflow.slice(0, 5),
    smallTargets: small.slice(0, 10), distorted, broken,
    actionBarCoversContent: barH > bodyPad + 1,
    fonts: [...new Set([...document.fonts].filter((f) => f.status === 'loaded').map((f) => f.family))].length,
  };
})();
