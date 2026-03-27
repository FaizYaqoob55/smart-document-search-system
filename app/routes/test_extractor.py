from app.services.text_extractor import extract_text_from_pdf, chunks_text


file_path = "sample.pdf"
text = extract_text_from_pdf(file_path)

print("Extracted Text:\n", text[:500])  # Print the first 500 characters of the extracted text

chunks=chunks_text(text)
print("\nTotal Chunks:", len(chunks))
print("\nFirst Chunk:\n", chunks[0])  # Print the first chunk of text
