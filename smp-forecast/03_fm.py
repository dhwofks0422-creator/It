# ============================================================
# [1] 데이터 준비
# ============================================================
import os
import platform
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from chronos import Chronos2Pipeline

# 1. 데이터 불러오기
# smp_hourly.csv는 2023-01-01부터 2025-12-31까지 26,304시간 데이터입니다.
df = pd.read_csv('smp_hourly.csv')
df['datetime'] = pd.to_datetime(df['datetime'])

# Chronos2Pipeline 입력 규격: id, datetime, smp 컬럼 필요
df['id'] = 'smp'

# 2. 파라미터 설정
# - 테스트 기간: 마지막 60일 (1,440시간)
# - 과거 입력(Context): 4주 (672시간)
# - 예측 단위: 하루치 (24시간)씩 60번 순차 예측
TEST = 24 * 60       # 1,440시간
CONTEXT = 24 * 28    # 672시간 (4주)
HORIZON = 24         # 24시간

test_start_idx = len(df) - TEST
y_test = df['smp'].iloc[test_start_idx:].values
dt_test = df['datetime'].iloc[test_start_idx:].values

# 기준선 (Naive): "어제 같은 시각의 값을 그대로 쓰기" (예측 대상 시점의 24시간 전 값)
naive_test = df['smp'].iloc[test_start_idx - 24 : len(df) - 24].values

print(f"데이터 준비 완료: 전체 {len(df):,}개 | 테스트 {len(y_test):,}개 (60일) | Context 윈도우 {CONTEXT}시간 (4주)")

# ============================================================
# [2] 모델 학습
# ============================================================
# 이 모델은 학습하지 않습니다 (zero-shot)
# 시계열 파운데이션 모델은 이미 대규모 데이터로 사전학습(pre-trained)되어 있으므로
# 우리 데이터로 fit() 과정을 거치지 않고 바로 예측에 활용합니다.

# ============================================================
# [3] 예측
# ============================================================
print("\nChronos-2 파운데이션 모델 불러오는 중...")
pipeline = Chronos2Pipeline.from_pretrained(
    "autogluon/chronos-2-small", device_map="cpu"
)
print("모델 로드 완료 (autogluon/chronos-2-small)")

print("\n60일간 하루치(24시간)씩 순차 예측을 시작합니다...")
preds_list = []

# 하루 단위(24시간)로 60번 예측 수행
for day in range(60):
    start_pred_idx = test_start_idx + day * HORIZON
    end_pred_idx = start_pred_idx + HORIZON
    
    # 모델에 보여줄 직전 4주(672시간) 데이터
    context_df = df.iloc[start_pred_idx - CONTEXT : start_pred_idx][['id', 'datetime', 'smp']]
    
    pred_df = pipeline.predict_df(
        context_df,
        prediction_length=HORIZON,
        quantile_levels=[0.1, 0.5, 0.9],
        id_column="id",
        timestamp_column="datetime",
        target="smp",
    )
    preds_list.append(pred_df)
    
    if (day + 1) % 10 == 0 or (day + 1) == 60:
        print(f"진행 상황: {day + 1}/60일 예측 완료 ({(day + 1) * 24}시간)", flush=True)

all_preds = pd.concat(preds_list, ignore_index=True)

# 분위수 컬럼 이름 파싱 (0.1, 0.5, 0.9 또는 '0.1', '0.5', '0.9')
c_10 = 0.1 if 0.1 in all_preds.columns else ('0.1' if '0.1' in all_preds.columns else all_preds.columns[-3])
c_50 = 0.5 if 0.5 in all_preds.columns else ('0.5' if '0.5' in all_preds.columns else ('mean' if 'mean' in all_preds.columns else all_preds.columns[-2]))
c_90 = 0.9 if 0.9 in all_preds.columns else ('0.9' if '0.9' in all_preds.columns else all_preds.columns[-1])

p10 = all_preds[c_10].values
p50 = all_preds[c_50].values
p90 = all_preds[c_90].values

# 비교 분석(04_compare.py)에서 사용할 수 있도록 pred_fm.csv 로 저장
pred_fm_df = pd.DataFrame({
    'datetime': all_preds['datetime'],
    'p10': p10,
    'p50': p50,
    'p90': p90
})
pred_fm_df.to_csv('pred_fm.csv', index=False, encoding='utf-8-sig')
print("\n예측 결과 저장 완료: pred_fm.csv")

# ============================================================
# [4] 평가 및 시각화
# ============================================================
# 평가지표 함수 정의 (1원 초과 대상 MAPE 계산)
def calc_metrics(actual, predicted):
    mae = np.mean(np.abs(actual - predicted))
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    m = actual > 1
    mape = np.mean(np.abs((actual[m] - predicted[m]) / actual[m])) * 100
    return mae, rmse, mape

naive_mae, naive_rmse, naive_mape = calc_metrics(y_test, naive_test)
model_mae, model_rmse, model_mape = calc_metrics(y_test, p50)

imp_mae = (naive_mae - model_mae) / naive_mae * 100
imp_rmse = (naive_rmse - model_rmse) / naive_rmse * 100
imp_mape = (naive_mape - model_mape) / naive_mape * 100

print("\n" + "=" * 65)
print(f"{'모델':<18} {'MAE (원)':>10} {'RMSE (원)':>10} {'MAPE (%)':>10} {'개선율':>10}")
print("-" * 65)
print(f"{'기준선 (어제 같은 시각)':<18} {naive_mae:10.2f} {naive_rmse:10.2f} {naive_mape:10.2f}% {'-':>10}")
print(f"{'Chronos-2 (p50)':<18} {model_mae:10.2f} {model_rmse:10.2f} {model_mape:10.2f}% {imp_mae:+9.1f}%")
print("=" * 65 + "\n")

# 그래프 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic' if platform.system() == 'Windows' else 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

# 마지막 7일 (168시간) 확대 시각화
ZOOM = 168
plt.figure(figsize=(12, 6))

# 10%~90% 예측 구간 음영 표시
plt.fill_between(
    dt_test[-ZOOM:], p10[-ZOOM:], p90[-ZOOM:],
    color='#1f77b4', alpha=0.2, label='10%~90% 예측 범위 (Chronos-2)'
)
plt.plot(dt_test[-ZOOM:], y_test[-ZOOM:], label='실제값 (Actual)', color='black', linewidth=1.5)
plt.plot(dt_test[-ZOOM:], naive_test[-ZOOM:], label='기준선 (Naive - 어제 같은 시각)', color='gray', linestyle='--', alpha=0.7)
plt.plot(dt_test[-ZOOM:], p50[-ZOOM:], label='Chronos-2 예측값 (p50 중앙값)', color='#1f77b4', linewidth=1.8)

plt.title('Chronos-2 파운데이션 모델 예측 결과 (마지막 7일 확대)', fontsize=14, pad=12)
plt.xlabel('일시', fontsize=11)
plt.ylabel('SMP (원/kWh)', fontsize=11)
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend(loc='upper right', fontsize=10)
plt.tight_layout()

# plots 폴더에 먼저 저장
os.makedirs('plots', exist_ok=True)
save_path = os.path.join('plots', '04_fm.png')
plt.savefig(save_path, dpi=300)
print(f"그래프 저장 완료: {save_path}")

# 화면에 그래프 표시
plt.show()

