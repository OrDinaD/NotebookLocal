from ingestion.chunking import chunk_text


def test_chunk_text_small():
    text = "short text"
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert chunks == ["short text"]


def test_chunk_text_overlap():
    text = "a" * 120
    chunks = chunk_text(text, chunk_size=50, overlap=10)
    assert len(chunks) >= 3
    assert all(len(c) <= 50 for c in chunks)
