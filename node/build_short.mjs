// build_short.mjs — data-driven renderer for the Lingopie viral pause-&-reveal shorts.
// Reads a resolved build.json (produced by the Python pipeline) and writes
// <publicDir>/index.html + <timingsPath> (ptimings.json the muxer reads).
// One file covers every style: s2 (POV hook), s3 (challenge hook), s4 (word-counter).
//
//   node build_short.mjs path/to/build.json
import fs from 'node:fs';
import path from 'node:path';

const cfg = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const { style, publicDir, timingsPath } = cfg;
const FPS = cfg.fps || 30, W = cfg.w || 1080, H = cfg.h || 1920, ACCENT = cfg.accent || '#FF8243';
const HOLD = cfg.hold ?? 3.8, INTRO = cfg.intro ?? 3.6, CTADUR = cfg.ctadur ?? 6.6;
const F = (n) => Number(n).toFixed(4);
const isS4 = style === 's4';

const SEG = { seg1: { dur: cfg.segDurs[0], src: cfg.segSrc[0] }, seg2: { dur: cfg.segDurs[1], src: cfg.segSrc[1] },
              seg3: { dur: cfg.segDurs[2], src: cfg.segSrc[2] }, seg4: { dur: cfg.segDurs[3], src: cfg.segSrc[3] } };
const STOPS = cfg.stops;      // [{id,word,en,tag,phrase:[..],hl}]
const LINES = cfg.lines;      // [[srcStart,text]...]
const HK = cfg.hook;          // {badge,big1,big2,sub}
const CTA = cfg.cta;          // {recap?,tag,btn,store,follow?}

const order = ['seg1', 'STOP0', 'seg2', 'STOP1', 'seg3', 'STOP2', 'seg4'];
let t = INTRO; const seg = {}; const stopAt = [];
for (const item of order) {
  if (item.startsWith('STOP')) { const i = +item.slice(4); stopAt[i] = t; t += HOLD; }
  else { seg[item] = { at: t, dur: SEG[item].dur, src: SEG[item].src }; t += SEG[item].dur; }
}
const DUR0 = t, CTA_AT = DUR0 + 0.1, DUR = CTA_AT + CTADUR + 0.5;
const comp = (srcT) => {
  for (const k of ['seg1', 'seg2', 'seg3', 'seg4']) { const s = seg[k];
    if (srcT >= s.src && srcT < s.src + s.dur + 1e-6) return s.at + (srcT - s.src); }
  return null;
};
const R = stopAt.map((v) => v + 1.35);

const segHtml = ['seg1', 'seg2', 'seg3', 'seg4'].map((k, i) =>
  `<video class="vid clip" id="${k}" src="${k}.mp4" muted playsinline data-start="${F(seg[k].at)}" data-duration="${F(seg[k].dur)}" data-track-index="${1 + i}"></video>`).join('\n  ');
const freezeHtml = STOPS.map((s, i) =>
  `<img class="vid clip" id="frz-${i}" src="frz-seg${i + 1}.png" data-start="${F(stopAt[i])}" data-duration="${F(HOLD)}" data-track-index="${10 + i}" data-layout-allow-occlusion />`).join('\n  ');

const capItems = [];
for (const k of ['seg1', 'seg2', 'seg3', 'seg4']) {
  const s = seg[k];
  const inSeg = LINES.filter(([ts]) => ts >= s.src && ts < s.src + s.dur);
  inSeg.forEach(([ts, text], j) => {
    const start = (j === 0) ? s.at : comp(ts);
    const nextTs = inSeg[j + 1] ? inSeg[j + 1][0] : null;
    const end = nextTs != null ? comp(nextTs) : s.at + s.dur;
    capItems.push({ start, dur: Math.max(0.2, end - start), text });
  });
}
const capHtml = capItems.map((c, i) =>
  `<div class="cap clip" id="cap-${i}" data-start="${F(c.start)}" data-duration="${F(c.dur)}" data-track-index="${50 + i}"><span>${c.text}</span></div>`).join('\n  ');

const cStates = isS4 ? [
  { n: 0, start: INTRO, end: R[0] }, { n: 1, start: R[0], end: R[1] },
  { n: 2, start: R[1], end: R[2] }, { n: 3, start: R[2], end: DUR0 }] : [];
const counterHtml = cStates.map((c, i) =>
  `<div class="wc clip${c.n === 3 ? ' wc-done' : ''}" id="wc-${i}" data-start="${F(c.start)}" data-duration="${F(c.end - c.start)}" data-track-index="${40 + i}"><span class="wc-ic">${c.n === 3 ? '🏆' : '◍'}</span><span class="wc-n">${c.n}</span><span class="wc-t">/3 words</span></div>`).join('\n  ');

