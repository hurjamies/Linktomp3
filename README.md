# Linktomp3

Muuntaa YouTube-linkit ladattaviksi **mp3-tiedostoiksi**. Mukana on sekä selainkäyttöliittymä
että komentoriviversio.

- Paras saatavilla oleva ääniraita muunnetaan mp3:ksi (128, 192, 256 tai 320 kbps)
- Tiedosto nimetään videon otsikon mukaan, ja otsikko ja muut tiedot tallennetaan mp3:n metatietoihin
- Soittolistalinkeistä ladataan vain kyseinen video
- Komentorivillä voi muuntaa monta linkkiä kerralla tai lukea linkit tekstitiedostosta

> Lataa vain sisältöä, johon sinulla on oikeus (esim. oma materiaali tai vapaasti
> lisensoitu sisältö). YouTuben käyttöehdot ja tekijänoikeudet koskevat myös latauksia.

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
