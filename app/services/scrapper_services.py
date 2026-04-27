import re
from bs4 import BeautifulSoup
import httpx
import requests

from app.database import SessionLocal
from app.services.text_extractor import chunks_text

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def clean_text(text):

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def scrape_url(url: str):

    
    

    try:

        # STEP 1 → fetch page
        response = httpx.get(
            url,
            headers={**HEADERS, "Referer": url},
            follow_redirects=True,
            timeout=30
        )

        if response.status_code == 403:
            response = requests.get(
                url,
                headers={**HEADERS, "Referer": url},
                timeout=30
            )

        if response.status_code != 200:
            return {
                "error": f"Failed with status {response.status_code}"
            }

        # STEP 2 → parse html
        soup = BeautifulSoup(response.text, "lxml")

        # STEP 3 → remove useless tags
        remove_tags = [
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "noscript"
        ]

        for tag in remove_tags:
            for element in soup.find_all(tag):
                element.decompose()

        # STEP 4 → extract title
        title = ""

        if soup.title:
            title = soup.title.get_text(strip=True)

        # STEP 5 → meta description
        description = ""

        desc = soup.find(
            "meta",
            attrs={"name": "description"}
        )

        if desc:
            description = desc.get("content", "")

        # STEP 6 → author
        author = ""

        author_meta = soup.find(
            "meta",
            attrs={"name": "author"}
        )

        if author_meta:
            author = author_meta.get("content", "")

        # STEP 7 → extract useful text
        content = []

        for tag in soup.find_all([
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "p",
            "li"
        ]):

            text = tag.get_text(" ", strip=True)

            if text:
                content.append(text)

        full_text = "\n".join(content)

        # STEP 8 → clean text
        full_text = clean_text(full_text)

        return {
            "url": url,
            "title": title,
            "author": author,
            "description": description,
            "content": full_text
        }

    except httpx.TimeoutException:

        return {
            "error": "Request timeout"
        }

    except Exception as e:

        return {
            "error": str(e)
        }





from datetime import datetime, timedelta
from app.models.document import Document
from app.models.document_chunks import DocumentChunk
from app.models.url_sources import UrlSources
from app.services.embeddings import (
    generate_embedding_batch
)




def ingest_url_pipeline(
    url: str,
    db,
    custom_title=None
):

    existing = db.query(Document).filter(
        Document.source_url == url
    ).first()

    scraped = scrape_url(url)

    if not scraped or scraped.get("error"):
        error_message = scraped.get("error") if scraped else "Unknown scraping error"
        raise ValueError(f"Failed to scrape URL '{url}': {error_message}")

    content = scraped.get("content", "")
    if not content:
        raise ValueError(f"No content was extracted from URL '{url}'")

    title = custom_title or scraped.get("title")

    chunks = chunks_text(content)

    embeddings = generate_embedding_batch(chunks)

    # duplicate url
    if existing:

        existing.content = content
        existing.title = title

        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == existing.id
        ).delete()

        db.commit()

        document = existing

    else:

        document = Document(
            title=title,
            content=content,
            source_url=url
        )

        db.add(document)
        db.commit()
        db.refresh(document)

    chunk_data = []

    for i, chunk in enumerate(chunks):

        chunk_data.append({
            "document_id": document.id,
            "chunk_text": chunk,
            "chunk_index": i,
            "embedding": embeddings[i]
        })

    db.bulk_insert_mappings(
        DocumentChunk,
        chunk_data
    )

    db.commit()

    url_source = db.query(UrlSources).filter(
        UrlSources.url == url
    ).first()

    if not url_source:

        url_source = UrlSources(
            url=url
        )

        db.add(url_source)

    url_source.last_scraped_at = datetime.utcnow()

    url_source.scrape_status = "success"

    url_source.next_scrape_at = (
        datetime.utcnow() + timedelta(hours=24)
    )

    db.commit()

    return document






from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

def auto_refresh_urls():

    db = SessionLocal()

    try:

        urls = db.query(
            UrlSources
        ).all()

        for source in urls:

            print(
                f"Refreshing: {source.url}"
            )

            ingest_url_pipeline(
                source.url,
                db
            )

    finally:

        db.close()


scheduler.add_job(
    auto_refresh_urls,
    "interval",
    hours=24,
)