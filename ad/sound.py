#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
يركّب الشريط الصوتي لإعلان «جاهز» من الصفر — بلا مكتبات وبلا مقاطع جاهزة،
فلا حقوق على أحد. كل صوت مربوط بلحظته في الفيديو:

  ٠.٠  عدّاد يدق في الظلام            ١٢.٤  الضربة الكبرى: «لا تفتح»
  ٢.٨  الدق يتسارع                    ١٦.٦  انفراج، ونقرات إنجاز
  ٥.٦  صمتة ثم وتر صافٍ (القاعدة)      ٢١.٠  وتر الختام
  ٨.٨  نبض خفيف كواجهة تُملأ

    python3 sound.py [out.wav]
"""
import math, random, struct, sys, wave

SR   = 44100
DUR  = 25.0
N    = int(SR * DUR)
L    = [0.0] * N
R    = [0.0] * N
rnd  = random.Random(7)          # ثابت: النتيجة نفسها في كل مرة

# ── أدوات ──
def put(start, samples, pan=0.5, gain=1.0):
    """يضيف مقطعًا في لحظته. pan: ٠ يسار، ١ يمين."""
    i0 = int(start * SR)
    gl, gr = gain * math.sqrt(1 - pan), gain * math.sqrt(pan)
    for k, v in enumerate(samples):
        j = i0 + k
        if 0 <= j < N:
            L[j] += v * gl
            R[j] += v * gr

def kick(amp=1.0, dur=1.0, f0=85.0, f1=32.0, click=0.5):
    """ضربة منخفضة: تردد يهبط بسرعة — أساس كل انتقال."""
    n, out, ph = int(dur * SR), [], 0.0
    for i in range(n):
        t = i / SR
        f = f1 + (f0 - f1) * math.exp(-t * 11.0)
        ph += 2 * math.pi * f / SR
        e = math.exp(-t * 3.0)
        v = math.sin(ph) * e
        if t < 0.006:                                   # نقرة البداية
            v += (rnd.random() * 2 - 1) * click * (1 - t / 0.006)
        out.append(v * amp)
    return out

def tick(amp=0.3, f=2300.0, dur=0.05):
    """دقّة ساعة: ضجيج قصير + رنّة عالية."""
    n, out = int(dur * SR), []
    for i in range(n):
        t = i / SR
        e = math.exp(-t * 190.0)
        out.append(((rnd.random() * 2 - 1) * 0.6 + math.sin(2 * math.pi * f * t) * 0.4) * e * amp)
    return out

def note(freq, dur=0.9, amp=0.4, decay=4.5):
    """نقرة موسيقية: أساس + توافقيان."""
    n, out = int(dur * SR), []
    for i in range(n):
        t = i / SR
        e = math.exp(-t * decay) * min(1.0, t / 0.004)
        out.append((math.sin(2*math.pi*freq*t)
                    + 0.38 * math.sin(4*math.pi*freq*t)
                    + 0.14 * math.sin(6*math.pi*freq*t)) * e * amp)
    return out

def bell(freq, dur=2.2, amp=0.4):
    """رنّة إنجاز — توافقيات غير صحيحة تعطي الطابع المعدني."""
    n, out = int(dur * SR), []
    for i in range(n):
        t = i / SR
        a = math.sin(2*math.pi*freq*t)        * math.exp(-t * 2.2)
        b = math.sin(2*math.pi*freq*2.76*t)   * math.exp(-t * 4.0) * 0.5
        c = math.sin(2*math.pi*freq*5.40*t)   * math.exp(-t * 6.5) * 0.22
        out.append((a + b + c) * min(1.0, t / 0.003) * amp)
    return out

def pad(freqs, dur, amp=0.1, attack=0.45, release=1.0):
    """فرشة مستمرة: كل تردد نسختان متباعدتان قليلًا ليتّسع الصوت."""
    n, out = int(dur * SR), []
    phs = [[0.0, 0.0] for _ in freqs]
    for i in range(n):
        t, s = i / SR, 0.0
        for k, f in enumerate(freqs):
            phs[k][0] += 2 * math.pi * (f - 0.22) / SR
            phs[k][1] += 2 * math.pi * (f + 0.22) / SR
            s += math.sin(phs[k][0]) + math.sin(phs[k][1])
        s /= (2 * len(freqs))
        e = min(1.0, t / attack) * min(1.0, max(0.0, (dur - t) / release))
        out.append(s * e * amp)
    return out

def sweep(dur=1.0, amp=0.3, f_from=250.0, f_to=6000.0, curve=2.0):
    """هسهسة صاعدة أو هابطة — ضجيج عبر مرشّح متحرّك."""
    n, out, y = int(dur * SR), [], 0.0
    for i in range(n):
        p = (i / n) ** curve
        fc = f_from + (f_to - f_from) * p
        a = 1 - math.exp(-2 * math.pi * fc / SR)
        y += a * ((rnd.random() * 2 - 1) - y)
        e = math.sin(math.pi * min(1.0, i / n)) ** 1.2
        out.append(y * e * amp)
    return out

# ═══ الخط الزمني ═══

# ١ و٢ — الظلام والعدّاد (٠ → ٥.٦)
put(0.00, kick(0.85, 1.3, 95, 30))
put(0.00, pad([55, 110, 164.81], 5.9, 0.105), gain=1.0)
t = 0.25
while t < 2.75:                                   # دقّ منتظم
    put(t, tick(0.26), pan=0.58)
    t += 0.5
put(2.80, kick(0.55, 0.9))
t = 2.95
while t < 5.55:                                   # يتسارع مع تراكم الفصول
    put(t, tick(0.20 + 0.10 * (t - 2.95) / 2.6), pan=0.42 if int(t*3) % 2 else 0.58)
    t += 0.33
put(4.65, sweep(0.95, 0.20, 300, 5200))           # صعود قبل الانتقال

# ٣ — القاعدة (٥.٦ → ٨.٨): صمت الدق، ووتر صافٍ
put(5.60, kick(0.62, 1.1, 78, 34))
put(5.62, pad([220, 261.63, 329.63], 3.0, 0.085))
put(6.15, note(261.63, 1.0, 0.30), pan=0.40)      # وزنه في الاختبار
put(6.45, note(329.63, 0.9, 0.26), pan=0.60)      # ×
put(6.65, note(440.00, 1.2, 0.30), pan=0.50)      # ضعفك فيه
put(7.45, sweep(0.55, 0.10, 400, 2600))           # الخط الأخضر يُرسم

# ٤ — الأداة (٨.٨ → ١٢.٤): نبض واجهة
put(8.80, kick(0.45, 0.8))
put(8.82, pad([164.81, 220.00], 3.4, 0.062))
for i, tt in enumerate((9.35, 9.57, 9.79)):       # ثلاثة صفوف تُملأ
    put(tt, note(523.25 if i == 1 else 392.00, 0.5, 0.17, 7.0), pan=0.35 + i * 0.15)
t = 9.0
while t < 12.3:                                   # نبض خافت يحفظ الإيقاع
    put(t, tick(0.055, 1500, 0.03), pan=0.5)
    t += 0.45
put(11.05, tick(0.34, 900, 0.09))                 # ضغطة الزر
put(11.12, note(329.63, 0.6, 0.26, 6.0))
put(11.30, note(440.00, 0.9, 0.30, 5.0))

# ٥ — «لا تفتح هذه المواضيع» (١٢.٤ → ١٦.٦): الضربة
put(12.40, kick(1.00, 1.6, 100, 28, click=0.8))
put(12.42, pad([55, 110, 130.81], 4.2, 0.125, attack=0.10, release=1.3))
put(13.55, sweep(0.30, 0.30, 5000, 500, curve=1.0))   # شطب أول
put(13.78, sweep(0.30, 0.30, 5000, 500, curve=1.0))   # شطب ثانٍ
put(14.95, note(82.41, 1.6, 0.34, 2.2))
put(15.35, kick(0.45, 1.1, 70, 30))                   # «تركها قرار، لا تقصير»

# ٦ — الخطة تعمل (١٦.٦ → ٢١.٠): انفراج
put(16.60, kick(0.60, 1.0, 80, 33))
put(16.62, pad([164.81, 220.00, 329.63], 4.4, 0.095))
t = 16.75
while t < 20.9:
    put(t, tick(0.085, 1900, 0.035), pan=0.45 if int(t*2) % 2 else 0.55)
    t += 0.40
put(18.05, bell(659.25, 1.8, 0.40), pan=0.42)     # ✓ الجلسة الأولى
put(18.55, bell(880.00, 2.0, 0.42), pan=0.58)     # ✓ الثانية
put(18.10, sweep(1.5, 0.085, 500, 3400))          # شريط التقدّم يمتلئ
for i in range(10):                                # الأرقام تعدّ
    put(17.95 + i * 0.1, tick(0.05, 2600, 0.025), pan=0.5)

# ٧ — الختام (٢١.٠ → ٢٥.٠)
put(21.00, kick(0.72, 1.4, 88, 30))
put(21.02, pad([110, 220, 329.63, 440], 3.9, 0.125, attack=0.30, release=1.6))
put(21.08, bell(880.00, 2.6, 0.46))
put(22.55, bell(659.25, 2.4, 0.24), pan=0.40)
put(23.10, note(220.00, 1.8, 0.22, 2.0), pan=0.60)

# ── إنهاء: تلاشٍ، ثم ضغط لطيف، ثم تسوية ──
fade0 = int(23.7 * SR)
for i in range(fade0, N):
    g = max(0.0, 1 - (i - fade0) / (N - fade0))
    L[i] *= g; R[i] *= g

peak = max(max(abs(v) for v in L), max(abs(v) for v in R), 1e-9)
norm = 0.90 / peak if peak > 0.90 else 1.0
out = sys.argv[1] if len(sys.argv) > 1 else 'jahiz-ad.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    frames = bytearray()
    for i in range(N):
        for v in (L[i] * norm, R[i] * norm):
            v = math.tanh(v * 1.08)                   # ضغط لطيف بدل القطع
            frames += struct.pack('<h', int(max(-1.0, min(1.0, v)) * 32767))
    w.writeframes(bytes(frames))
print('%s — %.1f ثانية، ذروة %.2f' % (out, DUR, peak))
