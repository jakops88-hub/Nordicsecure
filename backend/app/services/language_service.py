"""
Language Service - Multi-language support for UI text
Provides translations for English and Swedish languages
"""

from typing import Dict, Any


class LanguageService:
    """
    Service for handling UI translations between English and Swedish.
    """
    
    TRANSLATIONS = {
        "en": {
            # Tabs
            "tab_chat": "Chat",
            "tab_upload": "Upload",
            "tab_triage": "Mass Sorting",
            
            # Triage UI
            "triage_title": "🗂️ AI Triage - Batch File Sorting",
            "triage_description": "Automatically sort hundreds of unstructured files (PDF/Images) based on your criteria.",
            "source_folder": "Source Folder (Inbox)",
            "source_folder_help": "Path to the folder containing files to sort",
            "target_relevant": "Target Folder: Relevant",
            "target_relevant_help": "Path where relevant files will be moved",
            "target_irrelevant": "Target Folder: Irrelevant",
            "target_irrelevant_help": "Path where non-relevant files will be moved",
            "sorting_criteria": "Sorting Criteria",
            "sorting_criteria_help": "Describe what makes a document relevant (e.g., 'Is this document related to a bankruptcy application or promissory note?')",
            "sorting_criteria_placeholder": "E.g., Is this document related to a bankruptcy application or promissory note?",
            "start_sorting": "Start Sorting",
            "processing": "Processing files...",
            "complete": "Sorting Complete!",
            "download_log": "Download Audit Log",
            "live_log": "Live Execution Log",
            "progress": "Progress",
            
            # Status messages
            "processing_file": "Processing file",
            "moved_to_relevant": "Moved to: Relevant",
            "moved_to_irrelevant": "Moved to: Irrelevant",
            "skipped_error": "Skipped due to error",
            "files_processed": "files processed",
            "error_occurred": "Error occurred",
            
            # Audit log columns
            "log_filename": "Filename",
            "log_date": "Date",
            "log_decision": "Decision (Yes/No)",
            "log_reason": "AI Reasoning",
            "log_moved_to": "Moved To",
            
            # Errors
            "error_source_not_exists": "Source folder does not exist",
            "error_target_not_exists": "Target folder does not exist",
            "error_no_criteria": "Please provide sorting criteria",
            "error_file_processing": "Error processing file",
            
            # Settings
            "max_pages_label": "Max Pages to Analyze",
            "max_pages_help": "Limit OCR to first N pages to save time (recommended: 3-5)",
        },
        "sv": {
            # Tabs
            "tab_chat": "Chatt",
            "tab_upload": "Ladda upp",
            "tab_triage": "Mass-sortering",
            
            # Triage UI
            "triage_title": "🗂️ AI Triage - Batch-sortering",
            "triage_description": "Sortera automatiskt hundratals ostrukturerade filer (PDF/Bilder) baserat på dina kriterier.",
            "source_folder": "Källmapp (Inkorg)",
            "source_folder_help": "Sökväg till mappen som innehåller filer att sortera",
            "target_relevant": "Målmapp: Träff",
            "target_relevant_help": "Sökväg dit relevanta filer kommer att flyttas",
            "target_irrelevant": "Målmapp: Övrigt",
            "target_irrelevant_help": "Sökväg dit icke-relevanta filer kommer att flyttas",
            "sorting_criteria": "Sorteringskriterier",
            "sorting_criteria_help": "Beskriv vad som gör ett dokument relevant (t.ex. 'Är detta dokument relaterat till en konkursansökan eller skuldebrev?')",
            "sorting_criteria_placeholder": "T.ex. Är detta dokument relaterat till en konkursansökan eller skuldebrev?",
            "start_sorting": "Starta Sortering",
            "processing": "Bearbetar filer...",
            "complete": "Sortering Klar!",
            "download_log": "Ladda ner Revisionslogg",
            "live_log": "Live Exekveringslogg",
            "progress": "Framsteg",
            
            # Status messages
            "processing_file": "Bearbetar fil",
            "moved_to_relevant": "Flyttad till: Träff",
            "moved_to_irrelevant": "Flyttad till: Övrigt",
            "skipped_error": "Överhoppad p.g.a. fel",
            "files_processed": "filer bearbetade",
            "error_occurred": "Fel uppstod",
            
            # Audit log columns
            "log_filename": "Filnamn",
            "log_date": "Datum",
            "log_decision": "Beslut (Ja/Nej)",
            "log_reason": "AI Motivering",
            "log_moved_to": "Flyttad Till",
            
            # Errors
            "error_source_not_exists": "Källmappen finns inte",
            "error_target_not_exists": "Målmappen finns inte",
            "error_no_criteria": "Vänligen ange sorteringskriterier",
            "error_file_processing": "Fel vid bearbetning av fil",
            
            # Settings
            "max_pages_label": "Max Sidor att Analysera",
            "max_pages_help": "Begränsa OCR till första N sidorna för att spara tid (rekommenderat: 3-5)",
        }
    }
    
    def __init__(self, language: str = "en"):
        """
        Initialize language service.
        
        Args:
            language: Language code ('en' or 'sv')
        """
        self.language = language if language in ["en", "sv"] else "en"
    
    def get(self, key: str, default: str = "") -> str:
        """
        Get translated text for a key.
        
        Args:
            key: Translation key
            default: Default text if key not found
            
        Returns:
            Translated text
        """
        return self.TRANSLATIONS.get(self.language, {}).get(key, default or key)
    
    def set_language(self, language: str):
        """
        Set the current language.
        
        Args:
            language: Language code ('en' or 'sv')
        """
        if language in ["en", "sv"]:
            self.language = language
    
    def get_all(self) -> Dict[str, str]:
        """
        Get all translations for current language.
        
        Returns:
            Dictionary of all translations
        """
        return self.TRANSLATIONS.get(self.language, {})
