#!/data/data/com.termux/files/usr/bin/bash
# Linktomp3 – asennus Androidille (Termux).
#
# Aja Termuxissa repositorion kansiossa:
#     bash android/install.sh
#
# Asentaa Pythonin, ffmpegin ja Linktomp3:n sekä:
#   * jakotoiminnon: YouTube-sovellus -> Jaa -> Termux  => mp3 tallentuu Music/Linktomp3-kansioon
#   * komennon `linktomp3-web`, joka käynnistää selainkäyttöliittymän puhelimessa
#   * komennon `linktomp3`, jolla voi muuntaa linkkejä suoraan Termuxissa
# Skriptin voi ajaa uudelleen päivittääkseen ohjelman.
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="$HOME/bin"
CONF="$HOME/.config/linktomp3.conf"

say()  { printf '\n\033[1;31m==>\033[0m \033[1m%s\033[0m\n' "$*"; }
fail() { printf '\n\033[1;31mVIRHE:\033[0m %s\n' "$*" >&2; exit 1; }

if [ ! -d /data/data/com.termux/files ]; then
  fail "Tämä skripti on tarkoitettu Android-puhelimen Termux-sovellukseen."
fi

say "Päivitetään pakettilistat ja asennetaan Python ja ffmpeg (voi kestää muutaman minuutin)"
yes | pkg update -y || true
pkg install -y python python-pip ffmpeg git nodejs-lts

if [ -d "$APP_DIR/.git" ]; then
  say "Haetaan uusin versio"
  git -C "$APP_DIR" pull --ff-only || echo "(Päivitys ohitettiin – jatketaan nykyisellä versiolla.)"
fi

say "Asennetaan Linktomp3 ja yt-dlp"
# Termuxissa pipiä itseään ei saa päivittää, joten päivitetään vain paketit.
pip install --upgrade --disable-pip-version-check yt-dlp yt-dlp-ejs flask
pip install --upgrade --disable-pip-version-check --no-deps "$APP_DIR"

say "Annetaan Termuxille lupa tallentaa puhelimen muistiin"
if [ ! -d "$HOME/storage/shared" ]; then
  echo "Hyväksy puhelimen kysymä tallennuslupa."
  termux-setup-storage || true
  for _ in $(seq 1 60); do
    [ -d "$HOME/storage/shared" ] && break
    sleep 1
  done
fi
[ -d "$HOME/storage/shared" ] || fail "Tallennuslupaa ei saatu. Aja 'termux-setup-storage' ja sitten tämä skripti uudelleen."

mkdir -p "$BIN" "$HOME/.config" "$HOME/.shortcuts"
if [ ! -f "$CONF" ]; then
  cat > "$CONF" <<'EOF'
# Linktomp3-asetukset (muokkaa tarvittaessa)
# Kansio, johon jaetut kappaleet tallennetaan:
LINKTOMP3_DIR="$HOME/storage/shared/Music/Linktomp3"
# mp3:n laatu kbps: 128, 192, 256 tai 320
LINKTOMP3_BITRATE=192
EOF
fi

say "Otetaan käyttöön jakotoiminto (Jaa -> Termux)"
if [ -f "$BIN/termux-url-opener" ] && ! grep -q "Linktomp3" "$BIN/termux-url-opener"; then
  cp "$BIN/termux-url-opener" "$BIN/termux-url-opener.bak"
  echo "Aiempi termux-url-opener tallennettiin nimellä termux-url-opener.bak"
fi
install -m 755 "$APP_DIR/android/termux-url-opener" "$BIN/termux-url-opener"

cat > "$BIN/linktomp3-web" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# Linktomp3: käynnistää selainkäyttöliittymän osoitteeseen http://127.0.0.1:5000
PORT="${PORT:-5000}"
command -v termux-wake-lock >/dev/null && termux-wake-lock
trap 'command -v termux-wake-unlock >/dev/null && termux-wake-unlock' EXIT
( sleep 2; termux-open-url "http://127.0.0.1:$PORT/" ) &
echo "Linktomp3 käynnissä. Pysäytä painamalla Ctrl+C (tai sulje Termux-ilmoituksesta 'Exit')."
HOST=127.0.0.1 PORT="$PORT" python -m linktomp3.web
EOF
chmod 755 "$BIN/linktomp3-web"

# Pikakuvake Termux:Widget-sovellukselle (valinnainen)
cp "$BIN/linktomp3-web" "$HOME/.shortcuts/Linktomp3"
chmod 755 "$HOME/.shortcuts/Linktomp3"

say "Tarkistetaan asennus"
python -c "import linktomp3, yt_dlp; print('Linktomp3', linktomp3.__version__, '/ yt-dlp', yt_dlp.version.__version__)"
ffmpeg -version | head -1

. "$CONF"
cat <<EOF

$(printf '\033[1;32m')Valmis!$(printf '\033[0m')

1) JAKAMINEN (helpoin tapa)
   Avaa video YouTube-sovelluksessa -> Jaa -> Termux.
   mp3 tallentuu kansioon: ${LINKTOMP3_DIR#$HOME/storage/shared/}

2) SELAINSOVELLUS
   Kirjoita Termuxissa:  linktomp3-web
   Chrome avautuu. Valitse Chromen valikosta "Asenna sovellus" / "Lisää aloitusnäytölle",
   niin Linktomp3 näkyy omana sovelluksenaan ja jakovalikossa.

3) KOMENTORIVI
   linktomp3 "https://youtu.be/..." -o ~/storage/shared/Music

Päivitys myöhemmin:  bash $APP_DIR/android/install.sh
EOF
