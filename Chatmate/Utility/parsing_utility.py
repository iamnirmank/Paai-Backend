import os
from dotenv import load_dotenv
import PyPDF2
import docx
from llama_index.readers.web import SimpleWebPageReader
from llama_index.core import SimpleDirectoryReader
from llama_parse import LlamaParse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

SUPPORTED_FILE_TYPES = [
    '.602', '.abw', '.cgm', '.cwk', '.doc', '.docx', '.docm', 
    '.dot', '.dotm', '.hwp', '.key', '.lwp', '.mw', '.mcw', '.pages', 
    '.pbd', '.ppt', '.pptm', '.pptx', '.pot', '.potm', '.potx', '.rtf', 
    '.sda', '.sdd', '.sdp', '.sdw', '.sgl', '.sti', '.sxi', '.sxw', 
    '.stw', '.sxg', '.txt', '.uof', '.uop', '.uot', '.vor', '.wpd', 
    '.wps', '.xml', '.zabw', '.epub', '.jpg', '.jpeg', '.png', '.gif', 
    '.bmp', '.svg', '.tiff', '.webp', '.htm', '.html', '.xlsx', '.xls', 
    '.xlsm', '.xlsb', '.xlw', '.csv', '.dif', '.sylk', '.slk', '.prn', 
    '.numbers', '.et', '.ods', '.fods', '.uos1', '.uos2', '.dbf', 
    '.wk1', '.wk2', '.wk3', '.wk4', '.wks', '.123', '.wq1', '.wq2', 
    '.wb1', '.wb2', '.wb3', '.qpw', '.xlr', '.eth', '.tsv'
]

def document_parser(file_path):
    """Parse the text of a document using LlamaParse."""
    try:
        parser = LlamaParse(result_type="markdown")
        extension = get_file_extension(file_path)

        if extension not in SUPPORTED_FILE_TYPES:
            raise ValueError(f"Unsupported file type: {extension}")

        file_extractor = {extension: parser}
        documents = SimpleDirectoryReader(input_files=[file_path], file_extractor=file_extractor).load_data()
        return documents
    
    except Exception as e:
        print(f"Error parsing document: {str(e)}")
        return []

def read_file(file_path):
    """Parse the text of a document using LlamaParse."""
    try:
        file_type = get_file_extension(file_path)

        if file_type == ".pdf":
            return [{'text': read_pdf(file_path)}]
        elif file_type == ".docx":
            return [{'text': read_docx(file_path)}]
        else:
            return [{'text': doc.text} for doc in document_parser(file_path)]
    
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        return []

def get_file_extension(file_path):
    file_extension_index = file_path.lower().rfind('.')
    if file_extension_index == -1:
        raise ValueError("No file extension found")
    return file_path[file_extension_index:]

def read_pdf(file_path):
    """Read text from a PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(file_path)
        text = "".join([page.extract_text() for page in pdf_reader.pages])
        return text
    except Exception as e:
        logger.error(f"Error reading PDF: {str(e)}")
        return ""

def read_docx(file_path):
    """Read text from a DOCX file."""
    try:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        logger.error(f"Error reading DOCX: {str(e)}")
        return ""

def link_parser(url):
    """Parse the text of a webpage using LlamaParse."""
    try:
        documents = SimpleWebPageReader(html_to_text=True).load_data(url)
        return [{'text': doc.text} for doc in documents]
    except Exception as e:
        logger.error(f"Error parsing link: {str(e)}")
        return []