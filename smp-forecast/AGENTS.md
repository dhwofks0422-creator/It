# SMP 예측 실습 프로젝트

경영학부 학부생 대상 실습입니다. 사용자는 **프로그래밍 비전공자**입니다.
설명은 한국어로, 전문용어는 쉬운 말을 함께 적어 주세요.

---

## 🚫 0. 작업 범위 제한 (가장 중요 — 반드시 지킬 것)

- **이 프로젝트 폴더 안에서만 파일을 읽고 씁니다.**
- 상위 폴더(`../`), 홈 디렉터리(`~`), 바탕화면, 문서 폴더, 시스템 폴더 등
  **프로젝트 폴더 밖의 어떤 경로에도 접근하지 않습니다.**
- 절대 경로(`C:\`, `/Users/...`, `/home/...`)를 사용하지 않습니다.
  파일은 **항상 상대 경로**로만 지정합니다. (예: `smp_hourly.csv`, `plots/01.png`)
- 프로젝트 폴더 밖의 파일이 필요해 보이면, **직접 찾지 말고 사용자에게 물어봅니다.**
- 파일 삭제는 하지 않습니다. 필요하면 사용자에게 먼저 확인받습니다.
- `pip install` 등 설치 명령은 **반드시 먼저 물어보고** 실행합니다.

---

## 1. 데이터

- 파일: `smp_hourly.csv` (프로젝트 루트)
- 컬럼: `datetime`(YYYY-MM-DD HH:00), `smp`(시간별 SMP, 원/kWh)
- 기간: 2023-01-01 00시 ~ 2025-12-31 23시 = **26,304시간** (1,096일 × 24시간)
- 결측 없음. 인코딩은 UTF-8(BOM)이라 `encoding` 지정 없이 읽으면 됩니다.
- 이번 주차는 **SMP 하나만** 예측 입력으로 씁니다. 외부 데이터는 쓰지 않습니다.
  (전력수요·기온 같은 외부 변수는 추가 분석(05_multivar.py)과 3주차에서 다룹니다)

## 2. 예측 과제 (항상 이 설정을 씁니다)

우리 전력시장은 **하루전시장**입니다. 하루 전에 다음 날 24시간의 가격이
1시간 단위로 결정됩니다. 그래서 실습도 이 구조를 따릅니다.

| 항목 | 값 | 변수명 |
|---|---|---|
| 입력 | 과거 **96시간**(4일) | `LAG = 96` |
| 예측 | **24시간 뒤** (내일 같은 시각) | `HORIZON = 24` |
| 달력 정보 | 예측 대상 시점의 **시간(0~23)** 과 **요일(0~6)** | 아래 참조 |
| 테스트 | 마지막 **60일** = 1,440시간 | `TEST = 24 * 60` |
| 학습 | 그 이전 전부 (약 24,700개) | |

- **학습/테스트 분리는 시간 순서를 지킵니다. 절대 랜덤 셔플하지 않습니다.**
- 비교 기준선으로 **"어제 같은 시각의 값을 그대로 쓰기"(나이브)** 를 항상 함께 계산합니다.
- 평가지표는 **MAE, RMSE, MAPE** 세 개와 **기준선 대비 개선율(%)** 을 함께 출력합니다.

### 달력 정보(시간·요일) 만드는 법

시간과 요일은 **순환하는 값**이라 그냥 숫자로 넣으면 안 됩니다.
(23시와 0시는 붙어 있는데 숫자로는 가장 멀기 때문)
sin/cos 두 개로 바꿔서 넣습니다.

```python
g = 예측대상시점            # pandas Timestamp
sin_h, cos_h = np.sin(2*np.pi*g.hour/24),      np.cos(2*np.pi*g.hour/24)
sin_d, cos_d = np.sin(2*np.pi*g.dayofweek/7),  np.cos(2*np.pi*g.dayofweek/7)
```

### MAPE 주의

데이터에 SMP가 **0원인 시간이 25개** 있습니다(태양광 과잉공급).
0으로 나누면 무한대가 되므로 **실제값이 1원을 넘는 행만** 계산합니다.

```python
m = 실제 > 1
mape = np.mean(np.abs((실제[m] - 예측[m]) / 실제[m])) * 100
```


## 2-1. 추가 분석 — 외부 데이터를 넣을 때 (05_multivar.py 를 만들 때만)

기본 실습(00~04)은 SMP 하나만 씁니다. 추가 분석 단계에서만 아래를 적용합니다.

- 파일: `smp_features.csv` (26,304행, UTF-8 BOM)

| 컬럼 | 내용 | 모델 입력 |
|---|---|---|
| `smp` | 시간별 SMP (원/kWh) | **예측 대상** |
| `fcst` | 하루전 수요예측 (MW) — 전력거래소가 하루 전에 발표 | **사용 가능** |
| `demand` | 전력수요 실적 (MW) | ❌ 사용 금지 |
| `temp` | 서울 기온 (°C) | ❌ 사용 금지 |
| `solar` | 서울 일사 (MJ/m²) | ❌ 사용 금지 |

**`demand`, `temp`, `solar` 는 모델 입력으로 쓰지 않습니다.**
내일의 실측값은 내일이 되어야 알 수 있기 때문입니다(데이터 누수).
비교·설명 목적으로 한 번 넣어볼 때는 반드시 "반칙"이라고 표시합니다.

## 3. 코드 작성 규칙

1. **모든 주석과 출력 메시지는 한국어**로 작성합니다.
2. 코드는 반드시 아래 **4개 섹션**으로 나누고, 각 섹션 앞에 구분 주석을 넣습니다.

```python
# ============================================================
# [1] 데이터 준비
# ============================================================
# ============================================================
# [2] 모델 학습
# ============================================================
# ============================================================
# [3] 예측
# ============================================================
# ============================================================
# [4] 평가 및 시각화
# ============================================================
```

3. 웹 배포, API 서버, Flask, FastAPI, Streamlit 코드는 **절대 만들지 않습니다.**
4. 파일을 새로 만들 때는 기존 파일을 최대한 그대로 두고 **바뀐 부분이 잘 보이게** 합니다.

## 4. 파일 인코딩

- `smp_hourly.csv` 는 UTF-8(BOM)이라 그냥 읽으면 됩니다.
- 사용자가 **공공데이터포털·EPSIS에서 직접 받은 CSV는 대부분 CP949**입니다.
  한글이 깨지거나 `UnicodeDecodeError` 가 나면 `encoding='cp949'` 로 다시 읽습니다.
- 새로 CSV를 저장할 때는 **항상 `encoding='utf-8-sig'`** 를 씁니다.
- 사용자가 "한글이 깨진다"고 하면 CP949로 다시 읽어보고
  **UTF-8(BOM) 사본을 만들어 주는 것**을 제안합니다.

## 5. 코드 실행 방식

- 코드는 **터미널에서 `python 파일이름.py` 로 파일 전체를 한 번에 실행**합니다.
  (VS Code 편집기 오른쪽 위 ▷ 버튼도 같은 일을 합니다)
- `# %%` 같은 셀 구분 표시나 Jupyter Notebook(.ipynb)은 **쓰지 않습니다.** 순수 `.py` 파일만 만듭니다.
- 실행 결과(표·숫자)는 `print()` 로 터미널에 출력하고, 그래프는 파일로 저장한 뒤 마지막에 `plt.show()` 로 창을 띄웁니다.
- 사용자가 "실행해줘"라고 하면 터미널에서 실행하고 **출력을 그대로 보여준 뒤** 한국어로 설명합니다.

## 6. 그래프 규칙

```python
import matplotlib.pyplot as plt, platform
plt.rcParams['font.family'] = 'Malgun Gothic' if platform.system()=='Windows' else 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False
```

- **PNG 저장을 먼저** 하고(`plots/` 폴더), 그 다음 `plt.show()` 로 창을 띄웁니다. 창은 프로그램 끝에 한 번만 띄웁니다.
- 테스트 구간이 1,440시간이라 전체를 그리면 뭉개집니다.
  **마지막 7일(168시간)만 확대한 그래프**를 함께 그립니다.

## 7. 모델별 규칙

### ① 선형회귀
`sklearn.linear_model.LinearRegression` 을 사용합니다.

### ② MLP (신경망)
`sklearn.neural_network.MLPRegressor` 를 사용합니다. **아래 설정을 반드시 지킵니다.**

```python
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor

# 입력과 정답을 모두 표준화해야 결과가 안정적입니다
scaler = StandardScaler().fit(X_train)
y_mean, y_std = y_train.mean(), y_train.std()

model = MLPRegressor(
    hidden_layer_sizes=(64,), max_iter=500, random_state=9,
    early_stopping=True, n_iter_no_change=25,
)
model.fit(scaler.transform(X_train), (y_train - y_mean) / y_std)
pred = model.predict(scaler.transform(X_test)) * y_std + y_mean
```

### ④ LightGBM (다른 실습 환경 — 07_lgbm.py 를 만들 때만)
`lightgbm.LGBMRegressor` 를 사용합니다. 설치가 안 되어 있으면 `pip install lightgbm` 을 **먼저 물어보고** 실행합니다.

```python
from lightgbm import LGBMRegressor
model = LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=15,
                      random_state=9, verbose=-1)
model.fit(X_train, y_train)
```

### ③ 파운데이션 모델 (Chronos-2)
**반드시 아래 형식만 사용합니다.** `BaseChronosPipeline`, `torch.tensor` 방식은
옛날 버전이므로 절대 쓰지 않습니다.

```python
from chronos import Chronos2Pipeline

pipeline = Chronos2Pipeline.from_pretrained(
    "autogluon/chronos-2-small", device_map="cpu"
)

pred_df = pipeline.predict_df(
    context_df,                      # id, datetime, smp 컬럼을 가진 DataFrame
    prediction_length=24,            # 다음 24시간을 한 번에 예측
    quantile_levels=[0.1, 0.5, 0.9],
    id_column="id",
    timestamp_column="datetime",
    target="smp",
)
```

- Chronos는 **학습(fit)을 하지 않습니다.** `[2] 모델 학습` 섹션에는
  "이 모델은 학습하지 않습니다 (zero-shot)" 라는 주석만 남깁니다.
- 테스트 1,440시간을 **하루 단위로 60번** 실행합니다. 모델에 보여줄 과거(context)는 4주(672시간)면 충분합니다.
- 예측값(p10, p50, p90)을 `pred_fm.csv` 로 저장해 `04_compare.py` 가 읽게 합니다.

## 8. 파일 이름

| 파일 | 내용 |
|---|---|
| `00_explore.py` | (선택) 데이터 살펴보기 — 프롬프트 ① |
| `01_ml.py` | 선형회귀 |
| `02_mlp.py` | MLP 신경망 |
| `03_fm.py` | Chronos-2 — 예측값을 `pred_fm.csv` 로 저장 (04 에서 읽음) |
| `04_compare.py` | 세 모델 + 기준선 비교 — `pred_fm.csv` 가 없으면 Chronos 없이 세 가지만 비교 |
| `05_multivar.py` | (추가 분석) 외부 데이터 추가 — 프롬프트 ⑧ |
| `05b_leak.py` | (추가 분석) 반칙 실험 — 프롬프트 ⑨ |
| `06_window.py` | (추가 분석) `01_ml.py` 에서 LAG 만 168 로 — 프롬프트 ⑩ |
| `07_lgbm.py` | (다른 실습 환경) `01_ml.py` 에서 [2] 만 LightGBM 으로 — 프롬프트 ⑪ |
