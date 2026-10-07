# 02. 데이터베이스 모델 명세서 (02_database.md)

PostgreSQL 16 기반 Django ORM 데이터베이스 모델 설계입니다. (로컬 실습 환경에서는 기본 SQLite3로도 100% 동일하게 동작하도록 설계)

---

## 1. ERD 테이블 구조 요약

```
[ Team ] 1 ----- N [ User ]
                       |
                       +-- (manager) -- 1 ----- N [ Evaluation ] 1 ----- N [ EvaluationScore ]
                       |                               |                              |
                       +-- (employee) - 1 -------------+                              |
                                                                                      |
[ EvaluationItem ] 1 -----------------------------------------------------------------+
```

---

## 2. 테이블별 필드 정의

### (1) `Team` (팀 정보)
| 필드명 | 데이터 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `id` | AutoField / BigAutoField | Primary Key | 팀 고유 ID |
| `name` | CharField(100) | Unique | 팀 이름 (예: 개발팀, 마케팅팀) |
| `bonus_score` | IntegerField | Default=0, Min=0, Max=10 | 관리자가 부여하는 팀 보너스 점수 |

---

### (2) `User` (사용자 계정)
- `AbstractUser` 또는 커스텀 유저 모델 기반.
- 로그인 식별자로 기본 username 대신 **`employee_id`(사번)**를 사용.

| 필드명 | 데이터 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `id` | AutoField | Primary Key | 사용자 고유 ID |
| `employee_id` | CharField(50) | Unique, Index | 사번 (예: ADMIN, M001, E001) |
| `name` | CharField(100) | Not Null | 직원 이름 |
| `password` | CharField(128) | Encrypted | 해시 처리된 비밀번호 |
| `role` | CharField(20) | Choices: `ADMIN`, `MANAGER`, `EMPLOYEE` | 사용자 역할 (기본값: `EMPLOYEE`) |
| `team` | ForeignKey(Team) | Nullable (관리자는 null) | 소속 팀 (on_delete=models.SET_NULL) |

---

### (3) `EvaluationItem` (평가 항목)
| 필드명 | 데이터 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `id` | AutoField | Primary Key | 항목 고유 ID |
| `title` | CharField(200) | Not Null | 평가 항목명 (예: 업무 성과, 협업 태도) |
| `weight` | IntegerField | Min=1, Max=100 | 평가 가중치 (%) |
| `is_active` | BooleanField | Default=True | 활성화 여부 |
| `created_at` | DateTimeField | auto_now_add=True | 생성일시 |

> **비즈니스 규칙:** `is_active=True`인 항목들의 `weight` 합산은 반드시 100이어야 함.

---

### (4) `Evaluation` (평가 마스터)
| 필드명 | 데이터 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `id` | AutoField | Primary Key | 평가 고유 ID |
| `manager` | ForeignKey(User) | Related: `manager_evaluations` | 평가를 진행한 매니저 |
| `employee` | ForeignKey(User) | Related: `employee_evaluations` | 평가 대상 직원 |
| `status` | CharField(20) | Choices: `DRAFT`, `SUBMITTED` | 진행 상태 (임시저장 / 최종제출) |
| `submitted_at`| DateTimeField | Nullable | 최종 제출 일시 |
| `updated_at`  | DateTimeField | auto_now=True | 최근 수정 일시 |

> **중복 방지 제약 조건:** `unique_together = ('manager', 'employee')` (한 매니저는 한 직원에 대해 1개의 평가만 생성 가능)

---

### (5) `EvaluationScore` (항목별 점수)
| 필드명 | 데이터 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `id` | AutoField | Primary Key | 점수 고유 ID |
| `evaluation` | ForeignKey(Evaluation) | on_delete=CASCADE, Related: `scores` | 연결된 평가 마스터 |
| `item` | ForeignKey(EvaluationItem) | on_delete=PROTECT | 평가 항목 |
| `score` | IntegerField | Min=1, Max=5 | 부여한 점수 (1~5점) |

> **제약 조건:** `unique_together = ('evaluation', 'item')` (한 평가 내에서 동일 항목 중복 점수 방지)

