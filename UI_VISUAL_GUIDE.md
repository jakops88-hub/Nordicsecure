# AI Triage UI Screenshots and Visual Guide

## Main Interface

### Tab Navigation
The application now features three tabs at the top:
```
[💬 Chat] [📤 Upload] [🗂️ Mass Sorting]
```

In Swedish:
```
[💬 Chatt] [📤 Ladda upp] [🗂️ Mass-sortering]
```

### Sidebar - Settings
```
⚙️ Settings
─────────────────────────
Language / Språk: [English ▼]

License Status
✅ Active License / 🔒 License Expired

▼ Activate License
   License Key: [**********]
   [Activate]
```

---

## Mass Sorting Tab (English View)

### Header
```
🗂️ AI Triage - Batch File Sorting
Automatically sort hundreds of unstructured files (PDF/Images) based on your criteria.
```

### Input Section (Two Column Layout)

#### Left Column
```
📁 Source Folder (Inbox)
┌─────────────────────────────────────┐
│ /path/to/inbox                      │
└─────────────────────────────────────┘
ⓘ Path to the folder containing files to sort

✅ Target Folder: Relevant
┌─────────────────────────────────────┐
│ /path/to/relevant                   │
└─────────────────────────────────────┘
ⓘ Path where relevant files will be moved
```

#### Right Column
```
❌ Target Folder: Irrelevant
┌─────────────────────────────────────┐
│ /path/to/irrelevant                 │
└─────────────────────────────────────┘
ⓘ Path where non-relevant files will be moved

Max Pages to Analyze: [  5  ▲▼]
ⓘ Limit OCR to first N pages to save time (recommended: 3-5)
```

### Criteria Section
```
📋 Sorting Criteria
┌─────────────────────────────────────────────────────────┐
│ E.g., Is this document related to a bankruptcy          │
│ application or promissory note?                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
ⓘ Describe what makes a document relevant

              [🚀 Start Sorting]
```

---

## Processing View (During Execution)

### Progress Indicator
```
Processing files...
████████████████░░░░░░░░░░░░ 60%

▼ 📋 Live Execution Log
┌─────────────────────────────────────────────────────────┐
│ ⏳ Processing file: invoice_2023_001.pdf                │
│ ✅ Moved to: Relevant - Reason: Contains bankruptcy ref │
│ ⏳ Processing file: contract_2024_045.pdf               │
│ ❌ Moved to: Irrelevant - Reason: General contract      │
│ ⏳ Processing file: receipt_2024_089.pdf                │
│ ⚠️  Skipped due to error: Cannot extract text           │
│ ...                                                     │
└─────────────────────────────────────────────────────────┘
```

---

## Results View (After Completion)

### Statistics
```
✅ Sorting Complete!

┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Total Files │  Relevant   │ Irrelevant  │   Errors    │
│     100     │      45     │      52     │      3      │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

### Audit Log Table
```
📊 Audit Log
┌──────────────────────┬─────────────────────┬──────────┬────────────────────────────┬────────────┐
│ Filename             │ Date                │ Decision │ AI Reasoning               │ Moved To   │
├──────────────────────┼─────────────────────┼──────────┼────────────────────────────┼────────────┤
│ invoice_001.pdf      │ 2025-12-22 07:15:22 │ relevant │ Contains bankruptcy ref... │ relevant   │
│ contract_045.pdf     │ 2025-12-22 07:15:25 │ irrele.. │ General contract, no ban...│ irrelevant │
│ receipt_089.pdf      │ 2025-12-22 07:15:28 │ error    │ Cannot extract text        │ N/A        │
│ statement_092.pdf    │ 2025-12-22 07:15:31 │ relevant │ Mentions promissory note...│ relevant   │
│ ...                  │ ...                 │ ...      │ ...                        │ ...        │
└──────────────────────┴─────────────────────┴──────────┴────────────────────────────┴────────────┘

