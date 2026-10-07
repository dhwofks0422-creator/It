# ============================================================
# [1] 데이터 준비
# ============================================================
import os
import platform
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# 1. 데이터 불러오기
# smp_hourly.csv는 UTF-8(BOM) 인코딩이므로 기본 설정으로 바로 읽을 수 있습니다.
df = pd.read_csv('smp_hourly.csv')
df['datetime'] = pd.to_datetime(df['datetime'])

# 2. 실습 과제 파라미터 설정
# - 과거 96시간(4일)의 SMP를 입력으로 사용
# - 24시간 뒤(내일 같은 시각)의 SMP를 예측
# - 마지막 60일(1,440시간)을 테스트 세트로 사용
LAG = 96          # 과거 96시간 (4일치)
HORIZON = 24      # 24시간 뒤 (내일 같은 시각)
TEST = 24 * 60    # 테스트 기간 (마지막 60일 = 1,440시간)

smp = df['smp'].values
dts = df['datetime'].values

X_list = []
y_list = []
naive_list = []
dt_target_list = []

# 슬라이딩 윈도우 방식으로 입력(X)과 정답(y), 기준선(naive) 생성
# i는 과거 96시간 관측치의 끝 지점이며, 예측 대상 시점은 i로부터 HORIZON-1 (즉, 24시간 뒤)
for i in range(LAG, len(smp) - HORIZON + 1):
    # 과거 96시간 SMP를 한 줄의 특성 벡터로 추출
    past_smp = smp[i - LAG:i]
    
    # 예측 대상 시점 (내일 같은 시각)
    target_idx = i + HORIZON - 1
    g = pd.Timestamp(dts[target_idx])
    
    # 시간(0~23)과 요일(0~6)의 순환 정보 생성 (0시와 23시의 연속성을 유지하기 위해 sin/cos 변환)
    sin_h = np.sin(2 * np.pi * g.hour / 24)
    cos_h = np.cos(2 * np.pi * g.hour / 24)
    sin_d = np.sin(2 * np.pi * g.dayofweek / 7)
    cos_d = np.cos(2 * np.pi * g.dayofweek / 7)
    
    # 과거 96시간 SMP + 달력 정보 4개 결합 (총 100개 입력 변수)
    features = np.concatenate([past_smp, [sin_h, cos_h, sin_d, cos_d]])
    
    X_list.append(features)
    y_list.append(smp[target_idx])
    
    # 비교 기준선 (Naive): "어제 같은 시각의 값을 그대로 쓰기"
    # 예측 대상 시점(target_idx)의 24시간 전 값은 현재 시점 관측치의 마지막 값(smp[i - 1])과 정확히 일치합니다.
    naive_list.append(smp[i - 1])
    dt_target_list.append(g)

X = np.array(X_list)
y = np.array(y_list)
naive = np.array(naive_list)
dt_target = np.array(dt_target_list)

# 시간 순서를 엄격히 지켜 학습과 테스트 데이터 분할 (절대 랜덤 셔플 금지)
X_train, X_test = X[:-TEST], X[-TEST:]
y_train, y_test = y[:-TEST], y[-TEST:]
naive_train, naive_test = naive[:-TEST], naive[-TEST:]
dt_test = dt_target[-TEST:]

print(f"데이터 준비 완료: 전체 {len(X):,}개 | 학습 세트 {len(X_train):,}개 | 테스트 세트 {len(X_test):,}개")

# ============================================================
# [2] 모델 학습
# ============================================================
# 선형회귀 모델 생성 및 학습
model = LinearRegression()
model.fit(X_train, y_train)
print("모델 학습 완료 (LinearRegression)")

# ============================================================
# [3] 예측
# ============================================================
# 테스트 세트에 대해 24시간 뒤 SMP 예측 수행
pred = model.predict(X_test)
print("테스트 데이터 예측 완료")

# ============================================================
# [4] 평가 및 시각화
# ============================================================
# 평가지표 계산 함수
def calc_metrics(actual, predicted):
    mae = np.mean(np.abs(actual - predicted))
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    # 데이터에 SMP가 0원인 시간(태양광 과잉 등)이 있으므로, 실제값이 1원을 넘는 행만 MAPE 계산
    m = actual > 1
    mape = np.mean(np.abs((actual[m] - predicted[m]) / actual[m])) * 100
    return mae, rmse, mape

# 기준선 및 선형회귀 평가
naive_mae, naive_rmse, naive_mape = calc_metrics(y_test, naive_test)
model_mae, model_rmse, model_mape = calc_metrics(y_test, pred)

# 기준선 대비 개선율 (%) 계산
imp_mae = (naive_mae - model_mae) / naive_mae * 100
imp_rmse = (naive_rmse - model_rmse) / naive_rmse * 100
imp_mape = (naive_mape - model_mape) / naive_mape * 100

# 결과 표 출력
print("\n" + "=" * 65)
print(f"{'모델':<18} {'MAE (원)':>10} {'RMSE (원)':>10} {'MAPE (%)':>10} {'개선율':>10}")
print("-" * 65)
print(f"{'기준선 (어제 같은 시각)':<18} {naive_mae:10.2f} {naive_rmse:10.2f} {naive_mape:10.2f}% {'-':>10}")
print(f"{'선형회귀 (01_ml)':<18} {model_mae:10.2f} {model_rmse:10.2f} {model_mape:10.2f}% {imp_mae:+9.1f}%")
print("=" * 65 + "\n")

# 그래프 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic' if platform.system() == 'Windows' else 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

# 테스트 구간 중 마지막 7일(168시간) 확대 시각화
ZOOM = 168
plt.figure(figsize=(12, 6))
plt.plot(dt_test[-ZOOM:], y_test[-ZOOM:], label='실제값 (Actual)', color='black', linewidth=1.5)
plt.plot(dt_test[-ZOOM:], naive_test[-ZOOM:], label='기준선 (Naive - 어제 같은 시각)', color='gray', linestyle='--', alpha=0.7)
plt.plot(dt_test[-ZOOM:], pred[-ZOOM:], label='선형회귀 (Linear Regression)', color='#1f77b4', linewidth=1.8)

plt.title('SMP 24시간 뒤 예측 결과 비교 (마지막 7일 확대)', fontsize=14, pad=12)
plt.xlabel('일시', fontsize=11)
plt.ylabel('SMP (원/kWh)', fontsize=11)
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend(loc='upper right', fontsize=10)
plt.tight_layout()

# PNG 파일로 먼저 저장
os.makedirs('plots', exist_ok=True)
save_path = os.path.join('plots', '02_ml.png')
plt.savefig(save_path, dpi=300)
print(f"그래프 저장 완료: {save_path}")

# 화면에 그래프 창 표시
plt.show()

