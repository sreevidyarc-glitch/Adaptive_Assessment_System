import io
import re
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("adaptive_assessment.extraction")

MODULE_HEADER_PATTERN = re.compile(
    r'(?i)(?:^|\n)\s*(?:#+\s*)?(?:module|chapter|unit)\s*([0-9ivxlcdm]+|\w+)[:\-\s]*(.*?)(?=\n|$)'
)

def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """
    Extracts raw text from PDF, DOCX, and TXT files.
    """
    ext = filename.lower().split('.')[-1]

    if ext == 'pdf':
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            text_parts = []
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Failed to extract text from PDF '{filename}': {e}")
            raise ValueError(f"Could not read PDF file: {e}")

    elif ext in ('docx', 'doc'):
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            text_parts = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Failed to extract text from DOCX '{filename}': {e}")
            raise ValueError(f"Could not read Word document: {e}")

    elif ext in ('txt', 'md'):
        try:
            return file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return file_bytes.decode('latin-1')
            except Exception as e:
                raise ValueError(f"Could not decode text file: {e}")
    else:
        raise ValueError(f"Unsupported file format '.{ext}'. Supported formats: PDF, DOCX, TXT.")

def parse_and_chunk_course_material(
    text: str,
    max_chunk_chars: int = 350,
    min_chunk_chars: int = 25
) -> List[Dict[str, Any]]:
    """
    Identifies academic module sections and splits content into
    module-wise paragraph/sentence chunks S = {s_i}.
    """
    lines = text.splitlines()
    sections: List[Tuple[str, List[str]]] = []
    
    current_module = "Module 1: General Content"
    current_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        match = MODULE_HEADER_PATTERN.match(stripped)
        if match:
            # Save previous section if it has content
            if current_lines:
                sections.append((current_module, current_lines))
                current_lines = []
            
            mod_num = match.group(1).strip()
            mod_title = match.group(2).strip()
            if mod_title:
                current_module = f"Module {mod_num}: {mod_title}"
            else:
                current_module = f"Module {mod_num}"
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_module, current_lines))

    # If no modules were detected, treat the entire text as Module 1
    if not sections:
        sections.append(("Module 1: General Content", lines))

    # Now split each section into paragraph / sentence chunks
    chunks: List[Dict[str, Any]] = []
    global_index = 0

    for mod_name, sec_lines in sections:
        sec_text = "\n".join(sec_lines)
        # Split by double newline or single newline
        raw_paragraphs = re.split(r'\n+', sec_text)

        for para in raw_paragraphs:
            cleaned_para = re.sub(r'\s+', ' ', para).strip()
            if len(cleaned_para) < min_chunk_chars:
                continue

            # Split sentences if paragraph contains multiple full stops
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', cleaned_para) if s.strip()]
            
            if len(sentences) > 1 and len(cleaned_para) > max_chunk_chars:
                buffer = ""
                for sent in sentences:
                    if len(buffer) + len(sent) > max_chunk_chars and len(buffer) >= min_chunk_chars:
                        chunks.append({
                            "module_name": mod_name,
                            "chunk_index": global_index,
                            "content": buffer.strip()
                        })
                        global_index += 1
                        buffer = sent
                    else:
                        buffer = f"{buffer} {sent}".strip() if buffer else sent

                if len(buffer) >= min_chunk_chars:
                    chunks.append({
                        "module_name": mod_name,
                        "chunk_index": global_index,
                        "content": buffer.strip()
                    })
                    global_index += 1
            elif len(sentences) > 1:
                # Group 1-2 sentences per chunk
                for sent in sentences:
                    if len(sent) >= min_chunk_chars:
                        chunks.append({
                            "module_name": mod_name,
                            "chunk_index": global_index,
                            "content": sent
                        })
                        global_index += 1
            else:
                chunks.append({
                    "module_name": mod_name,
                    "chunk_index": global_index,
                    "content": cleaned_para
                })
                global_index += 1

    return chunks