const overlayHtml = STOPS.map((s, i) => {
  const b = 100 + i * 10, T = stopAt[i];
  const phrase = s.phrase.map((w, k) => k === s.hl ? `<span class="hl" id="hl-${i}">${w}</span>` : `<span>${w}</span>`).join(' ');
  return `
  <div class="scrim clip" id="scrim-${i}" data-start="${F(T)}" data-duration="${F(HOLD)}" data-track-index="${b}"></div>
  <div class="psub clip" id="psub-${i}" data-start="${F(T)}" data-duration="${F(HOLD)}" data-track-index="${b + 1}">${phrase}</div>
  <div class="tap clip" id="tap-${i}" data-start="${F(T)}" data-duration="${F(HOLD)}" data-track-index="${b + 2}"><div class="ripple"></div><div class="finger">👆</div></div>
  <div class="bubble clip" id="bub-${i}" data-start="${F(T)}" data-duration="${F(HOLD)}" data-track-index="${b + 3}">
    <div class="b-top"><span class="spk">🔊</span><span class="b-word">${s.word}</span></div>
    <div class="b-tr">${s.en}</div><div class="b-tag">${s.tag}</div>
  </div>`;
}).join('\n');

const anim = STOPS.map((s, i) => { const T = stopAt[i];
  return `
    tl.fromTo('#scrim-${i}',{opacity:0},{opacity:1,duration:0.3,ease:'power2.out'},${F(T)});
    tl.fromTo('#psub-${i}',{opacity:0,y:20},{opacity:1,y:0,duration:0.35,ease:'power3.out'},${F(T + 0.12)});
    tl.fromTo('#hl-${i}',{backgroundSize:'0% 100%'},{backgroundSize:'100% 100%',duration:0.3,ease:'power2.out'},${F(T + 0.5)});
    tl.fromTo('#hl-${i}',{scale:1},{scale:1.14,duration:0.18,yoyo:true,repeat:1,ease:'power2.out'},${F(T + 0.55)});
    tl.fromTo('#tap-${i} .ripple',{scale:0.2,opacity:0.9},{scale:2.4,opacity:0,duration:0.6,ease:'power2.out'},${F(T + 0.4)});
    tl.set('#tap-${i} .ripple',{opacity:0},${F(T + 1.0)});
    tl.fromTo('#tap-${i} .finger',{scale:1.15,y:-6,opacity:0},{scale:1,y:0,opacity:1,duration:0.18},${F(T + 0.35)});
    tl.set('#tap-${i} .finger',{opacity:0},${F(T + 1.2)});
    tl.fromTo('#bub-${i}',{opacity:0,scale:0.6,y:18},{opacity:1,scale:1,y:0,duration:0.5,ease:'back.out(2.2)'},${F(T + 0.66)});
    tl.to(['#scrim-${i}','#psub-${i}','#bub-${i}','#tap-${i}'],{opacity:0,duration:0.35,ease:'power2.in'},${F(T + HOLD - 0.4)});
    tl.set(['#scrim-${i}','#psub-${i}','#bub-${i}','#tap-${i}'],{opacity:0},${F(T + HOLD)});`;
}).join('\n');

const capAnim = capItems.map((c, i) =>
  `    tl.fromTo('#cap-${i}',{opacity:0,y:12},{opacity:1,y:0,duration:0.22,ease:'power2.out'},${F(c.start)});`).join('\n');
const counterAnim = cStates.map((c, i) =>
  `    tl.fromTo('#wc-${i}',{opacity:0,scale:0.6},{opacity:1,scale:1,duration:0.34,ease:'back.out(2.4)'},${F(c.start)});` +
  (c.n > 0 ? `\n    tl.to('#wc-${i}',{scale:1.14,duration:0.16,yoyo:true,repeat:1,ease:'power2.out'},${F(c.start + 0.02)});` : '') +
  (c.n === 3 ? `\n    tl.to('#wc-${i}',{scale:1.1,duration:0.5,yoyo:true,repeat:3,ease:'sine.inOut'},${F(c.start + 0.4)});` : '')
).join('\n');

