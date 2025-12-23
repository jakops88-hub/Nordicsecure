# Stress Testing Guide for Nordic Secure

This guide explains how to run comprehensive stress tests on the Nordic Secure application with 50 PDF files and detailed statistics.

## Overview

Two stress test scripts are available:

1. **Backend Stress Test** (`backend/test_pdf_stress.py`) - Tests PDF processing directly
2. **Live App Stress Test** (`stress_test_live.py`) - Tests the full stack via API

## Prerequisites

### System Requirements
- Python 3.10 or 3.11
- 16GB RAM minimum (32GB recommended)
- Backend dependencies installed: `pip install -r backend/requirements.txt`

### For Live App Testing
- Backend server running on `http://localhost:8000`
- Ollama running with llama3 model
- ChromaDB initialized

## Option 1: Backend Stress Test (Direct PDF Processing)

Tests PDF parsing and processing directly without API layer.

### Running the Test

```bash
# From repository root
cd /home/runner/work/Nordicsecure/Nordicsecure
python backend/test_pdf_stress.py
```

### What It Tests

- **PDF Generation**: Creates 50 realistic test PDFs (invoices with 3 pages each)
- **Text Extraction**: Parses PDF content
- **Memory Usage**: Monitors RAM consumption throughout
- **Performance**: Tracks execution time for all files
- **Memory Leak Detection**: Analyzes memory growth patterns

### Statistics Provided

#### Performance Metrics
- Total runtime
- Files processed (total, successful, failed)
- Success rate percentage
- Throughput (files/second)

#### Execution Time Statistics
- Average time per file
- Median (p50), p90, p95, p99 percentiles
- Min/max processing times
- Total processing time

#### Memory Analysis
- Initial/final memory usage
- Memory delta and growth percentage
- Peak/minimum/average memory
- Memory per file average
- Memory leak detection with linear regression

#### Real-time Progress
- Progress percentage
- Current file being processed
- Memory usage updates every 5 files
- Estimated time remaining (ETA)

### Output

1. **Console Output**: Real-time progress and final statistics
2. **Report File**: `stress_test_report_YYYYMMDD_HHMMSS.txt` with detailed breakdown

### Example Console Output

```
======================================================================
PDF PROCESSING STRESS TEST - MEMORY LEAK & PERFORMANCE ANALYSIS
======================================================================

Configuration:
  - Number of PDFs: 50
  - Iterations: 1
  - Total files to process: 50
  - Ollama Host: http://localhost:11434

✓ DocumentService initialized
✓ Generated 50 PDFs (Total: 245.32 KB)

======================================================================
STARTING STRESS TEST
======================================================================

Initial memory usage: 523.45 MB

Iteration 1/1
--------------------------------------------------
  [ 10.0%] File 5/50: 1.234s | Memory: 545.23 MB (Δ +21.78 MB) | ETA: 4.5m
  [ 20.0%] File 10/50: 1.189s | Memory: 556.12 MB (Δ +32.67 MB) | ETA: 3.8m
  ...
```

## Option 2: Live App Stress Test (Full Stack)

Tests the complete application including API endpoints and upload workflow.

### Starting the Backend

```bash
# Terminal 1: Start backend
cd /home/runner/work/Nordicsecure/Nordicsecure
python backend/main.py
```

Wait for backend to be ready (check for "Application startup complete" message).

### Running the Test

```bash
# Terminal 2: Run stress test
cd /home/runner/work/Nordicsecure/Nordicsecure
python stress_test_live.py
```

### What It Tests

- **API Health**: Verifies backend is running
- **File Upload**: Tests `/ingest` endpoint with 50 PDFs
- **API Response Times**: Measures HTTP request/response timing
- **End-to-End Processing**: Full upload + processing workflow
- **Error Handling**: Captures API errors and timeouts
- **System Integration**: Tests all components together

### Statistics Provided

#### Overall Metrics
- Total runtime
- Files processed
- Successful/failed uploads with percentages
- Throughput (files/second)

#### API Performance
- Average upload time
- Median (p50), p90, p95 percentiles
- Min/max upload times
- API response time distribution

#### Memory Analysis
- Initial/final memory usage
- Memory delta
- Peak memory usage
- Average memory during test

#### Error Analysis
- List of failed uploads
- Error messages for each failure
- Failure patterns

### Output

1. **Console Output**: Real-time progress with success indicators
2. **Report File**: `live_stress_test_report_YYYYMMDD_HHMMSS.txt`

### Example Console Output

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

Initial memory usage: 523.45 MB

  [ 10.0%] File 5/50: ✓ 2.145s | Success: 100.0% | Memory: 545.23 MB (Δ +21.78) | ETA: 4.5m
  [ 20.0%] File 10/50: ✓ 2.089s | Success: 100.0% | Memory: 556.12 MB (Δ +32.67) | ETA: 3.8m
  ...
