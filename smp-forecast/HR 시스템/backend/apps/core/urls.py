from django.urls import path
from . import views

urlpatterns = [
    # 1. 인증 관련
    path('auth/login/', views.auth_login, name='auth-login'),
    path('auth/me/', views.auth_me, name='auth-me'),
    path('auth/logout/', views.auth_logout, name='auth-logout'),

    # 2. 관리자: 팀 관리
    path('teams/', views.team_list_create, name='team-list-create'),
    path('teams/<int:pk>/', views.team_detail, name='team-detail'),

    # 2. 관리자: 사용자 관리
    path('users/', views.user_list_create, name='user-list-create'),
    path('users/<int:pk>/', views.user_detail, name='user-detail'),

    # 2. 관리자: 평가 항목 관리
    path('items/', views.item_list_create, name='item-list-create'),
    path('items/<int:pk>/', views.item_detail, name='item-detail'),

    # 3. 매니저: 평가 대상 및 입력
    path('manager/targets/', views.manager_targets, name='manager-targets'),
    path('manager/evaluations/<str:employee_id>/', views.manager_evaluation_detail, name='manager-eval-detail'),
    path('manager/evaluations/<str:employee_id>/save/', views.manager_evaluation_save, name='manager-eval-save'),

    # 4. 직원: 결과 조회
    path('employee/result/', views.employee_result, name='employee-result'),

    # 5. 관리자: 전체 결과 및 CSV
    path('admin/results/', views.admin_results_list, name='admin-results-list'),
    path('admin/results/export-csv/', views.admin_results_export_csv, name='admin-results-export-csv'),
]

