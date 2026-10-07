# 03. REST API 명세서 (03_api.md)

Django REST Framework (DRF) 기반의 심플하고 직관적인 API 엔드포인트 명세입니다.

---

## 1. 인증 및 사용자 정보

### `POST /api/auth/login/`
- **설명:** 사번과 비밀번호로 로그인
- **요청 Body:**
  ```json
  {
    "employee_id": "ADMIN",
    "password": "admin1234!"
  }
  ```
- **응답 (성공 200):**
  ```json
  {
    "token": "session_or_jwt_token",
    "user": {
      "id": 1,
      "employee_id": "ADMIN",
      "name": "최고관리자",
      "role": "ADMIN",
      "team": null
    }
  }
  ```

### `GET /api/auth/me/`
- **설명:** 현재 로그인한 사용자 정보 반환

---

## 2. 관리자(`ADMIN`) 전용 API

### 팀 관리
- `GET /api/teams/`: 팀 목록 조회 (보너스 점수 포함)
- `POST /api/teams/`: 신규 팀 생성 (`{"name": "개발팀", "bonus_score": 0}`)
- `PATCH /api/teams/<id>/`: 팀 이름 또는 팀 보너스 점수(0~10) 수정
- `DELETE /api/teams/<id>/`: 팀 삭제

### 사용자 관리
- `GET /api/users/`: 전체 사용자 목록 조회
- `POST /api/users/`: 사용자 추가 (`employee_id`, `name`, `password`, `role`, `team_id`)
- `PATCH /api/users/<id>/`: 사용자 정보 수정
- `DELETE /api/users/<id>/`: 사용자 삭제

### 평가 항목 관리
- `GET /api/items/`: 평가 항목 목록 및 현재 활성화된 가중치 총합 반환
- `POST /api/items/`: 평가 항목 추가 (`title`, `weight`)
- `PATCH /api/items/<id>/`: 평가 항목 수정
- `DELETE /api/items/<id>/`: 평가 항목 삭제

### 결과 및 현황 관리
- `GET /api/admin/results/`: 전체 직원의 개인 점수, 팀 보너스, 최종 점수 및 제출 현황 조회
- `GET /api/admin/results/export-csv/`: 엑셀 호환 CSV 파일 다운로드

---

## 3. 매니저(`MANAGER`) 전용 API

### `GET /api/manager/targets/`
- **설명:** 매니저 본인과 동일한 팀에 속한 평가 대상 직원 목록 및 진행률 반환
- **응답:**
  ```json
  {
    "total_count": 5,
    "completed_count": 3,
    "progress_rate": 60.0,
    "targets": [
      {
        "employee_id": "E001",
        "name": "김직원",
        "status": "SUBMITTED",
        "is_editable": false
      },
      {
        "employee_id": "E002",
        "name": "이직원",
        "status": "DRAFT",
        "is_editable": true
      }
    ]
  }
  ```

### `GET /api/manager/evaluations/<employee_id>/`
- **설명:** 특정 직원의 현재 평가 작성 내용(항목별 점수) 조회

### `POST /api/manager/evaluations/<employee_id>/save/`
- **설명:** 평가 내용 **임시 저장 (`DRAFT`)**
- **요청 Body:**
  ```json
  {
    "scores": [
      {"item_id": 1, "score": 4},
      {"item_id": 2, "score": 5}
    ]
  }
  ```

### `POST /api/manager/evaluations/<employee_id>/submit/`
- **설명:** 평가 내용 **최종 제출 (`SUBMITTED`)** — 제출 후 수정 불가

---

## 4. 직원(`EMPLOYEE`) 전용 API

### `GET /api/employee/result/`
- **설명:** 로그인한 직원 본인의 최종 점수 조회
- **응답:**
  ```json
  {
    "is_evaluated": true,
    "personal_score": 82.0,
    "team_bonus": 5,
    "final_score": 87.0,
    "team_name": "개발팀",
    "submitted_at": "2026-09-28T14:00:00"
  }
  ```

