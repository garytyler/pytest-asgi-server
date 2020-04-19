import httpx


def test_server_thread_is_alive(server_thread):
    server_thread(limit_max_requests=0, lifespan=False)
    assert server_thread.is_alive() is False
    server_thread.start()
    assert server_thread.is_alive() is True
    server_thread.stop()
    assert server_thread.is_alive() is False


def test_server_thread_context_manager(server_thread):
    server_thread(limit_max_requests=0, lifespan=False)
    assert server_thread.is_alive() is False
    with server_thread:
        assert server_thread.is_alive() is True
    assert server_thread.is_alive() is False


def test_server_thread_http_request(server_thread):
    with server_thread(limit_max_requests=1, lifespan=False) as server:
        resp = httpx.get(server.http_base_url + "/api")
        assert resp.status_code == 200


def test_server_thread_factory_http_requests_to_many_servers(server_thread_factory):
    server_threads = [
        server_thread_factory(limit_max_requests=1, lifespan=False) for n in range(3)
    ]
    with server_threads[0]:
        with server_threads[1]:
            with server_threads[2]:
                resp = httpx.get(server_threads[2].http_base_url + "/api")
                assert resp.status_code == 200
                resp = httpx.get(server_threads[1].http_base_url + "/api")
                assert resp.status_code == 200
                resp = httpx.get(server_threads[0].http_base_url + "/api")
                assert resp.status_code == 200
