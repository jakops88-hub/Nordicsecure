# 🚀 Stresstest av Nordic Secure Live App - 50 PDF-filer

## Snabbstart

```bash
# 1. Kör demo (inga beroenden)
python demo_stress_test.py

# 2. Kör riktigt test
python run_stress_test.py
```

Det är allt! 🎉

## Vad får du?

### 📊 Omfattande statistik för alla steg:

- **Prestanda**: körtid, genomströmning, framgångsgrad
- **Tidmätning**: genomsnitt, median, p50, p90, p95, p99
- **Minne**: initial, final, delta, peak, genomsnitt
- **Realtidsövervakning**: förlopp med ETA
- **Felspårning**: detaljerad analys av misslyckanden

### Exempel på utskrift:

```
  [ 10.0%] File 5/50: ✓ 2.14s | Success: 100.0% | Memory: 545 MB (Δ +22) | ETA: 4.5m
  [ 20.0%] File 10/50: ✓ 2.09s | Success: 100.0% | Memory: 556 MB (Δ +33) | ETA: 3.8m

📊 Overall Metrics:
  ├─ Total runtime: 125.67 seconds (2.09 minutes)
  ├─ Files processed: 50
  ├─ Successful: 49 (98.0%)
  └─ Throughput: 0.40 files/second

⏱️  Processing Time Statistics:
  ├─ Average: 2.513 seconds
  ├─ Median (p50): 2.456 seconds
  ├─ p90: 3.234 seconds
  └─ p95: 3.678 seconds

💾 Memory Analysis:
  ├─ Initial: 523.45 MB
  ├─ Final: 548.23 MB
  ├─ Delta: +24.78 MB
  └─ ✓ Memory stable - No memory leak detected
```

## Alternativ

### 1. Demo (rekommenderas första gången)

```bash
python demo_stress_test.py
```

- ✅ Visar hur testet fungerar
- ✅ Inga beroenden krävs
- ✅ Snabb demonstration

### 2. Quick Start (automatisk setup)

```bash
python run_stress_test.py
```

- ✅ Installerar beroenden automatiskt
- ✅ Kör både backend och live test
- ✅ Enklaste sättet att komma igång

### 3. Backend Test (endast PDF-bearbetning)

```bash
python backend/test_pdf_stress.py
```

- ✅ Testar PDF-bearbetning direkt
- ✅ Ingen API krävs
- ✅ Snabbare test

### 4. Live App Test (fullstack via API)

```bash
# Terminal 1: Starta backend
python backend/main.py

# Terminal 2: Kör test
python stress_test_live.py
```

- ✅ Testar hela stacken
- ✅ Via HTTP API
- ✅ Mest realistiskt test

## Anpassning

### Ändra antal PDF-filer

```bash
# 100 PDFer istället för 50
export STRESS_TEST_NUM_PDFS=100
python stress_test_live.py
```

### Ändra backend URL

```bash
export BACKEND_URL="http://192.168.1.100:8000"
python stress_test_live.py
```

### Flera iterationer

```bash
export STRESS_TEST_ITERATIONS=3  # 150 totala filer
python backend/test_pdf_stress.py
```

## Rapportfiler

Alla tester genererar detaljerade rapporter:

- `stress_test_report_YYYYMMDD_HHMMSS.txt` (backend)
- `live_stress_test_report_YYYYMMDD_HHMMSS.txt` (live app)

Innehåller:
- Komplett tidmätning för varje fil
- Minnesanvändning över tid
- Fellogg
- Statistisk analys

## Förväntat resultat

### Bra prestanda:
- ✅ Genomströmning: > 0.3 filer/sekund
- ✅ Genomsnitt: < 3 sekunder per fil
- ✅ Minnestillväxt: < 50 MB
- ✅ Framgångsgrad: > 95%

### Behöver undersökas:
- ⚠️ Genomströmning: < 0.2 filer/sekund
- ⚠️ Minnestillväxt: > 100 MB
- ⚠️ Framgångsgrad: < 90%

## Felsökning

| Problem | Lösning |
|---------|---------|
| Backend körs inte | `python backend/main.py` |
| Saknade beroenden | `python run_stress_test.py` (auto-fix) |
| Timeout | Kontrollera Ollama körs |
| Låg prestanda | Kontrollera GPU, CPU-användning |

## Dokumentation

- 📖 `STRESS_TEST_GUIDE.md` - Komplett guide (engelska)
- 📖 `STRESS_TEST_SWEDISH.md` - Fullständig svensk guide
- 📖 `STRESS_TEST_SUMMARY.md` - Teknisk sammanfattning

## Systemkrav

- Python 3.10+
- 16GB RAM (rekommenderat)
- Backend installerad
- (Valfritt) Ollama med llama3

## Support

Frågor? Kolla:
1. `demo_stress_test.py` - Se hur det fungerar
2. `STRESS_TEST_GUIDE.md` - Detaljerad guide
3. Rapportfiler - Innehåller feldetaljer

---

**Redo att använda!** Kör `python demo_stress_test.py` för att börja. 🚀
