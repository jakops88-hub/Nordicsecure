"""Setup configuration for NordicSecure backend."""

from setuptools import setup, find_packages

setup(
    name="nordicsecure-backend",
    version="0.1.0",
    description="Nordic Secure Private, offline RAG infrastructure for regulated industries",
    author="NordicSecure",
    packages=find_packages(),
    install_requires=[
        "PyPDF2>=3.0.0",
        "pdf2image>=1.16.0",
        "pytesseract>=0.3.10",
        "sentence-transformers>=2.2.0",
        "torch>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "numpy>=1.24.0",
        "pillow>=10.0.0",
    ],
    python_requires=">=3.8",
)
