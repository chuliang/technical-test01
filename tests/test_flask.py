
def test_health(app, config):
    test_client = app.test_client()

    resp = test_client.get('/health')

    assert resp.status_code == 200
    assert resp.data.decode('utf-8') == config.get('HEALTHY_MESSAGE')
