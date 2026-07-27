def test_chat_endpoint_returns_reply_and_actions(client):
    response = client.post("/api/v1/chat", json={"session_id": "s1", "message": "회의 준비 작업 만들어줘"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["reply"].startswith("네, 실장님")
    assert payload["task_status"] == "queued"
    assert payload["actions"][0]["type"] == "task.created"


def test_chat_without_task_keyword_stays_completed(client):
    response = client.post("/api/v1/chat", json={"session_id": "s-plain", "message": "안녕"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["task_status"] == "completed"
    assert payload["actions"] == []


def test_chat_created_task_appears_in_task_list(client):
    message = "내일 회의 자료 정리해 줘"
    chat_response = client.post("/api/v1/chat", json={"session_id": "s-task", "message": message})
    task_id = chat_response.json()["actions"][0]["task_id"]

    tasks = client.get("/api/v1/tasks").json()
    assert any(task["id"] == task_id and task["title"] == message for task in tasks)


def test_voice_endpoint_accepts_upload_and_returns_transcript(client):
    response = client.post("/api/v1/voice", files={"file": ("sample.wav", b"fake audio", "audio/wav")})
    assert response.status_code == 200
    payload = response.json()
    assert payload["transcript"]
    assert payload["intent"] in {"chat", "task"}


def test_tasks_crud(client):
    create_response = client.post("/api/v1/tasks", json={"title": "테스트 작업", "description": "설명", "priority": 2})
    assert create_response.status_code == 201
    assert create_response.json()["title"] == "테스트 작업"

    task_id = create_response.json()["id"]
    patch_response = client.patch(f"/api/v1/tasks/{task_id}", params={"status_value": "completed"})
    assert patch_response.status_code == 200
    assert patch_response.json()["completed_at"] is not None

    list_response = client.get("/api/v1/tasks")
    assert list_response.status_code == 200
    assert any(item["title"] == "테스트 작업" for item in list_response.json())


def test_task_patch_rejects_unknown_status(client):
    task_id = client.post("/api/v1/tasks", json={"title": "상태 검증"}).json()["id"]
    response = client.patch(f"/api/v1/tasks/{task_id}", params={"status_value": "made_up"})
    assert response.status_code == 400


def test_task_patch_returns_404_for_missing_task(client):
    response = client.patch("/api/v1/tasks/does-not-exist", params={"status_value": "running"})
    assert response.status_code == 404


def test_memory_crud_and_search(client):
    create_response = client.post(
        "/api/v1/memory",
        json={"category": "preference", "title": "호칭", "content": "사용자를 실장님으로 부릅니다.", "tags": ["profile"]},
    )
    assert create_response.status_code == 201
    assert create_response.json()["tags"] == ["profile"]

    list_response = client.get("/api/v1/memory")
    assert list_response.status_code == 200
    assert any(item["title"] == "호칭" for item in list_response.json())

    search_response = client.post("/api/v1/memory/search", json={"query": "실장님"})
    assert search_response.status_code == 200
    assert len(search_response.json()) >= 1


def test_memory_tags_preserve_commas(client):
    response = client.post(
        "/api/v1/memory",
        json={"content": "쉼표 포함 태그", "tags": ["회의, 자료", "일정"]},
    )
    assert response.status_code == 201
    assert response.json()["tags"] == ["회의, 자료", "일정"]


def test_task_and_memory_lists_are_scoped_to_the_caller(client):
    """user_id는 클라이언트가 아니라 인증 주체에서 온다."""
    created = client.post("/api/v1/tasks", json={"title": "소유권 확인", "user_id": "someone-else"})
    assert created.status_code == 201
    # 요청 본문의 user_id는 무시되고 현재 사용자로 저장된다.
    assert created.json()["user_id"] == "local-user"


def test_websocket_voice_flow(client):
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
