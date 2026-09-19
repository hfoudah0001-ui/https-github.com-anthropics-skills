#!/usr/bin/env bash
# يجمع الصوت بالصورة: موسيقى + تعليق صوتي، ثم يضعهما على الفيديو.
#   ./mix.sh                          الصوت المولّد من الخدمة  → jahiz-ad.mp4
#   ./mix.sh vo-free jahiz-ad-free.mp4 الصوت المجاني (espeak)   → jahiz-ad-free.mp4
#   FFMPEG=/path/ffmpeg ./mix.sh      لو لم يكن ffmpeg في المسار
set -euo pipefail
cd "$(dirname "$0")"
FF="${FFMPEG:-ffmpeg}"
SRC="${1:-vo}"                         # مجلد جمل التعليق الصوتي
OUT="${2:-jahiz-ad.mp4}"

python3 sound.py jahiz-ad.wav          # الموسيقى
python3 voice.py vo-track.wav "$SRC"   # التعليق الصوتي في مواضعه

# الموسيقى تنخفض تلقائيًا تحت الصوت (sidechain) ثم يُحدّ المزيج
"$FF" -y -hide_banner -loglevel error -i jahiz-ad.wav -i vo-track.wav -filter_complex \
"[0:a]volume=0.80[mus];\
 [1:a]volume=1.85,alimiter=limit=0.95,asplit=2[voc1][voc2];\
 [mus][voc1]sidechaincompress=threshold=0.02:ratio=12:attack=12:release=340[duck];\
 [duck][voc2]amix=inputs=2:normalize=0[mx];\
 [mx]alimiter=limit=0.97[aout]" -map "[aout]" -ar 44100 -ac 2 mix.wav

"$FF" -y -hide_banner -loglevel error -i jahiz-ad-silent.mp4 -i mix.wav \
  -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"

# نسخة بالموسيقى وحدها
"$FF" -y -hide_banner -loglevel error -i jahiz-ad-silent.mp4 -i jahiz-ad.wav \
  -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart jahiz-ad-music-only.mp4

echo "تم: $OUT (صوت + موسيقى) و jahiz-ad-music-only.mp4"
