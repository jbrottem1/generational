from core.jobs import JobStatus


def test_submit_and_run_job(job_queue):
    job_queue.register_handler("echo", lambda payload: {"echo": payload["value"]})
    job = job_queue.submit("echo", {"value": 42})
    assert job.status == JobStatus.PENDING

    finished = job_queue.run(job.id)
    assert finished.status == JobStatus.SUCCEEDED
    assert finished.result == {"echo": 42}
    assert finished.started_at and finished.finished_at


def test_run_next_processes_fifo(job_queue):
    order = []
    job_queue.register_handler("track", lambda payload: order.append(payload["n"]) or {})
    job_queue.submit("track", {"n": 1})
    job_queue.submit("track", {"n": 2})

    job_queue.run_next()
    job_queue.run_next()
    assert order == [1, 2]
    assert job_queue.run_next() is None


def test_handler_exception_marks_job_failed(job_queue):
    def boom(payload):
        raise RuntimeError("kaput")

    job_queue.register_handler("boom", boom)
    job = job_queue.run(job_queue.submit("boom", {}).id)
    assert job.status == JobStatus.FAILED
    assert "kaput" in job.error


def test_missing_handler_fails_gracefully(job_queue):
    job = job_queue.run(job_queue.submit("nope", {}).id)
    assert job.status == JobStatus.FAILED
    assert "No handler" in job.error


def test_stats_counts(job_queue):
    job_queue.register_handler("ok", lambda payload: {})
    job_queue.run(job_queue.submit("ok", {}).id)
    job_queue.submit("ok", {})
    stats = job_queue.stats()
    assert stats["succeeded"] == 1
    assert stats["pending"] == 1
    assert stats["total"] == 2
