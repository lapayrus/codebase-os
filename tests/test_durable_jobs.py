from codebase_os.providers.webhooks import DurableIngestionQueue, IngestionJob
from codebase_os.storage.memory import InMemoryStore


def test_durable_queue_deduplicates_delivery_and_tracks_completion():
    store = InMemoryStore()
    queue = DurableIngestionQueue(store)
    job = IngestionJob("delivery-1", 7, "acme/demo", "push")
    assert queue.enqueue(job)
    assert not queue.enqueue(job)
    claimed = queue.claim()
    assert claimed == job
    queue.complete(job.delivery_id, job.repository_id)
    assert queue.claim() is None


def test_durable_queue_releases_failed_job_for_retry():
    store = InMemoryStore()
    queue = DurableIngestionQueue(store)
    job = IngestionJob("delivery-2", 7, "acme/demo", "push")
    queue.enqueue(job)
    assert queue.claim() == job
    queue.fail(job.delivery_id, job.repository_id)
    assert queue.claim() == job
