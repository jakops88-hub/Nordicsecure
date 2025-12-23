# PDF Processing Stress Test with Real Llama 3 Inference

## Overview

This stress test evaluates the performance and memory usage of the NordicSecure PDF processing engine **with REAL Llama 3 model inference**. It performs PDF text extraction AND LLM-based categorization while monitoring memory consumption and execution time.

⚠️ **IMPORTANT**: This test now performs ACTUAL model inference using Ollama and Llama 3. The previous version only did PDF parsing without LLM calls.

## Purpose

As a Performance Engineer, this test helps you:
- **Measure Real-World Performance**: Tests the complete workflow including LLM inference
- **Monitor RAM Usage**: Tracks memory consumption with the model loaded and active
- **Validate Timing**: Ensures realistic execution times (5-10 seconds per file with LLM)
- **Assess Scalability**: Evaluates performance with 20 files processed sequentially

## Features

✅ Generates 20 dummy PDF files with realistic invoice content  
✅ **Loads and uses the actual Llama 3 model for classification**  
✅ Extracts text from PDFs using DocumentService  
✅ **Performs REAL LLM inference for each file (NOT mocked)**  
✅ Real-time memory monitoring using `psutil`  
✅ Performance tracking with timing for each file  
✅ Memory usage analysis with model loaded  
✅ Validation of realistic execution times (5-10 seconds per file)  

## Requirements

### System Requirements

1. **Ollama must be installed and running**
   ```bash
   # Install Ollama (if not already installed)
   # Visit: https://ollama.ai/download
   
   # Start Ollama server
   ollama serve
   ```

2. **Llama 3 model must be pulled**
   ```bash
   ollama pull llama3
   ```

### Python Dependencies

Install the required dependencies:

```bash
pip install psutil reportlab PyPDF2 requests pandas
```

Or use the project's requirements file:

```bash
pip install -r requirements.txt
```

## Usage

### Prerequisites Check

Before running the test, verify that Ollama is running:

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Should return a list of models including llama3
```

### Basic Usage

Run the stress test from the project root:

```bash
python backend/test_pdf_stress.py
```

⚠️ **Expected Duration**: ~2-3 minutes for 20 files (5-10 seconds per file with LLM inference)

### What It Does

1. **Initialization Phase**
   - Loads the DocumentService for PDF parsing
   - **Initializes TriageService with Llama 3 model connection**
   - **Verifies Ollama is running and model is available**
   - Generates 20 dummy PDF files in memory (~3.5 KB each)
   - Records baseline memory usage

2. **Stress Test Phase (REAL LLM INFERENCE)**
   - For each of the 20 PDFs:
     - Extracts text using DocumentService
     - **Sends text to Llama 3 for classification**
     - **Model performs actual inference (NOT mocked)**
     - Monitors memory usage after each file
     - Tracks execution time
   - Single iteration (20 files total)

3. **Analysis Phase**
   - Calculates average time per file
   - Reports memory usage with model loaded
   - Validates timing is realistic (warns if < 1s, confirms if >= 5s)
   - Generates comprehensive report

## Output

The stress test produces detailed output including:

### Performance Metrics
- Files processed (20 files)
- Average/Min/Max execution time per file
- Total processing time
- **Timing validation** (warns if too fast, confirms if realistic)

### Memory Analysis
- Initial vs Final memory usage
- Memory delta with model loaded
- Peak memory usage during inference
- Memory per file processed

### LLM Inference Validation
The test validates that real inference is happening:
- ✅ **Realistic timing**: >= 5 seconds per file
- ⚠️ **Warning**: < 1 second per file (model may be mocked)
- Shows classification results for each file

## Example Output

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
  File 3/20: 6.892s | Memory: 1853.12 MB (Δ +602.67 MB) | Classified: No
  ...
  File 20/20: 6.543s | Memory: 1865.78 MB (Δ +615.33 MB) | Classified: Yes
  End of iteration memory: 1866.12 MB

======================================================================
STRESS TEST RESULTS
======================================================================

Performance Metrics:
  - Files processed: 20
  - Average time per file: 6.745 seconds
  - Min time: 6.234 seconds
  - Max time: 7.891 seconds
  - Total processing time: 134.90 seconds

  ⚠️  Expected: 5-10 seconds per file with real LLM inference
  ✓ Realistic timing confirmed - LLM is performing real inference

Memory Analysis:
  - Initial memory: 1250.45 MB
  - Final memory: 1866.12 MB
  - Memory delta: +615.67 MB (+49.2%)
  - Peak memory: 1868.45 MB
  - Min memory: 1250.45 MB

======================================================================
SUMMARY
======================================================================
✓ Processed 20 files successfully
✓ Average time per file: 6.745 seconds
⚠️  Memory grew by 615.67 MB - Review for potential leaks
```

