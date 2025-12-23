# GPU Acceleration and Multilingual Support Guide

## Overview

This document describes the GPU acceleration features and multilingual support (including Punjabi script) implemented in NordicSecure for PDF processing and renaming.

## 1. GPU Acceleration

### Hardware Detection

NordicSecure automatically detects available hardware acceleration and optimizes inference accordingly:

**Supported Hardware:**
- **NVIDIA GPUs** (CUDA) - Automatic detection and full layer offloading
- **Apple Silicon** (M1/M2/M3) - Metal Performance Shaders (MPS) support
- **CPU Fallback** - Automatically used if no GPU is available

**Performance Impact:**
- **With GPU**: Inference time reduced from ~10s to ~1-2s per document
- **CPU Only**: ~10s per document (baseline)

### Implementation Details

The `HardwareDetector` class in `backend/app/utils/hardware_detector.py` performs the following:

1. **CUDA Detection**: Checks if PyTorch with CUDA is available and if NVIDIA GPU is present
2. **MPS Detection**: Checks if running on macOS with Apple Silicon and MPS support
3. **Device Selection**: Returns appropriate device string (`cuda`, `mps`, or `cpu`)
4. **GPU Layer Configuration**: Sets `n_gpu_layers=-1` to offload all layers when GPU is available

### How It Works

```python
from backend.app.utils.hardware_detector import get_hardware_detector

detector = get_hardware_detector()
hardware = detector.detect_hardware()

print(f"Device: {hardware['device']}")  # 'cuda', 'mps', or 'cpu'
print(f"GPU Layers: {hardware['gpu_layers']}")  # -1 for all, 0 for CPU
```

The hardware detection is automatically integrated into:
- **DocumentService**: Sentence-transformers embeddings use detected GPU
- **Future LLM Integration**: Ready for llama-cpp-python with GPU offloading

## 2. Intelligent PDF Renaming

### Feature Overview

The RenameService extracts author and title information from PDF content (not filename) and renames files to a standardized format: `Author - Title.pdf`

**Key Features:**
- Analyzes first 3 pages of PDF content (not just filename)
- Uses local LLM (Llama 3) for intelligent extraction
- Handles multilingual content (English, Swedish, Punjabi, Arabic, Chinese, etc.)
- Safe renaming with collision detection
- UTF-8 filename support for non-ASCII characters

### Usage

**Single File Rename:**
```bash
curl -X POST http://localhost:8000/rename/single \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/rich dad poor dad.pdf",
    "max_pages": 3
  }'
```

**Batch Rename (20,000 books example):**
```bash
curl -X POST http://localhost:8000/rename/batch \
  -H "Content-Type: application/json" \
  -d '{
    "folder_path": "/path/to/books",
    "max_pages": 3
  }'
```

### Renaming Logic

The service follows this process:

1. **Extract Text**: Reads first 3 pages of PDF using PyPDF2
2. **OCR Fallback**: If PDF is scanned/image-based, uses Tesseract OCR
3. **LLM Analysis**: Sends text to Llama 3 with prompt:
   ```
   Analyze this document excerpt and extract:
   - Author name(s)
   - Document title
   Preserve original language/script
   ```
4. **Sanitize**: Removes invalid filename characters while preserving UTF-8
5. **Rename**: Safely renames to `Author - Title.pdf` format

### Example Transformations

```
Before: rich dad poor dad.pdf
After:  Robert Kiyosaki - Rich Dad Poor Dad.pdf

Before: 1234567890.pdf
After:  J.K. Rowling - Harry Potter and the Philosopher's Stone.pdf

Before: scan_book_punjabi.pdf
After:  ਅਮਰੀਕ ਸਿੰਘ - ਪੰਜਾਬ ਦੀ ਇਤਿਹਾਸ.pdf
```

## 3. Multilingual Support

### Unicode and UTF-8 Encoding

**PDF Text Extraction:**
- PyPDF2 natively supports UTF-8 encoding
- Correctly extracts Punjabi (ਪੰਜਾਬੀ), Arabic (العربية), Chinese (中文), etc.
- No additional configuration needed

**File Renaming:**
- Python's `Path.rename()` handles UTF-8 correctly on Windows/Linux/macOS
- Filenames can contain any valid Unicode characters
- Invalid characters are sanitized while preserving script

**Supported Scripts:**
- Latin (English, Swedish, German, etc.)
- Devanagari (Hindi, Marathi)
- Gurmukhi (Punjabi)
- Arabic
- Chinese/Japanese/Korean (CJK)
- Cyrillic (Russian, Ukrainian)
- And more...

### Tesseract OCR Language Support

For **scanned PDFs**, Tesseract OCR is used to extract text. Language packs must be installed separately.

**Installing Punjabi Language Pack:**

**Windows:**
```bash
# Download from: https://github.com/tesseract-ocr/tessdata
# Place pan.traineddata in: C:\Program Files\Tesseract-OCR\tessdata\
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr-pan
```

**macOS:**
```bash
brew install tesseract-lang
```

