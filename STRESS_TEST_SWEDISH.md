# Stresstestning av Nordic Secure - Svensk Sammanfattning

## Sammanfattning

Jag har implementerat omfattande stresstestning för din Nordic Secure Live-app med 50 PDF-filer och detaljerad statistik för alla steg.

## Vad har implementerats

### 1. Förbättrat Backend Stresstest (`backend/test_pdf_stress.py`)

**Konfigurerat för 50 PDFer** (ändrat från 20)

**Omfattande statistik:**
- ⏱️ Tidsmätning: genomsnitt, median, p50, p90, p95, p99
- 💾 Minnesanalys: initial, final, delta, peak, genomsnitt
- 📊 Prestanda: genomströmning, framgångsgrad
- 🔍 Minnesläckagedetektion med linjär regression
- ⏳ Realtidsförlopp med ETA-beräkning
- 📄 Automatisk rapportgenerering

### 2. Live App Stresstest (`stress_test_live.py`)

**Testar hela stacken via API:**
- Fullständigt uppladdningsarbetsflöde via `/ingest` endpoint
- API-svarstidsmätning
- Backend health check
- Fel- och undantagshantering
- Detaljerad rapportgenerering

### 3. Snabbstartsscript (`run_stress_test.py`)

**Automatisk setup:**
- Kontrollerar och installerar beroenden automatiskt
- Verifierar att backend körs
- Färgkodad utskrift
- Kommandoradsalternativ

### 4. Demonstrationsscript (`demo_stress_test.py`)

**Visar funktionalitet utan beroenden:**
- Demonstrerar utskriftsformat
- Ingen installation krävs
- Visar alla statistiktyper

## Hur man kör testerna

### Alternativ 1: Snabbstart (Rekommenderat)

```bash
# Terminal 1: Starta backend
python backend/main.py

# Terminal 2: Kör stresstest
python run_stress_test.py
```

### Alternativ 2: Individuella tester

**Backend test (ingen API krävs):**
```bash
python backend/test_pdf_stress.py
```

**Live app test (backend måste köra):**
```bash
# Starta backend först
python backend/main.py

# Kör test
python stress_test_live.py
```

### Alternativ 3: Demo (inga beroenden)

```bash
python demo_stress_test.py
```

## Anpassning

### Ändra antal PDFer

**Via miljövariabel:**
```bash
export STRESS_TEST_NUM_PDFS=100
python stress_test_live.py
```

**Via kommandoradsalternativ:**
```bash
python run_stress_test.py --pdfs 100
```

### Miljövariabler

| Variabel | Beskrivning | Standard |
|----------|-------------|----------|
| `STRESS_TEST_NUM_PDFS` | Antal PDFer att testa | `50` |
| `STRESS_TEST_ITERATIONS` | Antal iterationer | `1` |
| `BACKEND_URL` | Backend API URL | `http://localhost:8000` |

## Statistik som tillhandahålls

### 📊 Övergripande mått
- Total körtid (sekunder och minuter)
- Antal filer bearbetade (lyckade/misslyckade)
- Framgångsgrad i procent
- Genomströmning (filer/sekund)

### ⏱️ Exekveringsstatistik
- Genomsnitt, Median (p50)
- Min/Max tid
- p90, p95, p99 percentiler
- Total bearbetningstid

### 💾 Minnesanalys
- Initial/slutlig minnesanvändning
- Minnesdelta och tillväxtprocent
- Peak/minimum/genomsnitt minne
- Minne per fil
- Minnesläckagedetektion

### 📈 Realtidsförlopp
- Framstegsprocent
- Aktuell filstatus
- Minnesuppdateringar var 5:e fil
- Beräknad återstående tid (ETA)

## Exempelutskrift

```
======================================================================
LIVE APP STRESS TEST - FULL STACK PERFORMANCE ANALYSIS
======================================================================

Configuration:
  - Number of PDFs: 50
  - Backend URL: http://localhost:8000

✓ Backend is healthy and ready
✓ Generated 50 PDFs (Total: 245.32 KB)

======================================================================
STARTING LIVE APP STRESS TEST
======================================================================

  [ 10.0%] File 5/50: ✓ 2.145s | Success: 100.0% | Memory: 545.23 MB (Δ +21.78) | ETA: 4.5m
  [ 20.0%] File 10/50: ✓ 2.089s | Success: 100.0% | Memory: 556.12 MB (Δ +32.67) | ETA: 3.8m
  ...

======================================================================
LIVE APP STRESS TEST RESULTS
======================================================================

📊 Overall Metrics:
  ├─ Total runtime: 125.67 seconds (2.09 minutes)
  ├─ Files processed: 50
  ├─ Successful uploads: 49 (98.0%)
  ├─ Failed uploads: 1
  └─ Throughput: 0.40 files/second

⏱️  Upload Time Statistics:
  ├─ Average: 2.513 seconds
  ├─ Median (p50): 2.456 seconds
  ├─ Min: 1.234 seconds
  ├─ Max: 4.567 seconds
  ├─ p90: 3.234 seconds
  └─ p95: 3.678 seconds

💾 Memory Analysis:
  ├─ Initial: 523.45 MB
  ├─ Final: 548.23 MB
  ├─ Delta: +24.78 MB
  ├─ Peak: 556.89 MB
  └─ Average: 537.45 MB

📋 SUMMARY
✓ Processed 50 files in 125.67 seconds
✓ Success rate: 98.0% (49/50)
✓ Average time: 2.513 seconds
✓ Throughput: 0.40 files/second
✓ Memory usage stable: +24.78 MB
```

