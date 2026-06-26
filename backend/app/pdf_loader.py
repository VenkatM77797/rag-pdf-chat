from pathlib import Path

import fitz


def load_pdf_text(
    path: str | Path,
) -> str:
    """
    Extract selectable text from every PDF page.
    """
    pdf_path = Path(path)

    if not pdf_path.is_file():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    page_texts: list[str] = []

    with fitz.open(pdf_path) as document:
        if document.page_count == 0:
            raise ValueError(
                "The PDF contains no pages."
            )

        for page in document:
            page_text = page.get_text(
                "text"
            ).strip()

            if page_text:
                page_texts.append(
                    page_text
                )

    extracted_text = "\n\n".join(
        page_texts
    ).strip()

    if not extracted_text:
        raise ValueError(
            "No readable text was found in the PDF. "
            "The document may contain scanned images "
            "instead of selectable text."
        )

    return extracted_text