import re
from langchain_core.documents import Document
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from pypdf import PdfReader

_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

# Remove null bytes and control characters (keep \n \r \t and printable chars)
_CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')


def _sanitize(text: str) -> str:
    return _CTRL.sub('', str(text)).strip()


def _clean(chunks: list) -> list:
    result = []
    for c in chunks:
        text = _sanitize(c.page_content)
        if len(text) >= 10:
            c.page_content = text
            result.append(c)
    return result


def load_pdf(file_path: str) -> list:
    reader = PdfReader(file_path)
    docs = []
    for i, page in enumerate(reader.pages):
        text = _sanitize(page.extract_text() or "")
        if text:
            docs.append(Document(
                page_content=text,
                metadata={"source": file_path, "page": i + 1},
            ))
    return _clean(_splitter.split_documents(docs))


def load_website(url: str) -> list:
    docs = WebBaseLoader(url).load()
    return _clean(_splitter.split_documents(docs))
