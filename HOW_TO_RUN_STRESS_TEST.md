# How to Run the Updated Stress Test with Real Llama 3 Inference

## What Changed

The stress test has been updated per PR #15 critique to perform **REAL LLM inference** instead of just PDF parsing.

### Before (unrealistic):
- ❌ Only parsed PDFs without LLM classification
- ❌ 0.003s per file (too fast to be real)
- ❌ No model loaded into memory
- ❌ Not representative of production workload

### After (realistic):
- ✅ Loads Llama 3 model via Ollama
- ✅ Performs REAL classification inference on each file
- ✅ 5-10 seconds per file (realistic timing)
- ✅ Shows actual RAM usage with model active
- ✅ Tests complete production workflow

## Prerequisites

### 1. Install Ollama

Download and install from: https://ollama.ai/download

Or on Linux:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Start Ollama Server

```bash
ollama serve
```

Keep this running in a terminal. It should show:
```
Ollama is running
```

### 3. Pull Llama 3 Model

In another terminal:
```bash
ollama pull llama3
```

This will download the model (~4GB). Wait for it to complete.

### 4. Verify Setup

```bash
# Check Ollama is accessible
curl http://localhost:11434/api/tags

# Should show llama3 in the models list
```

### 5. Install Python Dependencies

```bash
cd /path/to/Nordicsecure
pip install -r requirements.txt
```

## Running the Test

```bash
python backend/test_pdf_stress.py
```

### Expected Output

```
======================================================================
PDF PROCESSING STRESS TEST WITH REAL LLAMA 3 INFERENCE
======================================================================

Configuration:
  - Number of PDFs: 20
  - Iterations: 1
  - Total files to process: 20
  - Ollama URL: http://localhost:11434
  - Model: llama3

Initializing DocumentService...
✓ DocumentService initialized

Initializing TriageService with llama3...
⚠️  This will connect to Ollama and load the model into memory
✓ TriageService initialized

Verifying Ollama connection...
✓ Ollama is running and accessible
✓ Model 'llama3' is available

Generating 20 dummy PDF files...
✓ Generated 20 PDFs (Total: 69.12 KB)

======================================================================
STARTING STRESS TEST WITH REAL LLAMA 3 INFERENCE
======================================================================

⚠️  Note: Each file will take 5-10 seconds due to real model inference

Initial memory usage: 1250.45 MB

Iteration 1/1
--------------------------------------------------
  File 1/20: 6.234s | Memory: 1850.23 MB (Δ +599.78 MB) | Classified: Yes
  File 2/20: 7.145s | Memory: 1852.34 MB (Δ +601.89 MB) | Classified: Yes
  ...
```

### Expected Duration

- **Total time**: ~2-3 minutes for 20 files
- **Per file**: 5-10 seconds (with real LLM inference)
- **Memory increase**: +500-800 MB (model loading)

## Verification Checklist

After running the test, verify:

- [ ] Average time per file is between 5-10 seconds
- [ ] Memory increased by ~600 MB or more
- [ ] Each file shows "Classified: Yes" or "No"
- [ ] Test confirms "Realistic timing confirmed - LLM is performing real inference"

## Troubleshooting

### Error: "Ollama is not accessible"
**Solution**: Make sure `ollama serve` is running in another terminal

### Error: "Model 'llama3' not found"
**Solution**: Run `ollama pull llama3` to download the model

### Warning: "Average time is too low!"
**Solution**: This means the LLM isn't running. Check:
1. Ollama is running: `curl http://localhost:11434/api/tags`
2. Model is available: `ollama list`

### Import Errors
**Solution**: Install dependencies: `pip install -r requirements.txt`

## What the Test Does

1. **PDF Generation**: Creates 20 dummy PDFs with invoice-like content
2. **Text Extraction**: Uses DocumentService to parse each PDF
3. **LLM Classification**: Sends text to Llama 3 for categorization (NOT MOCKED!)
4. **Memory Monitoring**: Tracks RAM usage throughout the process
5. **Performance Analysis**: Reports timing and validates realistic execution

## Results Interpretation

### ✅ Good Results
- Average time: 5-10 seconds per file
- Memory stable after initial model load
- All files classified successfully
- Message: "Realistic timing confirmed"

### ⚠️ Bad Results (Model Not Running)
- Average time: < 1 second per file
- Warning: "Average time is too low!"
- Memory doesn't increase significantly
- Indicates LLM inference is not happening

## Additional Information

For more details, see: `backend/STRESS_TEST_README.md`

## Questions?

If you encounter issues or have questions about the stress test, please open an issue on GitHub.
