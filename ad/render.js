/* يرسم ad.html إطارًا إطارًا عبر بروتوكول كروم، ويمرّرها مباشرة إلى ffmpeg.
   لا ملفات وسيطة على القرص. الاستعمال:  node render.js [عرض] [ارتفاع] [اسم الملف] */
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

/* كروم: من متغيّر البيئة، أو نسخة بلايرايت، أو ما هو مثبّت في النظام */
const CHROME = process.env.CHROME || (function(){
  const g = require('fs');
  const guesses = [
    '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    '/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
  ];
  for(const c of guesses) if(g.existsSync(c)) return c;
  throw new Error('لم أجد كروم — عيّن CHROME=/path/to/chrome');
})();
/* ffmpeg: حزمة ffmpeg-static إن وُجدت، وإلا ffmpeg من النظام */
const FFMPEG = process.env.FFMPEG || (function(){
  for(const m of ['ffmpeg-static', path.join(__dirname, '../enc/node_modules/ffmpeg-static')]){
    try{ return require(m); }catch(e){}
  }
  return 'ffmpeg';
})();
const W = +(process.argv[2] || 1080);
const H = +(process.argv[3] || 1920);
const OUT = path.join(__dirname, process.argv[4] || 'jahiz-ad.mp4');
const FPS = 30;
const PAGE = 'file://' + path.join(__dirname, 'ad.html') + '?static';

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main(){
  const port = 9333 + Math.floor(Math.random() * 300);
  const chrome = spawn(CHROME, [
    '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars',
    '--disable-dev-shm-usage', '--force-device-scale-factor=1',
    '--font-render-hinting=none', '--disable-lcd-text',
    '--remote-debugging-port=' + port, 'about:blank'
  ], { stdio: ['ignore', 'ignore', 'ignore'] });

  // انتظر منفذ التنقيح
  let targets = null;
  for(let i = 0; i < 60 && !targets; i++){
    await sleep(250);
    try{ targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); }catch(e){}
  }
  if(!targets) throw new Error('لم يبدأ كروم');
  const page = targets.find(t => t.type === 'page');

  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });

  let id = 0;
  const waiting = new Map();
  const events = new Map();
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if(m.id && waiting.has(m.id)){
      const { res, rej } = waiting.get(m.id); waiting.delete(m.id);
      m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result);
    } else if(m.method && events.has(m.method)){
      events.get(m.method)(); events.delete(m.method);
    }
  };
  const send = (method, params) => new Promise((res, rej) => {
    const i = ++id; waiting.set(i, { res, rej });
    ws.send(JSON.stringify({ id: i, method, params: params || {} }));
  });
  const once = method => new Promise(res => events.set(method, res));

  await send('Page.enable');
  await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride',
    { width: W, height: H, deviceScaleFactor: 1, mobile: false });

  const loaded = once('Page.loadEventFired');
  await send('Page.navigate', { url: PAGE });
  await loaded;
  // لا تلتقط قبل أن تجهز الخطوط، وإلا خرجت الإطارات الأولى بخط بديل
  await send('Runtime.evaluate', { expression: 'document.fonts.ready.then(()=>1)', awaitPromise: true });
  await sleep(400);

  const dur = (await send('Runtime.evaluate', { expression: 'window.__dur', returnByValue: true })).result.value;

  // وضع اللقطات: STILLS="1.2,4.1,..." يلتقط لحظات بعينها بدل الفيديو
  if(process.env.STILLS){
    const ts = process.env.STILLS.split(',').map(Number);
    for(let i = 0; i < ts.length; i++){
      await send('Runtime.evaluate', { expression: `__seek(${ts[i]})`, returnByValue: true });
      const sh = await send('Page.captureScreenshot', { format: 'jpeg', quality: 92 });
      fs.writeFileSync(path.join(__dirname, 'still_' + i + '.jpg'), Buffer.from(sh.data, 'base64'));
    }
    ws.close(); chrome.kill();
    console.log('لقطات: ' + ts.length);
    return;
  }

  const frames = Math.round(dur * FPS);

  const ff = spawn(FFMPEG, [
    '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-i', 'pipe:0',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '19',
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT
  ], { stdio: ['pipe', 'ignore', 'pipe'] });
  let ffErr = '';
  ff.stderr.on('data', d => { ffErr += d; if(ffErr.length > 4000) ffErr = ffErr.slice(-4000); });
  const done = new Promise((res, rej) =>
    ff.on('close', c => c === 0 ? res() : rej(new Error('ffmpeg ' + c + '\n' + ffErr))));

  const write = buf => new Promise(res => ff.stdin.write(buf) ? res() : ff.stdin.once('drain', res));

  for(let f = 0; f < frames; f++){
    const t = f / FPS;
    await send('Runtime.evaluate', { expression: `__seek(${t})`, returnByValue: true });
    const shot = await send('Page.captureScreenshot', { format: 'jpeg', quality: 94 });
    await write(Buffer.from(shot.data, 'base64'));
    if(f % 75 === 0) process.stdout.write(`  ${f}/${frames}\n`);
    // لقطة الغلاف من أقوى لحظة: بطاقة «لا تفتح»
    if(Math.abs(t - 14.2) < 0.02)
      fs.writeFileSync(path.join(__dirname, 'cover.jpg'), Buffer.from(shot.data, 'base64'));
  }
  ff.stdin.end();
  await done;

  ws.close(); chrome.kill();
  const kb = Math.round(fs.statSync(OUT).size / 1024);
  console.log(`تم: ${OUT} — ${frames} إطارًا، ${dur} ثانية، ${kb} ك.ب`);
}
main().catch(e => { console.error('فشل:', e.message); process.exit(1); });