const introAnim = `
    tl.fromTo('#hookwrap',{opacity:0},{opacity:1,duration:0.25,ease:'power2.out'},0.04);
    tl.fromTo('#h-pausebadge',{opacity:0,scale:0.7},{opacity:1,scale:1,duration:0.4,ease:'back.out(2)'},0.1);
    tl.fromTo('#h-big1',{opacity:0,y:26},{opacity:1,y:0,duration:0.32,ease:'power3.out'},0.22);
    tl.fromTo('#h-big2',{opacity:0,y:26},{opacity:1,y:0,duration:0.32,ease:'power3.out'},0.36);
    tl.fromTo('#h-sub',{opacity:0,y:16},{opacity:1,y:0,duration:0.3,ease:'power3.out'},${F(Math.min(1.0, INTRO - 1.2))});
    tl.to('#h-sub',{scale:1.05,duration:0.45,yoyo:true,repeat:1,ease:'sine.inOut'},${F(INTRO - 1.0)});
    tl.to(['#hookwrap','#h-pausebadge'],{opacity:0,duration:0.28,ease:'power2.in'},${F(INTRO - 0.3)});
    tl.set(['#hookwrap','#h-pausebadge'],{opacity:0},${F(INTRO)});
    tl.set('#cold',{opacity:0},${F(INTRO)});`;

const ctaRecapHtml = isS4 && CTA.recap ? `<div class="cta-recap" id="cta-recap">${CTA.recap}</div>` : '';
const ctaFollowHtml = CTA.follow ? `<div class="cta-follow" id="cta-follow">${CTA.follow}</div>` : '';
const ctaAnim = `
    tl.fromTo('#ctaout',{opacity:0},{opacity:1,duration:0.45,ease:'power2.out'},${F(CTA_AT)});` +
  (ctaRecapHtml ? `\n    tl.fromTo('#ctaout .cta-recap',{opacity:0,scale:0.8},{opacity:1,scale:1,duration:0.45,ease:'back.out(2)'},${F(CTA_AT + 0.1)});` : '') +
  `\n    tl.fromTo('#ctaout .dr-mark',{opacity:0,scale:0.85},{opacity:1,scale:1,duration:0.5,ease:'back.out(1.8)'},${F(CTA_AT + (ctaRecapHtml ? 0.5 : 0.1))});
    tl.fromTo('#ctaout .cta-tag',{opacity:0,y:14},{opacity:1,y:0,duration:0.4},${F(CTA_AT + 0.7)});
    tl.fromTo('#ctaout .cta-btn',{opacity:0,scale:0.85},{opacity:1,scale:1,duration:0.45,ease:'back.out(2.4)'},${F(CTA_AT + 0.9)});
    tl.to('#ctaout .cta-btn',{scale:1.06,duration:0.5,yoyo:true,repeat:3,ease:'sine.inOut'},${F(CTA_AT + 1.4)});
    tl.fromTo('#ctaout .cta-store',{opacity:0},{opacity:1,duration:0.4},${F(CTA_AT + 1.2)});` +
  (ctaFollowHtml ? `\n    tl.fromTo('#ctaout .cta-follow',{opacity:0,y:14},{opacity:1,y:0,duration:0.4,ease:'power3.out'},${F(CTA_AT + 1.8)});` : '');

