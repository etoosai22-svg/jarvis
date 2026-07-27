# 다음 세션 인수인계

**기준일: 2026-07-27** · 최신 커밋 `547bc7e` · CI green · 작업 트리 clean

---

## 1. 지금 어디까지 됐나

음성으로 말하면 → 인식하고 → 도구를 쓰고 → 위험한 건 승인받고 → 음성으로 답하는 **전 구간이 동작합니다.**

| Phase | 상태 |
|---|---|
| 1 기반 | 저장소·CI(3잡) 완료. 브랜치 보호 규칙·Lint 잡 미완 |
| 2 Backend | API·DB·Alembic 완료. **Redis 미사용** |
| 3 Frontend | 대화/작업/메모리 실데이터. **Home·Settings 일부 목업** |
| 4 Voice | STT·TTS·문장 스트리밍·앱 녹음까지 완료. **입력 스트리밍(말하는 중 인식) 미구현** |
| 5 MCP | 서버 5종 + 게이트웨이 완료. Booking 2차 |
| 6 AI | 오케스트레이터·응답 생성 완료. **메모리 회수는 키워드 ILIKE** (벡터 미도입) |
| 7 Security | JWT 검증·소유권·감사로그 완료. **IdP 연동·WS 인증·HTTPS 미착수** |
| 8 Testing | 백엔드 48 + MCP 37. **실 Postgres·E2E·성능 테스트 없음** |

상세 진행은 [PROGRESS.md](PROGRESS.md), 항목별 상태는 [docs/24_Project_Tasks.md](docs/24_Project_Tasks.md).

### 응답 속도 (실측, 좌표 캐시 상태)

| 턴 | 첫 소리 | 전체 |
|---|---|---|
| 순수 대화 | 2.4~2.6초 | 3.4~3.7초 |
| 도구 사용 | 2.5~5.3초 | 7.2~9.1초 |

시작점은 14.5초였습니다. 남은 지연은 도구 실행(날씨 API 왕복 ~2초)과 응답 생성입니다.

---

## 2. 실행 방법 (검증됨)

터미널 두 개:

```bash
cd ~/JARVIS/backend && uv run uvicorn app.main:app --port 8100
```

```bash
cd ~/JARVIS/frontend && EXPO_PUBLIC_API_BASE_URL=http://localhost:8100 npx expo start --web --port 8081
```

브라우저에서 `localhost:8081` → 오브를 눌러 녹음 시작, 다시 눌러 전송.

**포트가 중요합니다:**
- `8100` — 기본값 8000은 **Claude 데스크톱 앱**이 점유 중
- `8081` — 백엔드 CORS 허용 목록에 있는 포트 (바꾸면 브라우저가 차단)
- `EXPO_PUBLIC_API_BASE_URL` 없으면 앱이 8000을 바라봄

---

## 3. 이 환경의 함정 (모르면 시간 낭비함)

| 항목 | 내용 |
|---|---|
| **LLM** | openclaw Bedrock 게이트웨이(`127.0.0.1:8091`) 의존. **꺼져 있으면** 규칙 라우터로 폴백해 자유 대화가 정해진 문구만 나옴 |
| **OpenAI 키 없음** | 음성은 온디바이스(faster-whisper + macOS `say`). `VOICE_PROVIDER=auto`가 알아서 고름 |
| **Xcode 없음** | Command Line Tools만 있어 **iOS 시뮬레이터 불가**. 앱 검증은 Expo 웹으로 |
| **인앱 브라우저 마이크 차단** | Claude 브라우저 패널에서는 마이크가 막힘. **사용자 본인 Chrome**에서 테스트해야 함 |
| **자동화 클릭** | `left_click`이 PointerEvent를 안 보내 react-native-web `Pressable`이 반응 안 함. 검증하려면 `pointerdown`/`pointerup`을 직접 dispatch |
| **테스트 격리** | `.env`가 실제 Bedrock을 가리키므로 `conftest.py`가 LLM·음성을 명시적으로 끔. 이걸 지우면 테스트가 실제 API를 호출함(스위트 0.7초 → 133초) |
| **`.env`** | gitignore됨. Bedrock 키가 들어 있음 |

---

## 4. 다음에 할 만한 것 (우선순위 순)

1. **실기기 테스트** — Expo Go로 iOS/Android 네이티브 녹음·재생 확인.
   웹 경로는 검증됐지만 네이티브 녹음 코드는 타입체크만 통과한 상태.
   `EXPO_PUBLIC_API_BASE_URL=http://<개발PC-LAN-IP>:8100`
2. **Phase 7 보안** — WS 인증(현재 무인증), IdP 연동, HTTPS
3. **Home·Settings 목업 제거** — 일정·최근대화·연동상태가 아직 하드코딩
4. **응답 속도** — 날씨 예보 캐시, 선행 문장 유도 프롬프트
5. **메모리 벡터 검색** — `embedding_id` 컬럼과 `/memory/search` 계약은 이미 준비됨

---

## 5. 알려진 한계 (숨기지 말 것)

- **말하는 중 실시간 인식 없음** — 발화가 끝나야 처리 시작
- **인터럽션 불가** — 답하는 중 끼어들기는 현재 구조로 안 됨 (LiveKit/pipecat 영역)
- **Haiku가 길이 지침을 덜 지킴** — 2~3문장 요청에 가끔 5문장. 되돌리려면 `.env`의 `LLM_VOICE_MODEL` 삭제
- **calendar·notes는 로컬 sqlite** — Google 연동 전 임시 스토어 (도구 인터페이스는 유지됨)
- **weather 특보는 항상 빈 목록** — Open-Meteo가 제공 안 함
- **실 Postgres 미검증** — compose 구성만 있고 실제로 띄워본 적 없음

---

## 6. 작업 규칙 (이 저장소의 약속)

- **`~/JARVIS` 하나만 쓴다.** 워크스페이스별 사본을 만들면 예전처럼 갈라짐
- **계약 문서가 코드보다 우선.** 동작을 바꾸려면 [docs/09](docs/09_API_Spec.md)·[13](docs/13_Database_Schema.md)을 먼저 고친다
- **문서에 없는 걸 구현해야 하면 문서를 먼저 고친다.** 발명 후 미기록이 과거 드리프트의 주원인
- 수용 기준은 [docs/18](docs/18_Testing_Strategy.md) §1