[⬇️ Download Audit Log (CSV)]
```

---

## Mass Sorting Tab (Swedish View)

### Header
```
🗂️ AI Triage - Batch-sortering
Sortera automatiskt hundratals ostrukturerade filer (PDF/Bilder) baserat på dina kriterier.
```

### Input Section
```
📁 Källmapp (Inkorg)
┌─────────────────────────────────────┐
│ /path/to/inbox                      │
└─────────────────────────────────────┘
ⓘ Sökväg till mappen som innehåller filer att sortera

✅ Målmapp: Träff
┌─────────────────────────────────────┐
│ /path/to/relevant                   │
└─────────────────────────────────────┘
ⓘ Sökväg dit relevanta filer kommer att flyttas

❌ Målmapp: Övrigt
┌─────────────────────────────────────┐
│ /path/to/irrelevant                 │
└─────────────────────────────────────┘
ⓘ Sökväg dit icke-relevanta filer kommer att flyttas

Max Sidor att Analysera: [  5  ▲▼]
ⓘ Begränsa OCR till första N sidorna för att spara tid (rekommenderat: 3-5)

📋 Sorteringskriterier
┌─────────────────────────────────────────────────────────┐
│ T.ex. Är detta dokument relaterat till en              │
│ konkursansökan eller skuldebrev?                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
ⓘ Beskriv vad som gör ett dokument relevant

              [🚀 Starta Sortering]
```

### Results (Swedish)
```
✅ Sortering Klar!

┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Totalt Filer│  Relevanta  │ Irrelevanta │     Fel     │
│     100     │      45     │      52     │      3      │
└─────────────┴─────────────┴─────────────┴─────────────┘

📊 Revisionslogg
[Table with Swedish headers: Filnamn, Datum, Beslut (Ja/Nej), AI Motivering, Flyttad Till]

[⬇️ Ladda ner Revisionslogg (CSV)]
```

---

## Error Messages

### English
- "Please provide all folder paths."
- "Please provide sorting criteria."
- "Source folder does not exist"
- "Error: [specific error message]"

### Swedish
- "Vänligen ange alla mappsökvägar."
- "Vänligen ange sorteringskriterier."
- "Källmappen finns inte"
- "Fel: [specifikt felmeddelande]"

---

## Key UI Features

1. **Responsive Layout**: Uses Streamlit's column system for optimal space usage
2. **Help Text**: All inputs have helpful tooltips (ⓘ icon)
3. **Progress Indicators**: Real-time progress bar during processing
4. **Live Log**: Expandable section showing file-by-file progress
5. **Statistics Cards**: Visual metrics display using Streamlit metrics
6. **Data Table**: Interactive pandas DataFrame display with sorting/filtering
7. **Download Button**: One-click CSV export of audit log
8. **Language Switching**: Instant UI language change without page reload
9. **Icons**: Emoji-based icons for visual clarity
10. **Color Coding**: 
    - ✅ Green for relevant/success
    - ❌ Red for irrelevant/errors
    - ⏳ Yellow/loading for processing
    - ⚠️ Warning for errors

---

## Accessibility Features

- Clear visual hierarchy
- Sufficient color contrast
- Descriptive labels
- Help text for all inputs
- Error messages are clear and actionable
- Progress feedback for long operations
- Multi-language support

---

## Responsive Design

The UI adapts to different screen sizes:
- **Desktop**: Two-column layout for inputs
- **Tablet**: Single column with all inputs stacked
- **Mobile**: Optimized for touch with larger buttons

---

## User Flow

1. **Setup**
   - Select language preference
   - Navigate to Mass Sorting tab

2. **Configuration**
   - Enter source folder path
   - Enter target folder paths
   - Write sorting criteria
   - Adjust max pages if needed

3. **Execution**
   - Click "Start Sorting"
   - Monitor progress bar
   - Watch live log for real-time updates

4. **Review**
   - Check statistics
   - Review audit log table
   - Download CSV for records

5. **Compliance**
   - Keep audit log for regulatory requirements
   - Share with auditors/reviewers
   - Use for process improvement