const html = `<!doctype html>
<html lang="es"><head><meta charset="utf-8"/><style>
@font-face{font-family:'Inter';src:url('fonts/Inter-400-latin.woff2') format('woff2');font-weight:400;font-display:block;}
@font-face{font-family:'Inter';src:url('fonts/Inter-700-latin.woff2') format('woff2');font-weight:700;font-display:block;}
@font-face{font-family:'Poppins';src:url('fonts/Poppins-800.woff2') format('woff2');font-weight:800;font-display:block;}
:root{--accent:${ACCENT};}
*{box-sizing:border-box;margin:0;padding:0;}
html,body{width:${W}px;height:${H}px;overflow:hidden;background:#000;font-family:'Inter',sans-serif;}
#stage{position:relative;width:${W}px;height:${H}px;overflow:hidden;background:#000;}
.vid{position:absolute;inset:0;width:${W}px;height:${H}px;object-fit:cover;z-index:1;}
.scrim{position:absolute;inset:0;z-index:60;opacity:0;background:rgba(6,6,10,0.55);}
.topgrad{position:absolute;top:0;left:0;right:0;height:300px;z-index:8;background:linear-gradient(180deg,rgba(0,0,0,0.6),transparent);}
.botgrad{position:absolute;bottom:0;left:0;right:0;height:520px;z-index:8;background:linear-gradient(0deg,rgba(0,0,0,0.72),transparent);}
.brandmark{position:absolute;top:60px;left:56px;z-index:30;font-family:'Poppins';font-weight:800;font-size:40px;color:#fff;letter-spacing:-1px;text-shadow:0 3px 14px rgba(0,0,0,0.6);}
.brandmark span{color:var(--accent);}
.wc{position:absolute;top:64px;left:50%;transform:translateX(-50%);z-index:34;display:flex;align-items:center;gap:12px;font-family:'Poppins';font-weight:800;background:rgba(10,8,14,0.55);border:2px solid rgba(255,255,255,0.22);border-radius:999px;padding:14px 30px;backdrop-filter:blur(3px);text-shadow:0 2px 8px rgba(0,0,0,0.6);}
.wc .wc-ic{font-size:38px;} .wc .wc-n{font-size:52px;color:var(--accent);} .wc .wc-t{font-size:34px;color:#fff;}
.wc.wc-done{border-color:var(--accent);background:rgba(255,130,67,0.22);} .wc.wc-done .wc-n{color:#fff;}
.cap{position:absolute;left:60px;right:60px;top:1500px;z-index:12;text-align:center;}
.cap span{display:inline;font-family:'Inter';font-weight:800;font-size:60px;line-height:1.28;color:#fff;letter-spacing:-0.5px;-webkit-box-decoration-break:clone;box-decoration-break:clone;padding:6px 4px;text-shadow:0 3px 16px rgba(0,0,0,0.95),0 1px 3px rgba(0,0,0,0.9);}
.psub{position:absolute;left:60px;right:60px;top:1500px;z-index:64;text-align:center;font-family:'Inter';font-weight:800;font-size:66px;line-height:1.2;color:#fff;text-shadow:0 4px 20px rgba(0,0,0,0.9);}
.psub span{padding:0 4px;}
.psub .hl{color:#20140a;background:linear-gradient(var(--accent),var(--accent));background-repeat:no-repeat;background-position:0 0;background-size:0% 100%;border-radius:12px;padding:2px 16px;display:inline-block;box-shadow:0 10px 30px rgba(255,130,67,0.5);}
.tap{position:absolute;left:50%;top:1470px;transform:translateX(-50%);z-index:66;width:0;height:0;}
.tap .ripple{position:absolute;left:-70px;top:-10px;width:140px;height:140px;border-radius:50%;border:6px solid rgba(255,255,255,0.85);}
.tap .finger{position:absolute;left:10px;top:20px;font-size:90px;filter:drop-shadow(0 6px 10px rgba(0,0,0,0.5));}
.bubble{position:absolute;left:50%;top:1120px;transform:translateX(-50%);z-index:68;min-width:520px;background:#fff;border-radius:32px;padding:36px 48px 34px;text-align:center;box-shadow:0 30px 80px rgba(0,0,0,0.55);}
.bubble::after{content:'';position:absolute;left:50%;bottom:-26px;transform:translateX(-50%);border-left:28px solid transparent;border-right:28px solid transparent;border-top:30px solid #fff;}
.bubble .b-top{display:flex;align-items:center;justify-content:center;gap:20px;} .bubble .spk{font-size:52px;}
.bubble .b-word{font-family:'Poppins';font-weight:800;font-size:82px;color:#141416;letter-spacing:-1px;}
.bubble .b-tr{margin-top:10px;font-family:'Inter';font-weight:800;font-size:64px;color:var(--accent);}
.bubble .b-tr::before{content:'→ ';color:#c9c9cf;}
.bubble .b-tag{margin-top:12px;font-family:'Inter';font-weight:700;font-size:30px;letter-spacing:2px;color:#9a9aa2;text-transform:uppercase;}
.hookwrap{position:absolute;inset:0;z-index:82;opacity:0;}
.hookwrap .h-scrim{position:absolute;inset:0;background:linear-gradient(0deg,rgba(0,0,0,0.86) 4%,rgba(0,0,0,0.42) 34%,rgba(0,0,0,0.05) 58%,transparent 72%);}
.hookwrap .h-pausebadge{position:absolute;top:120px;left:50%;transform:translateX(-50%);font-family:'Inter';font-weight:800;font-size:34px;letter-spacing:4px;color:#fff;background:rgba(0,0,0,0.42);border:1px solid rgba(255,255,255,0.28);border-radius:999px;padding:14px 30px;}
.hookwrap .h-text{position:absolute;left:60px;right:60px;bottom:360px;text-align:center;}
.hookwrap .h-big{font-family:'Poppins';font-weight:800;font-size:92px;line-height:1.02;color:#fff;letter-spacing:-2px;text-shadow:0 4px 22px rgba(0,0,0,0.85);}
.hookwrap .h-big.h-accent{color:var(--accent);margin-top:4px;}
.hookwrap .h-sub{margin-top:26px;display:inline-block;font-family:'Inter';font-weight:800;font-size:46px;color:#20140a;background:#fff;border-radius:999px;padding:16px 34px;box-shadow:0 14px 40px rgba(0,0,0,0.4);}
.ctaout{position:absolute;inset:0;z-index:90;opacity:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;text-align:center;padding:0 70px;background:radial-gradient(80% 55% at 50% 42%, rgba(255,130,67,0.30), transparent 62%),linear-gradient(180deg,#17110d,#0c0a11);}
.ctaout .cta-recap{font-family:'Inter';font-weight:800;font-size:44px;color:#fff;background:rgba(255,255,255,0.10);border:1px solid rgba(255,255,255,0.2);border-radius:999px;padding:16px 34px;}
.ctaout .cta-recap b{color:var(--accent);}
.ctaout .dr-mark{font-family:'Poppins';font-weight:800;font-size:100px;color:#fff;letter-spacing:-2px;text-shadow:0 4px 20px rgba(0,0,0,0.5);margin-top:4px;}
.ctaout .dr-mark span{color:var(--accent);}
.ctaout .cta-tag{font-family:'Inter';font-weight:800;font-size:46px;color:#fff;max-width:840px;line-height:1.15;} .ctaout .cta-tag b{color:var(--accent);}
.ctaout .cta-btn{margin-top:10px;font-family:'Inter';font-weight:800;font-size:52px;color:#26140a;background:var(--accent);padding:26px 60px;border-radius:999px;box-shadow:0 16px 48px rgba(255,130,67,0.55);}
.ctaout .cta-store{font-family:'Inter';font-weight:700;font-size:32px;color:rgba(255,255,255,0.6);}
.ctaout .cta-follow{margin-top:18px;font-family:'Inter';font-weight:800;font-size:36px;color:#fff;background:rgba(255,255,255,0.10);border:1px solid rgba(255,255,255,0.22);border-radius:999px;padding:14px 30px;}
</style></head><body>
<div id="stage" data-composition-id="short" data-start="0" data-duration="${F(DUR)}" data-fps="${FPS}" data-width="${W}" data-height="${H}">
  ${segHtml}
  ${freezeHtml}
  <div class="topgrad clip" data-start="${F(INTRO)}" data-duration="${F(DUR0 - INTRO)}" data-track-index="7" data-layout-allow-occlusion></div>
  <div class="botgrad clip" data-start="${F(INTRO)}" data-duration="${F(DUR0 - INTRO)}" data-track-index="8" data-layout-allow-occlusion></div>
  <div class="brandmark clip" data-start="${F(INTRO)}" data-duration="${F(DUR0 - INTRO)}" data-track-index="9">Drama<span>Rizz</span></div>
  ${counterHtml}
  ${capHtml}
${overlayHtml}
  <img class="vid clip" id="cold" src="cold.png" data-start="0" data-duration="${F(INTRO)}" data-track-index="6" data-layout-allow-occlusion />
  <div class="hookwrap clip" id="hookwrap" data-start="0" data-duration="${F(INTRO)}" data-track-index="82">
    <div class="h-scrim"></div>
    <div class="h-pausebadge" id="h-pausebadge">${HK.badge}</div>
    <div class="h-text">
      <div class="h-big" id="h-big1">${HK.big1}</div>
      <div class="h-big h-accent" id="h-big2">${HK.big2}</div>
      <div class="h-sub" id="h-sub">${HK.sub}</div>
    </div>
  </div>
  <div class="ctaout clip" id="ctaout" data-start="${F(CTA_AT)}" data-duration="${F(DUR - CTA_AT)}" data-track-index="95">
    ${ctaRecapHtml}
    <div class="dr-mark">Drama<span>Rizz</span></div>
    <div class="cta-tag">${CTA.tag}</div>
    <div class="cta-btn">${CTA.btn}</div>
    <div class="cta-store">${CTA.store}</div>
    ${ctaFollowHtml}
  </div>
  <script src="vendor/gsap.min.js"></script>
  <script>(function(){
    const tl = window.gsap.timeline({paused:true});
${introAnim}
${counterAnim}
${capAnim}
${anim}
${ctaAnim}
    window.__timelines=window.__timelines||{};window.__timelines['short']=tl;
  })();</script>
</div></body></html>`;

fs.writeFileSync(path.join(publicDir, 'index.html'), html);
const out = { style, dur: DUR, dur0: DUR0, intro: INTRO, cta_at: CTA_AT, hold: HOLD,
  stops: STOPS.map((s, i) => ({ id: s.id, at: stopAt[i] })),
  seg: Object.fromEntries(Object.entries(seg).map(([k, v]) => [k, { at: v.at, dur: v.dur, src: v.src }])) };
fs.writeFileSync(timingsPath, JSON.stringify(out, null, 2));
console.log('built ' + style + ' dur=' + DUR.toFixed(2));
