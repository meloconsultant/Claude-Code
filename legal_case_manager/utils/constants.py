"""Constants for the Legal Case Manager."""

# Bates numbering ranges
PLAINTIFF_BATES_START = 1
PLAINTIFF_BATES_END = 99999
DEFENDANT_BATES_START = 100000
DEFENDANT_BATES_END = 199999

BATES_PREFIX_PLAINTIFF = "PLTF"
BATES_PREFIX_DEFENDANT = "DFND"

# Document categories
DOC_CATEGORIES = [
    "pleadings",
    "discovery",
    "witness_statements",
    "depositions",
    "emails",
    "photos",
    "contracts",
    "financial_records",
    "expert_reports",
    "motions",
    "orders",
    "correspondence",
    "transcripts",
    "exhibits",
    "other",
]

# Relevance tags
RELEVANCE_TAGS = {
    "HOT_GOOD": "Hot-Good (damaging to opposing party)",
    "HOT_BAD": "Hot-Bad (hurts our position)",
    "NEUTRAL": "Neutral",
    "PRIVILEGE": "Privilege (redact)",
    "CONFIDENTIAL": "Confidential",
    "WORK_PRODUCT": "Work Product",
}

# Case phases (ordered)
CASE_PHASES = [
    "intake",
    "pleadings",
    "discovery",
    "motions",
    "trial_prep",
    "trial",
    "post_trial",
    "appeal",
]

CASE_PHASE_LABELS = {
    "intake": "Intake & Investigation",
    "pleadings": "Pleadings",
    "discovery": "Discovery",
    "motions": "Pre-Trial Motions",
    "trial_prep": "Trial Preparation",
    "trial": "Trial",
    "post_trial": "Post-Trial",
    "appeal": "Appeal",
}

# File type mappings
FILE_TYPE_MAP = {
    ".pdf": "PDF Document",
    ".doc": "Word Document",
    ".docx": "Word Document",
    ".xls": "Excel Spreadsheet",
    ".xlsx": "Excel Spreadsheet",
    ".csv": "CSV Data",
    ".txt": "Plain Text",
    ".eml": "Email",
    ".msg": "Email (Outlook)",
    ".jpg": "Photograph",
    ".jpeg": "Photograph",
    ".png": "Image",
    ".tiff": "Image (TIFF)",
    ".tif": "Image (TIFF)",
    ".gif": "Image",
    ".mp3": "Audio Recording",
    ".wav": "Audio Recording",
    ".mp4": "Video Recording",
    ".mov": "Video Recording",
    ".avi": "Video Recording",
    ".json": "JSON Data",
    ".xml": "XML Data",
    ".html": "HTML Document",
    ".zip": "Archive",
    ".pptx": "PowerPoint Presentation",
    ".ppt": "PowerPoint Presentation",
}

# Issue tags for case themes
COMMON_ISSUES = [
    "breach_of_contract",
    "negligence",
    "fraud",
    "misrepresentation",
    "discrimination",
    "harassment",
    "wrongful_termination",
    "personal_injury",
    "product_liability",
    "intellectual_property",
    "trade_secret",
    "defamation",
    "malpractice",
    "insurance_dispute",
    "employment_dispute",
]
