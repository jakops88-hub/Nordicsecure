# PDF Processing Stress Test

## Overview

This stress test evaluates the performance and memory stability of the NordicSecure PDF processing engine. It performs repeated PDF parsing operations while monitoring for memory leaks and performance degradation.

## Purpose

As a Performance Engineer, this test helps you:
- **Detect Memory Leaks**: Identifies if memory grows linearly without garbage collection
- **Measure Performance**: Tracks execution time and throughput
- **Validate Stability**: Ensures the system can handle repeated operations without degradation
- **Baseline Metrics**: Establishes performance baselines for future optimization

## Features

✅ Generates 50 dummy PDF files with realistic content (invoice-like data)  
✅ Processes PDFs in multiple iterations (default: 3 iterations = 150 files)  
✅ Real-time memory monitoring using `psutil`  
✅ Performance tracking with timing for every 5th file  
✅ Memory leak detection using linear regression analysis  
✅ Comprehensive performance and memory reporting  
✅ Automatic garbage collection between iterations  

## Requirements

Install the required dependencies:

```bash
pip install psutil reportlab PyPDF2
```

Or use the project's requirements file:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the stress test from the project root:

```bash
python backend/test_pdf_stress.py
```

### What It Does

1. **Initialization Phase**
   - Loads the DocumentService
   - Generates 50 dummy PDF files in memory (~3.5 KB each)
   - Records baseline memory usage

2. **Stress Test Phase**
   - Processes all 50 PDFs
   - Repeats 3 times (150 files total)
   - Monitors memory every 5 files
   - Forces garbage collection after each iteration

3. **Analysis Phase**
   - Calculates average time per file
   - Analyzes memory growth patterns
   - Detects potential memory leaks
   - Generates comprehensive report

## Output

The stress test produces detailed output including:

### Performance Metrics
- Files processed
- Average/Min/Max execution time per file
- Total processing time
- Throughput (files/second)

### Memory Analysis
- Initial vs Final memory usage
- Memory delta and growth percentage
- Peak and minimum memory usage
- Memory growth rate (MB per sample)

### Memory Leak Detection
The test uses statistical analysis to detect memory leaks:
- ✅ **No leak**: Memory stable, growth < 5 MB
- ⚠️ **Warning**: Significant growth but not linear (may be caching)
- 🚨 **Leak detected**: Linear growth > 5 MB with consistent slope

## Example Output

```
======================================================================
PDF PROCESSING STRESS TEST - MEMORY LEAK & PERFORMANCE ANALYSIS
======================================================================

Configuration:
  - Number of PDFs: 50
  - Iterations: 3
  - Total files to process: 150

Initializing DocumentService...
✓ DocumentService initialized

Generating 50 dummy PDF files...
✓ Generated 50 PDFs (Total: 172.80 KB)

======================================================================
STARTING STRESS TEST
======================================================================

Initial memory usage: 703.83 MB

Iteration 1/3
--------------------------------------------------
  File 5/150: 0.003s | Memory: 703.99 MB (Δ +0.16 MB)
  File 10/150: 0.003s | Memory: 703.99 MB (Δ +0.16 MB)
  ...
  End of iteration memory: 704.11 MB

======================================================================
STRESS TEST RESULTS
======================================================================

Performance Metrics:
  - Files processed: 150
  - Average time per file: 0.003 seconds
  - Min time: 0.003 seconds
  - Max time: 0.005 seconds
  - Total processing time: 0.49 seconds

Memory Analysis:
  - Initial memory: 703.83 MB
  - Final memory: 704.11 MB
  - Memory delta: +0.28 MB (+0.0%)
  - Peak memory: 704.11 MB
  - Min memory: 703.83 MB

Memory Leak Detection:
  - Memory growth rate: 0.0038 MB per sample

✓ Memory appears stable - No significant memory leak detected
  Memory growth is within acceptable limits (0.28 MB).

======================================================================
SUMMARY
======================================================================
✓ Processed 150 files successfully
✓ Average time per file: 0.003 seconds
✓ Memory stable: +0.28 MB change
```

## Interpreting Results

### Good Results ✅
- Average time per file: < 0.01 seconds
- Memory delta: < 5 MB
- No linear growth pattern
- Stable memory across iterations

### Warning Signs ⚠️
- Average time increasing over iterations
- Memory growth > 5 MB but not linear
- Occasional spikes in execution time

### Critical Issues 🚨
- Memory leak detected (linear growth)
- Memory delta > 50 MB
- Increasing execution times
- Process crashes or errors

## Customization

You can modify the test parameters in `test_pdf_stress.py`:

```python
# Create stress test with custom parameters
stress_test = PDFStressTest(
    num_pdfs=100,     # Number of PDFs to generate
    iterations=5      # Number of times to process all PDFs
)
```

## Integration with CI/CD

Add the stress test to your continuous integration pipeline:

```bash
# Run stress test and fail if memory leak detected
python backend/test_pdf_stress.py || exit 1
```

## Troubleshooting

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

### High initial memory usage
This is normal - sentence-transformers models consume significant memory. The stress test focuses on memory growth, not absolute values.

## Technical Details

### PDF Generation
- Uses `reportlab` to create realistic PDFs with text content
- Fallback to minimal PDF generation if reportlab unavailable
- Each PDF contains 3 pages with invoice-like data

### Memory Monitoring
- Uses `psutil.Process().memory_info().rss` for accurate memory tracking
- Samples memory every 5 files and at iteration boundaries
- Forces garbage collection between iterations

### Leak Detection Algorithm
1. Collect memory samples throughout execution
2. Calculate linear regression slope
3. Check for consistent upward trend
4. Flag if growth > 5 MB AND slope > 0.5 MB/sample

## Performance Baseline

Based on the initial test run:
- **Throughput**: ~306 files/second
- **Average time**: 0.003 seconds per file
- **Memory stability**: +0.28 MB over 150 files
- **Status**: ✅ No memory leaks detected

## Future Enhancements

Potential improvements to the stress test:
- [ ] Add CPU usage monitoring
- [ ] Test with real PDF files from a directory
- [ ] Configurable stress test duration
- [ ] Performance regression detection
- [ ] Concurrent processing stress test
- [ ] Export results to JSON/CSV for trending

## License

This stress test is part of the NordicSecure project.

## Contact

For questions or issues with the stress test, please open an issue on GitHub.
