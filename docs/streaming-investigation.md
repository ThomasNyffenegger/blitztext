# Live-/Streaming-Transkription – Machbarkeitsuntersuchung

**Stand:** 2026-05 · **Ergebnis:** Auf dem Entwicklungs-Laptop nicht machbar. Auf schnellerer Hardware erneut prüfen.

## Ziel

Text soll *während* des Sprechens transkribiert werden („Just-in-time"), d.h. eine Live-Vorschau im Overlay, die mitwächst – statt erst beim Loslassen des Hotkeys.

## Warum das technisch knifflig ist

Whisper ist **kein Streaming-Modell** – es verarbeitet abgeschlossene Audio-Fenster, keine fortlaufenden Ströme. Live-Transkription wird deshalb simuliert: man transkribiert den bisher aufgenommenen Puffer alle ~1s neu (Sliding Window) und zeigt das jeweils aktuelle Ergebnis. Der Text am Ende „flackert", bis genug Kontext da ist (bekannt von Live-Untertiteln).

Fertige Bibliothek dafür: [`RealtimeSTT`](https://github.com/KoljaB/RealtimeSTT) (nutzt intern faster-whisper, implementiert LocalAgreement-Stabilisierung).

## Voraussetzung: Real-Time-Factor (RTF)

RTF = Verarbeitungszeit / Audio-Dauer.

- RTF < 1 = schneller als Echtzeit
- **RTF < ~0,5** = Faustregel, ab der Streaming flüssig wird (überlappende Fenster werden mehrfach transkribiert)

## Messergebnisse (Entwicklungs-Laptop, faster-whisper int8, CPU)

Hardware: Intel Haswell-CPU (~2015), GTX 960M (für Whisper zu schwach), Python 3.14.

Der **entscheidende** Wert für Streaming ist der „5s-Fenster"-Fall: ein mittendrin
abgeschnittenes Audiofenster, wie es Streaming permanent erzeugt. Solche Schnitte
bringen den Decoder zu Halluzinations-/Wiederholungsschleifen → deutlich langsamer
als sauber endendes Audio.

| Modell | 5s-Fenster (Streaming-Fall) | Voller Clip (sauberes Ende) |
|--------|-----------------------------|------------------------------|
| `tiny`  | **RTF ~1,4–1,9** (stabil)   | RTF 0,5–1,5 (verrauscht)     |
| `base`  | RTF ~4,6–5,2                | RTF ~1,0–3,0                 |
| `small` | RTF ~3,9–4,9                | RTF ~1,6–2,3                 |

### Wichtige Beobachtungen

1. **Selbst `tiny`** (das kleinste, qualitativ schlechteste Modell) liegt im
   Streaming-Fall konstant **über** Echtzeit (RTF ~1,5–1,9). Live-Vorschau würde
   also 2–4s nachhinken *und* halluzinieren.
2. Der Fenster-RTF ist über alle Läufe **stabil** (1,36 / 1,85 / 1,90), während
   der Voll-Clip-RTF stark schwankt (0,54–1,54). Grund: die Halluzinations-Schleife
   ist taktunabhängig bounded, der saubere Kurz-Clip ist takt-/lastempfindlich.
3. **Akku vs. Netz / Energiesparmodus** war *nicht* der Hebel: am Netz waren die
   Werte nicht besser (tiny voll 1,54 am Netz vs. 0,54 im Akku) – dominiert von
   thermischem Throttling und Hintergrundlast, nicht von der Stromversorgung.

## Fazit

Echtes Wort-für-Wort-Streaming ist auf diesem Laptop **nicht machbar**. Der
Flaschenhals ist strukturell (Decoder-Verhalten bei abgeschnittenen Fenstern +
schwache CPU) und wird durch Energieeinstellungen nicht gelöst.

## Nächste Schritte auf schnellerer Hardware

1. `python benchmark_rtf.py` ausführen.
2. Wenn `tiny` im **5s-Fenster-Fall RTF < 0,5** schafft (und idealerweise `base`
   < 1,0), lohnt sich echtes Streaming.
3. Dann Umbau planen:
   - **Zwei-Modell-Ansatz:** `tiny`/`base` für die Live-Vorschau, `small` für den
     finalen Durchlauf beim Loslassen (eingefügter Text bleibt hochwertig).
   - `recorder.py`: mitlesbarer Rolling-Buffer statt nur Frame-Sammlung.
   - Neuer Streaming-Worker-Thread (alle ~1s Puffer transkribieren, mit
     LocalAgreement-Stabilisierung – oder `RealtimeSTT` als Basis).
   - `overlay.py`: vom Status-Anzeiger zum Live-Untertitel-Fenster.
   - Einfügen bleibt wie heute: final beim Loslassen (Live-Tippen in fremde Apps
     ist nicht sauber machbar).

## Alternative ohne schnellere Hardware: „Chunk-bei-Pause"

Kein Wort-für-Wort-Streaming, sondern: bei natürlichen Sprechpausen (Stille-
Erkennung) wird der bis dahin *abgeschlossene* Abschnitt transkribiert (sauberes
Ende → günstiger RTF). Der Text wächst satzweise mit etwas Versatz. Gröberes
Feedback, aber auf der vorhandenen CPU umsetzbar. Bisher nicht umgesetzt.
