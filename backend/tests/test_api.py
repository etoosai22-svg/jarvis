from fastapi.testclient import TestClient

from app.main import app


def test_chat_endpoint_returns_reply_and_actions():
    with TestClient(app) as client:
        response = client.post("/api/v1/chat", json={"session_id": "s1", "message": "회의 준비 작업 만들어줘"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["reply"].startswith("네, 실장님")
    assert payload["task_status"] == "completed"
    assert payload["actions"][0]["type"] == "task.created"


def test_voice_endpoint_accepts_upload_and_returns_transcript():
    with TestClient(app) as client:
        response = client.post("/api/v1/voice", files={"file": ("sample.wav", b"fake audio", "audio/wav")})
    assert response.status_code == 200
    payload = response.json()
    assert payload["transcript"]
    assert payload["intent"] in {"chat", "task"}


def test_tasks_crud():
    with TestClient(app) as client:
        create_response = client.post("/api/v1/tasks", json={"title": "테스트 작업", "description": "설명", "priority": 2})
        list_response = client.get("/api/v1/tasks")
    assert create_response.status_code == 201
    assert create_response.json()["title"] == "테스트 작업"
    assert list_response.status_code == 200
    assert any(item["title"] == "테스트 작업" for item in list_response.json())


def test_memory_crud_and_search():
    with TestClient(app) as client:
        create_response = client.post(
            "/api/v1/memory",
            json={"category": "preference", "title": "호칭", "content": "사용자를 실장님으로 부릅니다.", "tags": ["profile"]},
        )
        list_response = client.get("/api/v1/memory")
        search_response = client.post("/api/v1/memory/search", json={"query": "실장님"})
    assert create_response.status_code == 201
    assert create_response.json()["tags"] == ["profile"]
    assert list_response.status_code == 200
    assert any(item["title"] == "호칭" for item in list_response.json())
    assert search_response.status_code == 200
    assert len(search_response.json()) >= 1


def test_websocket_voice_flow():
    with TestClient(app) as client:
        with client.websocket_connect("/api/v1/ws/voice") as websocket:
            websocket.send_json({"type": "session.start", "session_id": "s1"})
            assert websocket.receive_json()["type"] == "task.started"
            websocket.send_json({"type": "audio.chunk", "audio": "ZmFrZQ=="})
            assert websocket.receive_json()["type"] == "transcript.partial"
            websocket.send_json({"type": "audio.end"})
            assert websocket.receive_json()["type"] == "transcript.final"
            assert websocket.receive_json()["type"] == "assistant.delta"
            assert websocket.receive_json()["type"] == "audio.output"
            assert websocket.receive_json()["type"] == "task.completed"