**Required Language Packs for Common Languages:**
- English: `eng` (usually pre-installed)
- Swedish: `swe`
- Punjabi: `pan`
- Hindi: `hin`
- Arabic: `ara`
- Chinese Simplified: `chi_sim`
- Chinese Traditional: `chi_tra`

**Multiple Language Detection:**
```python
# For multilingual documents
pytesseract.image_to_string(image, lang='eng+pan+hin')
```

### Verifying OCR Support

**Check installed languages:**
```bash
tesseract --list-langs
```

**Test OCR with specific language:**
```bash
tesseract input.png output -l pan
```

## 4. Performance Optimization for Large Libraries

For users with **20,000+ books**, performance is critical:

### Optimization Strategies

1. **GPU Acceleration** (Essential)
   - Reduces inference time by 5-10x
   - NVIDIA GPU with 8GB+ VRAM recommended
   - Apple M1/M2/M3 with 16GB+ unified memory

2. **Lazy Loading** (Implemented)
   - Only reads first 3 pages of each PDF
   - Reduces disk I/O significantly
   - Configurable via `max_pages` parameter

3. **Batch Processing** (Implemented)
   - Processes all files in one operation
   - Progress tracking and error recovery
   - Detailed audit log for review

4. **Parallel Processing** (Future Enhancement)
   - Process multiple files simultaneously
   - Utilize multiple CPU cores
   - Further reduce total processing time

### Estimated Processing Times

**Hardware: NVIDIA RTX 3080 + NVMe SSD**
- Single file: ~1-2 seconds
- 20,000 files: ~11-22 hours (sequential)
- With 4x parallelization: ~3-6 hours

**Hardware: Apple M2 Max + SSD**
- Single file: ~2-3 seconds  
- 20,000 files: ~13-30 hours (sequential)
- With 4x parallelization: ~4-8 hours

**Hardware: CPU Only (Intel i7)**
- Single file: ~10-15 seconds
- 20,000 files: ~55-83 hours (sequential)
- GPU acceleration highly recommended for large libraries

## 5. Troubleshooting

### GPU Not Detected

**Issue**: Hardware detector shows CPU only, but GPU is present

**Solutions:**
1. Install PyTorch with CUDA support:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

2. Verify CUDA installation:
   ```bash
   nvidia-smi
   ```

3. Check PyTorch CUDA availability:
   ```python
   import torch
   print(torch.cuda.is_available())
   print(torch.cuda.get_device_name(0))
   ```

### OCR Not Working for Punjabi

**Issue**: Text extraction fails or shows garbled text for Punjabi PDFs

**Solutions:**
1. Install Punjabi language pack:
   ```bash
   sudo apt-get install tesseract-ocr-pan
   ```

2. Verify installation:
   ```bash
   tesseract --list-langs | grep pan
   ```

3. Test with sample image:
   ```bash
   tesseract punjabi_text.png output -l pan
   ```

### Filename Encoding Errors

**Issue**: Renamed files have garbled characters on Windows

**Solutions:**
1. Ensure Python uses UTF-8:
   ```bash
   set PYTHONIOENCODING=utf-8
   ```

2. Use latest Windows 10/11 (better UTF-8 support)

3. Check filesystem supports UTF-8 filenames (NTFS, ext4, APFS all do)

## 6. API Reference

### POST /rename/single

Rename a single PDF file based on content.

**Request:**
```json
{
  "file_path": "/path/to/file.pdf",
  "max_pages": 3
}
```

**Response:**
```json
{
  "original_name": "old_name.pdf",
  "new_name": "Author - Title.pdf",
  "success": true,
  "author": "Author Name",
  "title": "Document Title",
  "confidence": 0.92,
  "error": null
}
```

### POST /rename/batch

Batch rename all PDFs in a folder.

**Request:**
```json
{
  "folder_path": "/path/to/books",
  "max_pages": 3
}
```

**Response:**
```json
{
  "total_files": 20000,
  "processed": 20000,
  "renamed": 19500,
  "failed": 500,
  "rename_log": [
    {
      "original_name": "file1.pdf",
      "new_name": "Author1 - Title1.pdf",
      "success": true,
      "author": "Author1",
      "title": "Title1",
      "confidence": 0.95
    }
  ]
}
```

## 7. Best Practices

1. **Always backup before batch renaming** - Make a copy of your library first
2. **Test on small subset** - Try 10-20 files before processing 20,000
3. **Review audit log** - Check for extraction errors or edge cases
4. **Use GPU for large libraries** - Dramatically faster processing
5. **Monitor disk space** - Ensure sufficient space for operations
6. **Check Ollama is running** - Service depends on local LLM API

## 8. Future Enhancements

- [ ] Parallel processing support (4x-8x speedup)
- [ ] Direct llama-cpp-python integration for offline operation
- [ ] Custom prompt templates for specialized domains
- [ ] Smart book series detection and numbering
- [ ] ISBN extraction and metadata enrichment
- [ ] Cover image extraction and organization
