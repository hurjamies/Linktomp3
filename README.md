# Linktomp3

Muuntaa YouTube-linkit ladattaviksi **mp3-tiedostoiksi**. Mukana on sekä selainkäyttöliittymä
että komentoriviversio.

- Paras saatavilla oleva ääniraita muunnetaan mp3:ksi (128, 192, 256 tai 320 kbps)
- Tiedosto nimetään videon otsikon mukaan, ja otsikko ja muut tiedot tallennetaan mp3:n metatietoihin
- Soittolistalinkeistä ladataan vain kyseinen video
- Komentorivillä voi muuntaa monta linkkiä kerralla tai lukea linkit tekstitiedostosta

> Lataa vain sisältöä, johon sinulla on oikeus (esim. oma materiaali tai vapaasti
> lisensoitu sisältö). YouTuben käyttöehdot ja tekijänoikeudet koskevat myös latauksia.

## Windows-sovellus (työpöydän kuvake)

Kloonaa repo ja aja kerran:

```powershell
powershell -ExecutionPolicy Bypass -File windows\install.ps1
```

Skripti asentaa tarvittaessa ffmpegin, luo virtuaaliympäristön ja tekee **Linktomp3**-pikakuvakkeen
työpöydälle ja Käynnistä-valikkoon. Kuvake avaa ohjelman omaan ikkunaansa (Edge/Chrome-sovellustila);
valmiit mp3:t tallentuvat **Lataukset**-kansioon. Kun ikkunan sulkee, ohjelma sammuu kokonaan.
Loki: `%LOCALAPPDATA%\Linktomp3\linktomp3.log`.

## Android-puhelin (Termux)

Ohjelma toimii kokonaan puhelimessa, tietokonetta ei tarvita.

### Asennus (kerran)

1. Asenna **Termux** F-Droidista: <https://f-droid.org/packages/com.termux/>
   (Play Kaupan Termux on vanhentunut, älä käytä sitä.)
   Valinnaisesti samasta paikasta myös **Termux:API** (ilmoitukset) ja **Termux:Widget** (kotinäytön pikakuvake).
2. Avaa Termux ja kirjoita (tai liitä) tämä rivi:

   ```bash
   pkg install -y git && git clone https://github.com/hurjamies/Linktomp3 && bash Linktomp3/android/install.sh
   ```

   Hyväksy tallennuslupa, kun puhelin kysyy sitä. Asennus kestää muutaman minuutin.
   Jos repositorio on yksityinen, git kysyy GitHub-käyttäjätunnusta ja salasanaksi
   [henkilökohtaista tunnusta (token)](https://github.com/settings/tokens).

### Käyttö

**Tapa 1: jakaminen (helpoin).** Avaa video YouTube-sovelluksessa, valitse **Jaa** ja sitten **Termux**.
mp3 tallentuu kansioon **Music/Linktomp3**, josta musiikkisovellukset löytävät sen.

**Tapa 2: oma sovellus kotinäytöllä.** Kirjoita Termuxissa `linktomp3-web`, jolloin Chrome avautuu.
Valitse Chromen valikosta **Asenna sovellus** (tai **Lisää aloitusnäytölle**). Sen jälkeen:

- Linktomp3 avautuu omana sovelluksenaan kotinäytöltä.
- Linktomp3 näkyy YouTuben jakovalikossa, ja jaettu linkki muunnetaan heti.
- Valmis mp3 tallentuu **Lataukset**-kansioon.

Palvelimen on oltava käynnissä Termuxissa (`linktomp3-web` tai Termux:Widgetin pikakuvake **Linktomp3**).
Jos se ei ole käynnissä, sovellus näyttää ohjeen sen käynnistämiseen.

**Asetukset:** tallennuskansion ja laadun voi vaihtaa tiedostossa `~/.config/linktomp3.conf`.

**Päivitys:** `bash ~/Linktomp3/android/install.sh` (päivittää myös yt-dlp:n).

**Jos muunnos keskeytyy näytön sammuessa,** poista Termuxilta akunsäästö
(Asetukset → Sovellukset → Termux → Akku → Ei rajoituksia).

> Vaihtoehto: voit ajaa ohjelmaa myös tietokoneella (`HOST=0.0.0.0 python -m linktomp3.web`) ja avata
> puhelimen selaimessa `http://<tietokoneen-IP>:5000`. Asennus kotinäytölle ja jakovalikko vaativat
> kuitenkin https:n tai localhostin, joten Termux-tapa on suositeltavin.

## Vaatimukset

- Python 3.9 tai uudempi
- [ffmpeg](https://ffmpeg.org/) asennettuna ja PATHissa
  - Windows: `winget install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Linux (Debian/Ubuntu): `sudo apt install ffmpeg`

## Asennus

```bash
git clone https://github.com/hurjamies/Linktomp3.git
cd Linktomp3
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Käyttö: selain

```bash
python -m linktomp3.web
```

Avaa selaimessa <http://127.0.0.1:5000>, liitä linkki ja paina **Muunna**. Kun muunnos on valmis,
mp3-tiedoston lataus alkaa automaattisesti.

Asetukset ympäristömuuttujilla:

| Muuttuja | Oletus | Merkitys |
|---|---|---|
| `HOST` | `127.0.0.1` | Kuunneltava osoite (`0.0.0.0` = näkyy lähiverkkoon) |
| `PORT` | `5000` | Portti |
| `LINKTOMP3_MAX_DURATION` | `10800` | Videon enimmäispituus sekunteina |
| `LINKTOMP3_JOB_TTL` | `1800` | Kuinka monta sekuntia valmiit tiedostot säilytetään palvelimella |
| `LINKTOMP3_WORKERS` | `3` | Montako muunnosta voi olla käynnissä samanaikaisesti |

## Käyttö: komentorivi

```bash
# yksi linkki, tallennus kansioon ./mp3
python -m linktomp3 "https://www.youtube.com/watch?v=XXXXXXXXXXX"

# useita linkkejä, 320 kbps, oma kansio
python -m linktomp3 LINKKI1 LINKKI2 -b 320 -o Musiikki

# linkit tiedostosta (yksi per rivi, #-alkuiset rivit ohitetaan)
python -m linktomp3 -f linkit.txt

# ilman argumentteja ohjelma kysyy linkin
python -m linktomp3
```

Kun asennat paketin komennolla `pip install .`, saat käyttöön myös komennot `linktomp3`
ja `linktomp3-web`.

## Vianetsintä

- **"ffmpeg puuttuu"** – asenna ffmpeg (ks. Vaatimukset) ja avaa pääte uudelleen.
- **Lataus epäonnistuu, vaikka linkki on oikein** – YouTube muuttaa sivustoaan usein. Päivitä
  yt-dlp: `pip install -U yt-dlp`.

## Testit

```bash
pip install pytest
python -m pytest
```