```

## Understanding the Statistics

### Performance Metrics

- **Throughput**: Files processed per second (higher is better)
- **Average Time**: Mean processing time per file
- **Percentiles**: 
  - p50 (median): 50% of files processed faster than this
  - p90: 90% of files processed faster than this
  - p95/p99: Performance for slowest files

### Memory Analysis

- **Memory Delta**: Total memory growth during test
- **Peak Memory**: Maximum memory used
- **Memory Leak Detection**: 
  - ✓ Stable: Memory growth < 5MB
  - ⚠️ Warning: Memory growth > 5MB but not linear
  - ❌ Leak: Memory growth > 5MB with linear trend

### Success Rates

- **100%**: Perfect - all files processed successfully
- **95-99%**: Good - minor issues
- **< 95%**: Investigate errors in report file

## Customizing the Tests

### Changing Number of PDFs

**Option 1: Via Environment Variable (Recommended)**
```bash
# Backend test
export STRESS_TEST_NUM_PDFS=100
python backend/test_pdf_stress.py

# Live app test
export STRESS_TEST_NUM_PDFS=100
python stress_test_live.py
```

**Option 2: Edit the script's `main()` function:**
```python
# backend/test_pdf_stress.py
stress_test = PDFStressTest(num_pdfs=100, iterations=1)

# stress_test_live.py
stress_test = LiveAppStressTest(num_pdfs=100)
```

### Running Multiple Iterations

For memory leak detection over extended periods:

**Option 1: Via Environment Variable**
```bash
export STRESS_TEST_NUM_PDFS=50
export STRESS_TEST_ITERATIONS=3
python backend/test_pdf_stress.py  # 150 total files
```

**Option 2: Edit the code:**
```python
stress_test = PDFStressTest(num_pdfs=50, iterations=3)  # 150 total files
```

### Changing Backend URL

For remote testing:

**Option 1: Via Environment Variable (Recommended)**
```bash
export BACKEND_URL="http://192.168.1.100:8000"
python stress_test_live.py
```

**Option 2: Edit the code:**
```python
stress_test = LiveAppStressTest(
    num_pdfs=50,
    backend_url="http://192.168.1.100:8000"
)
```

### Environment Variables Reference

The stress tests support the following environment variables:

| Variable | Description | Default | Used By |
|----------|-------------|---------|---------|
| `STRESS_TEST_NUM_PDFS` | Number of PDFs to test | `50` | Backend & Live tests |
| `STRESS_TEST_ITERATIONS` | Number of iterations | `1` | Backend test only |
| `BACKEND_URL` | Backend API URL | `http://localhost:8000` | Live test only |

## Interpreting Results

### Good Performance Indicators

✓ Throughput > 0.5 files/second  
✓ Average time < 2 seconds per file  
✓ Memory growth < 50 MB  
✓ Success rate > 95%  
✓ p95 time < 3 seconds  

### Performance Issues

⚠️ Throughput < 0.3 files/second - System may be overloaded  
⚠️ Memory growth > 100 MB - Possible memory leak  
⚠️ Success rate < 90% - Check error logs  
⚠️ High p95/p99 times - Investigate slow files  

### Common Issues

1. **Backend Not Running**
   ```
   ❌ ERROR: Backend is not running or not healthy!
   ```
   Solution: Start backend with `python backend/main.py`

2. **Ollama Not Available**
   ```
   ERROR processing: Connection refused
   ```
   Solution: Start Ollama and pull llama3 model

3. **Out of Memory**
   ```
   MemoryError or system slowdown
   ```
   Solution: Reduce number of PDFs or add more RAM

4. **Timeouts**
   ```
   Request timed out after 120 seconds
   ```
   Solution: Increase timeout or check system load

## Report Files

Both tests generate detailed report files with complete statistics:

### Report Contents

- Test configuration and timestamp
- Overall performance summary
- Detailed timing for every file
- Memory usage over time
- Complete error log
- Statistical analysis

### Report Location

Reports are saved in the current directory:
- `stress_test_report_YYYYMMDD_HHMMSS.txt` (backend test)
- `live_stress_test_report_YYYYMMDD_HHMMSS.txt` (live app test)

## Troubleshooting

### Test Runs Very Slowly

1. Check CPU usage (`top` or Task Manager)
2. Ensure Ollama is using GPU if available
3. Reduce number of PDFs
4. Check disk I/O

### High Memory Usage

1. Monitor with `htop` or Task Manager
2. Check for memory leaks in report
3. Ensure proper garbage collection
4. Restart backend between tests

### Connection Errors

1. Verify backend is running: `curl http://localhost:8000/health`
2. Check firewall settings
3. Verify correct port (8000 for backend, 8501 for frontend)

## Best Practices

1. **Close other applications** before running stress tests
2. **Monitor system resources** during the test
3. **Run tests multiple times** for consistent results
4. **Save reports** for comparison over time
5. **Test with realistic data** when possible
6. **Baseline first** - run a small test (10 files) first

## Next Steps

After running stress tests:

1. Review the generated report files
2. Compare results with previous tests
3. Identify performance bottlenecks
4. Check memory leak indicators
5. Optimize based on findings
6. Re-test to verify improvements

## Support

For issues or questions:
- Check error messages in report files
- Review backend logs
- Ensure all dependencies are installed
- Verify system meets minimum requirements