## Interpreting Results

### Good Results ✅
- Average time per file: **5-10 seconds** (realistic for LLM inference)
- Model successfully loaded and performing inference
- Memory stabilizes after initial model load
- All files classified successfully

### Warning Signs ⚠️
- Average time < 1 second (model may not be running)
- Memory continues growing linearly beyond model load
- Connection errors to Ollama
- Classification failures

### Critical Issues 🚨
- Ollama not running or not accessible
- Model not found or failed to load
- Average time < 0.5 seconds (definitely not using LLM)
- Process crashes or out of memory errors

## Customization

You can modify the test parameters in `test_pdf_stress.py`:

```python
# Create stress test with custom parameters
stress_test = PDFStressTest(
    num_pdfs=20,           # Number of PDFs to generate
    iterations=1,          # Number of iterations (keep at 1 for LLM testing)
    ollama_url="http://localhost:11434",  # Ollama API URL
    model_name="llama3"    # LLM model name
)
```

## Notes

- This test requires Ollama to be running locally, so it's not suitable for CI/CD pipelines
- The test takes ~2-3 minutes to complete (vs <1 second without LLM)
- Memory usage will be significantly higher due to model loading (~600-800 MB increase)
- Results will vary based on hardware and Ollama configuration

## Troubleshooting

### Ollama Connection Error
```
ERROR: Ollama is not accessible at http://localhost:11434
```
**Solution**: Start Ollama server
```bash
ollama serve
```

### Model Not Found
```
⚠️  Model 'llama3' not found in available models
```
**Solution**: Pull the Llama 3 model
```bash
ollama pull llama3
```

### ImportError: No module named 'pandas'
```bash
pip install pandas
```

### ImportError: PyPDF2 not found
```bash
pip install PyPDF2
```

### ImportError: No module named 'psutil'
```bash
pip install psutil
```

### ImportError: No module named 'reportlab'
```bash
pip install reportlab
```

### Average Time Too Low (< 1 second)
This indicates the LLM is not actually running. Check:
1. Ollama is running: `curl http://localhost:11434/api/tags`
2. Model is available: `ollama list`
3. No mocking in the code

## Technical Details

### PDF Generation
- Uses `reportlab` to create realistic PDFs with text content
- Fallback to minimal PDF generation if reportlab unavailable
- Each PDF contains 3 pages with invoice-like data

### LLM Integration
- Uses `TriageService` which connects to Ollama API
- Sends extracted text to Llama 3 for classification
- Classification criteria: "Classify if this document is an invoice or receipt"
- Each inference call is REAL - no mocking or caching
- Model performs actual token generation and reasoning

### Memory Monitoring
- Uses `psutil.Process().memory_info().rss` for accurate memory tracking
- Samples memory after each file to track model impact
- Forces garbage collection after iteration
- Tracks memory delta from baseline

### Performance Validation
- Warns if average time < 1 second (likely not using LLM)
- Confirms if average time >= 5 seconds (realistic for LLM)
- Tracks min/max/average times across all files

## Performance Baseline

Expected results with REAL Llama 3 inference:
- **Throughput**: ~0.15-0.2 files/second (with LLM)
- **Average time**: 5-10 seconds per file
- **Memory growth**: +500-800 MB (model loading and inference)
- **Status**: ✅ Real LLM inference confirmed

**Note**: Previous version without LLM: 0.003s per file, +0.28 MB
**Current version with LLM**: ~6-7s per file, +600 MB (much more realistic!)

## Future Enhancements

Potential improvements to the stress test:
- [ ] Add CPU usage monitoring during inference
- [ ] Test with different LLM models (llama2, mistral, etc.)
- [ ] Test with varying PDF sizes and complexity
- [ ] Concurrent inference stress test (multiple files in parallel)
- [ ] Export results to JSON/CSV for trending
- [ ] Compare performance across different hardware (CPU vs GPU)
- [ ] Test with actual production PDFs

## License

This stress test is part of the NordicSecure project.

## Contact

For questions or issues with the stress test, please open an issue on GitHub.
