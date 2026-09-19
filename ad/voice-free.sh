#!/usr/bin/env bash
# تعليق صوتي مجاني بالكامل، دون أي خدمة مدفوعة: espeak-ng يعمل داخل جهازك.
# التشكيل مقصود — بدونه ينطق المركّب الحروف على غير وجهها.
#   sudo apt-get install -y espeak-ng   ثم   ./voice-free.sh
set -euo pipefail
cd "$(dirname "$0")"
FF="${FFMPEG:-ffmpeg}"
mkdir -p vo-free

# يلائم طول الجملة نافذتها في الفيديو بتسريع لطيف عند اللزوم
fit () {  # fit <اسم> <أقصى ثوانٍ>
  d=$(python3 -c "import wave;w=wave.open('vo-free/$1.wav');print(w.getnframes()/w.getframerate())")
  f=$(python3 -c "print('%.4f' % max(1.0, $d/$2))")
  if [ "$(python3 -c "print(1 if $f > 1.01 else 0)")" = "1" ]; then
    "$FF" -y -hide_banner -loglevel error -i "vo-free/$1.wav" -af "atempo=$f" -ar 44100 -ac 1 "vo-free/$1.fit.wav"
    mv "vo-free/$1.fit.wav" "vo-free/$1.wav"
    echo "  $1: سُرّع ×$f ليناسب $2 ث"
  fi
}

say () {  # say <اسم> <نص>
  espeak-ng -v ar -s 172 -p 35 -a 175 -w "vo-free/$1.raw.wav" "$2"
  "$FF" -y -hide_banner -loglevel error -i "vo-free/$1.raw.wav" \
    -af "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,areverse,highpass=f=90,lowpass=f=7500,acompressor=threshold=-18dB:ratio=3:attack=8:release=180" \
    -ar 44100 -ac 1 "vo-free/$1.wav"
  rm -f "vo-free/$1.raw.wav"
}

say a "يَوْمَانِ عَلَى اخْتِبَارِكَ، وَتِسْعَةُ فُصُولٍ."
say b "الْأَهَمُّ لَيْسَ تَرْتِيبَ الْفُصُولِ، بَلْ وَزْنُ الْمَوْضُوعِ فِي الِاخْتِبَارِ، وَضَعْفُكَ فِيهِ."
say c "وَيَقُولُ مَا لَا يَقُولُهُ غَيْرُهُ: هَذِهِ الْمَوَاضِيعُ، لَا تَفْتَحْهَا."
say d "خُطَّةٌ بِالدَّقِيقَةِ، وَمُؤَقِّتٌ لِكُلِّ جَلْسَةٍ."
say e "جَاهِزٌ. مَجَّانِيٌّ، وَمِنَ الْمُتَصَفِّحِ مُبَاشَرَةً."

# النوافذ مأخوذة من مواضع اللقطات في ad.html
fit a 3.30
fit b 6.30
fit c 5.00
fit d 3.00
fit e 3.60
echo "تم توليد الجمل في vo-free/"