## Rapportfiler

Båda testerna genererar detaljerade rapportfiler:
- `stress_test_report_YYYYMMDD_HHMMSS.txt` - Backend test
- `live_stress_test_report_YYYYMMDD_HHMMSS.txt` - Live app test

**Rapportinnehåll:**
- Testkonfiguration och tidsstämpel
- Övergripande prestandasammanfattning
- Detaljerad tidmätning för varje fil
- Minnesanvändning över tid
- Komplett fellogg
- Statistisk analys

## Förväntad prestanda

**Med GPU:**
- Genomströmning: 0.4-0.6 filer/sekund
- Genomsnittlig tid: 1-2 sekunder per fil

**Utan GPU:**
- Genomströmning: 0.1-0.2 filer/sekund
- Genomsnittlig tid: 5-10 sekunder per fil

**Minne:**
- Förväntat: < 50 MB tillväxt för 50 filer
- Varning: > 100 MB tillväxt
- Kritiskt: > 200 MB eller linjär tillväxt

## Felsökning

| Problem | Lösning |
|---------|---------|
| Backend körs inte | Starta med `python backend/main.py` |
| Saknade beroenden | Kör `python run_stress_test.py` (auto-installerar) |
| Timeout-fel | Kontrollera att Ollama körs |
| Hög minnesanvändning | Starta om backend mellan tester |
| Låg genomströmning | Kontrollera CPU/GPU-användning |

## Dokumentation

**Fullständiga guider:**
- `STRESS_TEST_GUIDE.md` - Komplett guide på engelska
- `STRESS_TEST_SUMMARY.md` - Teknisk implementationssammanfattning
- `STRESS_TEST_SWEDISH.md` - Denna svenska sammanfattning

## Filer som skapats/modifierats

### Modifierade:
- `backend/test_pdf_stress.py` - Förbättrad med 50 PDFer och omfattande statistik

### Skapade:
- `stress_test_live.py` - Nytt fullstack API-stresstest
- `run_stress_test.py` - Snabbstartsscript med auto-setup
- `demo_stress_test.py` - Demonstrationsscript
- `STRESS_TEST_GUIDE.md` - Omfattande dokumentation
- `STRESS_TEST_SUMMARY.md` - Implementationssammanfattning
- `STRESS_TEST_SWEDISH.md` - Svensk sammanfattning

## Tekniska detaljer

**Beroenden som krävs:**
- `psutil` - Minnesövervakning
- `reportlab` - PDF-generering
- `PyPDF2` - PDF-manipulering
- `requests` - HTTP API-anrop

Alla installeras automatiskt av `run_stress_test.py`.

**Kompatibilitet:**
- Python 3.10+
- Windows, macOS, Linux
- Fungerar med befintlig Nordic Secure-installation
- Inga ändringar i produktionskod krävs

## Sammanfattning

✅ **Klart!** Du kan nu stresstesta din Live-app med 50 PDF-filer och få detaljerad statistik på alla steg.

### Vad ingår:
- ✅ 50 PDF-stresstestning
- ✅ Omfattande statistik (prestanda, tidmätning, minne)
- ✅ Realtidsförlopp med ETA
- ✅ Fullstack API-testning
- ✅ Automatisk rapportgenerering
- ✅ Enkel setup och körning
- ✅ Komplett dokumentation
- ✅ Konfigurering via miljövariabler

### Snabbstart:
```bash
# Kör demo först (inga beroenden)
python demo_stress_test.py

# Sedan kör riktigt test
python run_stress_test.py
```

**Klart att använda omedelbart!** 🎉

## Support

För frågor eller problem:
- Läs `STRESS_TEST_GUIDE.md` för detaljerad information
- Kontrollera felmeddelanden i rapportfilerna
- Verifiera att alla beroenden är installerade
- Kontrollera att backend körs på rätt port
