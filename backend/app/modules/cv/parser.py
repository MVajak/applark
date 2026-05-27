from typing import cast

import pymupdf  # pyright: ignore[reportMissingTypeStubs]


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract plain text from PDF bytes using PyMuPDF.

    Reads entirely in-memory — never writes the PDF to disk.
    Pages are joined with double newlines so page boundaries survive
    as paragraph breaks for downstream chunking.
    """
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        pages: list[str] = [
            cast(str, page.get_text())  # pyright: ignore[reportUnknownMemberType]
            for page in doc
        ]
    return "\n\n".join(pages).strip()
