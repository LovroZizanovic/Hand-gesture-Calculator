# Hand Gesture Calculator
Projekt iz kolegija:Robotski vid 

Kalkulator koji se upravlja gestama ruku u stvarnom vremenu, izrađen u Pythonu koristeći OpenCV i MediaPipe. Koristi webcam i geste ruku za unos brojeva i matematičkih operacija — bez tipkovnice.

---

## Načini igre

### Lagano — Slobodni unos
- Nema tajmera ni ciljnog broja
- Slobodno gradi izraze gestama
- Idealno za učenje kontrola

### Srednje — 2 broja, 1 operacija, 25 sekundi
- Na ekranu se prikazuje ciljni broj koji trebaš dosegnuti
- Unos: `Broj → Operacija → Broj`
- Svaki točan odgovor donosi bod i pokreće novu rundu
- Pogriješiš ili istekne vrijeme — igra završava

### Teško — 3 broja, 2 operacije, 20 sekundi
- Teži ciljni broj, manje vremena
- Unos: `Broj → Operacija → Broj → Operacija → Broj`
- Izraz se izračunava slijeva nadesno

---

## Geste i kontrole

| Gesta | Unos |
|---|---|
| ✊ Zatvorena šaka | `+` (zbrajanje) |
| ✌️ V-znak (kažiprst + srednji prst) | `-` (oduzimanje) |
| 👍 Palac gore | `*` (množenje) |
| 🤙 Palac + mali prst | `/` (dijeljenje) |
| ☝️ 0–5 prstiju ispruženo | Broj (0–5) |

Svaki unos potrebno je držati mirno **1,5 sekunde** da bi se potvrdio. Traka napretka na dnu ekrana prikazuje koliko je još ostalo.

---

## Pokretanje

### Preduvjeti

- Python 3.10+
- Webcam

### Instalacija

**Opcija 1 – Lokalno pokretanje**

```bash
git clone https://github.com/YOUR_USERNAME/hand-gesture-calculator.git
cd hand-gesture-calculator

pip install -r requirements.txt

python main.py
```

**Opcija 2 – Docker (Linux s X11)**

```bash
xhost +local:docker
docker compose up --build
```

> Docker postavke koriste X11 prosljeđivanje za GUI i montiraju `/dev/video0`. Ako je tvoj webcam na drugom uređaju, prilagodi `docker-compose.yml`.

---

## Struktura projekta

```
hand-gesture-calculator/
├── main.py            # Ulazna točka — provjera paketa, pokretanje GUI-a
├── gui.py             # Tkinter sučelje: odabir težine i glavni prikaz igre
├── calculator.py      # Logika igre, state machine, bodovanje, izgradnja izraza
├── hand_detector.py   # Detekcija ruke, brojanje prstiju, prepoznavanje gesti
├── overlay.py         # OpenCV pomoćne funkcije za crtanje (panel, tajmer, game over)
├── challenge.py       # Generiranje ciljnih brojeva za Srednje i Teško
├── requirements.txt   # Python paketi
├── Dockerfile
└── docker-compose.yml
```

---

## Tehnologije

- **OpenCV** — snimanje webcama i renderiranje okvira
- **MediaPipe** — detekcija 21 ključne točke na ruci
- **Tkinter** — desktop GUI i odabir težine
- **Pillow** — renderiranje emojija na okvire
- **NumPy** — manipulacija okvirima

---

## Kako radi

1. Aplikacija otvara Tkinter prozor gdje odabireš težinu.
2. Slika s webcama prikazuje se u stvarnom vremenu s označenim točkama ruke.
3. MediaPipe detektira koliko je prstiju ispruženo (brojevi 0–5) i prepoznaje oblike ruke za matematičke operacije.
4. Svaki unos mora biti miran 1,5 sekunde da bi se registrirao — tako se sprječavaju slučajni unosi.
5. Nakon što je cijeli izraz unesen, program ga izračunava i uspoređuje s ciljnim brojem. Točan odgovor donosi bod i pokreće novu rundu, a netočan završava igru.

---

## Poznata ograničenja

- Brojevi su ograničeni na **0–5** (jednom rukom, prema broju prstiju)
- Dijeljenje radi samo kada je rezultat cijeli broj
- Potrebno je dobro osvjetljenje za pouzdanu detekciju ruke
- Docker prosljeđivanje webcama podržano je samo na Linuxu
