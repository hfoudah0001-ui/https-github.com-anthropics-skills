#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
يركّب مسار التعليق الصوتي: يضع كل جملة في لحظتها من الفيديو (٢٥ ثانية، ٤٤١٠٠).
المقاطع نفسها تُولَّد من خدمة تركيب الكلام ثم تُنظَّف وتُحفظ في vo/*.wav.

    python3 voice.py vo-track.wav [مجلد الجمل]

المجلد الافتراضي vo/ (صوت مولّد من خدمة)، و vo-free/ للنسخة المجانية.
"""
import math, struct, sys, wave

SR   = 44100
DUR  = 25.0
N    = int(SR * DUR)

# الجملة → لحظة بدايتها على شريط الفيديو
CUES = [
    ('vo/a.wav',  0.45),   # يومان على اختبارك… وتسعة فصول.          [الخطّاف]
    ('vo/b.wav',  5.80),   # الأهم ليس ترتيب الفصول، بل وزن الموضوع… [القاعدة + الإدخال]
    ('vo/c.wav', 12.85),   # ويقول ما لا يقوله غيره: لا تفتحها.      [بعد الضربة بلحظة]
    ('vo/d.wav', 18.05),   # خطة بالدقيقة، ومؤقت لكل جلسة.           [الجلسات]
    ('vo/e.wav', 21.10),   # جاهز. مجاني، ومن المتصفح مباشرة.        [الختام]
]

L = [0.0] * N
R = [0.0] * N

def read_wav(path):
    with wave.open(path, 'rb') as w:
        assert w.getframerate() == SR, path + ': تردد غير متوقع'
        n, ch = w.getnframes(), w.getnchannels()
        raw = w.readframes(n)
    vals = struct.unpack('<%dh' % (len(raw) // 2), raw)
    if ch == 2:                                   # لو جاء ثنائيًا: خذ متوسط القناتين
        vals = [(vals[i] + vals[i+1]) / 2 for i in range(0, len(vals), 2)]
    return [v / 32768.0 for v in vals]

SRC = sys.argv[2] if len(sys.argv) > 2 else 'vo'

for path, at in CUES:
    path = path.replace('vo/', SRC + '/', 1)
    s = read_wav(path)
    fade = int(0.012 * SR)                        # تلاشٍ قصير يمنع الطقطقة
    for i in range(min(fade, len(s))):
        s[i] *= i / fade
        s[-1 - i] *= i / fade
    i0 = int(at * SR)
    for k, v in enumerate(s):
        j = i0 + k
        if 0 <= j < N:
            L[j] += v
            R[j] += v
    print('%-10s %5.2f → %5.2f ث' % (path.split('/')[-1], at, at + len(s) / SR))

peak = max(max(abs(v) for v in L), 1e-9)
g = 0.92 / peak if peak > 0.92 else 1.0
out = sys.argv[1] if len(sys.argv) > 1 else 'vo-track.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    frames = bytearray()
    for i in range(N):
        for v in (L[i] * g, R[i] * g):
            frames += struct.pack('<h', int(max(-1.0, min(1.0, v)) * 32767))
    w.writeframes(bytes(frames))
print('%s — ذروة %.2f، كسب %.2f' % (out, peak, g))
