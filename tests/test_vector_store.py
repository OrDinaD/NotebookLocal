from models.schemas import Modality, VectorRecord
from storage.in_memory_store import InMemoryVectorStore


def test_inmemory_upsert_and_search():
    store = InMemoryVectorStore()
    store.upsert(
        [
            VectorRecord(
                id="1",
                source_uri="a",
                modality=Modality.text,
                text="alpha",
                embedding=[1.0, 0.0, 0.0],
                metadata={"type": "doc"},
            ),
            VectorRecord(
                id="2",
                source_uri="b",
                modality=Modality.image,
                text="beta",
                embedding=[0.0, 1.0, 0.0],
                metadata={"type": "img"},
                image_uri="/tmp/x.png",
            ),
            VectorRecord(
                id="3",
                source_uri="c",
                modality=Modality.audio,
                text="gamma",
                embedding=[0.0, 0.0, 1.0],
                metadata={"type": "media"},
            ),
        ]
    )
    hits = store.search([1.0, 0.0, 0.0], top_k=2)
    assert len(hits) == 2
    assert hits[0].id == "1"

    filtered = store.search([0.0, 1.0, 0.0], top_k=3, filters={"type": "img"})
    assert len(filtered) == 1
    assert filtered[0].image_uri == "/tmp/x.png"
