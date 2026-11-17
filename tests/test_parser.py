"""Tests for HTML parsing, text cleaning, and malformed document handling."""

from archimind.ingestion.parser import DocumentParser


def test_html_cleaning_and_tag_stripping():
    """Verify that script, style, nav, and footer elements are thoroughly stripped."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Redis Architecture</title>
        <script>console.log("malicious code");</script>
        <style>body { color: red; }</style>
    </head>
    <body>
        <nav><a href="/home">Home</a></nav>
        <h1>Redis Architecture Overview</h1>
        <p>Redis is an in-memory data structure store.</p>
        <h2>Persistence</h2>
        <p>Redis supports RDB snapshots and AOF persistence.</p>
        <footer>Copyright 2026</footer>
    </body>
    </html>
    """
    parser = DocumentParser()
    parsed = parser.parse(
        raw_content=html_content,
        url="https://redis.io/docs",
        fallback_title="Redis Docs",
        domain="redis.io",
    )

    assert parsed.title == "Redis Architecture"
    assert parsed.source_domain == "redis.io"

    # Confirm stripped tags do not appear in text
    all_text = " ".join([s.text for s in parsed.sections])
    assert "malicious code" not in all_text
    assert "color: red" not in all_text
    assert "Copyright 2026" not in all_text
    assert "in-memory data structure store" in all_text


def test_malformed_html_handling():
    """Verify parser robustness against unclosed tags, broken markup, and special characters."""
    malformed_html = """
    <html><body>
    <h2>Broken Heading Without Closing
    <p>This is a paragraph with an unclosed <b>bold tag and broken entities &amp &gt
    <div>Some text inside unclosed div
    <script>alert('xss');
    """
    parser = DocumentParser()
    parsed = parser.parse(
        raw_content=malformed_html,
        url="https://example.com/broken",
        fallback_title="Fallback Title",
        domain="example.com",
    )

    assert parsed is not None
    assert parsed.title == "Fallback Title"
    assert len(parsed.sections) > 0
    all_text = " ".join([s.text for s in parsed.sections])
    assert "paragraph with an unclosed" in all_text
    assert "alert('xss')" not in all_text


def test_plain_text_fallback():
    """Verify that plain text documents without HTML markup are parsed correctly."""
    plain_text = (
        "Envoy proxy threading model is based on an event-driven loop. "
        "Each worker thread binds to an event loop using libevent."
    )
    parser = DocumentParser()
    parsed = parser.parse(
        raw_content=plain_text,
        url="https://www.envoyproxy.io/plain",
        fallback_title="Envoy Plain Text",
        domain="www.envoyproxy.io",
    )

    assert parsed.title == "Envoy Plain Text"
    assert len(parsed.sections) == 1
    assert "Envoy proxy threading model" in parsed.sections[0].text
