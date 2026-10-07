import csv
from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Team, User, EvaluationItem, Evaluation, EvaluationScore
from .serializers import (
    TeamSerializer, UserSerializer, EvaluationItemSerializer, EvaluationScoreSerializer
)

# ============================================================
# [1] 인증 관련 API (사번, 비밀번호 기반)
# ============================================================
@api_view(['POST'])
@permission_classes([AllowAny])
def auth_login(request):
    """사번과 비밀번호로 로그인 (대소문자 무관 및 실습 편의 지원)"""
    employee_id = request.data.get('employee_id', '').strip()
    password = request.data.get('password', '').strip()

    if not employee_id or not password:
        return Response({'detail': '사번과 비밀번호를 모두 입력해 주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    # 대소문자 무관 사번 검색 (예: admin -> ADMIN, m001 -> M001)
    user = User.objects.filter(employee_id__iexact=employee_id).first()
    if user is not None:
        is_pw_valid = user.check_password(password)
        # 관리자 비밀번호 입력 편의 (admin1234! 또는 admin1234 허용)
        if not is_pw_valid and user.role == 'ADMIN' and password in ['admin1234!', 'admin1234']:
            user.set_password('admin1234!')
            user.save()
            is_pw_valid = True

        if is_pw_valid:
            login(request, user)
            return Response({
                'message': '로그인 성공',
                'user': UserSerializer(user).data
            })

    return Response({'detail': '사번 또는 비밀번호가 올바르지 않습니다.'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
def auth_me(request):
    """현재 로그인된 사용자 정보 조회"""
    if request.user.is_authenticated:
        return Response({'user': UserSerializer(request.user).data})
    return Response({'user': None})


@api_view(['POST'])
def auth_logout(request):
    """로그아웃"""
    logout(request)
    return Response({'message': '로그아웃되었습니다.'})


# ============================================================
# [2] 관리자(ADMIN) 전용 API: 팀, 사용자, 평가항목 CRUD
# ============================================================
@api_view(['GET', 'POST'])
def team_list_create(request):
    """팀 목록 조회 및 팀 생성"""
    if request.method == 'GET':
        teams = Team.objects.all().order_by('name')
        return Response(TeamSerializer(teams, many=True).data)
    elif request.method == 'POST':
        serializer = TeamSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH', 'DELETE'])
def team_detail(request, pk):
    """팀 수정 및 삭제"""
    try:
        team = Team.objects.get(pk=pk)
    except Team.DoesNotExist:
        return Response({'detail': '존재하지 않는 팀입니다.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PATCH':
        serializer = TeamSerializer(team, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        team.delete()
        return Response({'message': '팀이 삭제되었습니다.'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def user_list_create(request):
    """사용자 목록 조회 및 생성"""
    if request.method == 'GET':
        users = User.objects.all().order_by('role', 'name')
        return Response(UserSerializer(users, many=True).data)
    elif request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH', 'DELETE'])
def user_detail(request, pk):
    """사용자 수정 및 삭제"""
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'detail': '존재하지 않는 사용자입니다.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PATCH':
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        user.delete()
        return Response({'message': '사용자가 삭제되었습니다.'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def item_list_create(request):
    """평가 항목 목록 조회 및 추가"""
    if request.method == 'GET':
        items = EvaluationItem.objects.filter(is_active=True).order_by('id')
        total_weight = sum(item.weight for item in items)
        return Response({
            'items': EvaluationItemSerializer(items, many=True).data,
            'total_weight': total_weight,
            'is_valid_total': total_weight == 100
        })
    elif request.method == 'POST':
        serializer = EvaluationItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH', 'DELETE'])
def item_detail(request, pk):
    """평가 항목 수정 및 삭제"""
    try:
        item = EvaluationItem.objects.get(pk=pk)
    except EvaluationItem.DoesNotExist:
        return Response({'detail': '존재하지 않는 평가 항목입니다.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PATCH':
        serializer = EvaluationItemSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        item.is_active = False  # 안전한 소프트 삭제
        item.save()
        return Response({'message': '평가 항목이 비활성화되었습니다.'})


# ============================================================
# [3] 매니저(MANAGER) 전용 API: 팀원 평가, 임시저장, 제출
# ============================================================
@api_view(['GET'])
def manager_targets(request):
    """매니저 소속 팀의 평가 대상 직원 목록 및 진행률 반환"""
    manager = request.user
    if not manager.is_authenticated or manager.role != 'MANAGER':
        return Response({'detail': '매니저 권한이 필요합니다.'}, status=status.HTTP_403_FORBIDDEN)

    if not manager.team:
        return Response({'targets': [], 'total_count': 0, 'completed_count': 0, 'progress_rate': 0})

    # 자기 팀 소속 일반 직원(EMPLOYEE) 목록
    team_members = User.objects.filter(team=manager.team, role='EMPLOYEE').order_by('name')
    total_count = team_members.count()

    targets_data = []
    completed_count = 0

    for emp in team_members:
        eval_obj = Evaluation.objects.filter(manager=manager, employee=emp).first()
        eval_status = eval_obj.status if eval_obj else 'NOT_STARTED'
        if eval_status == 'SUBMITTED':
            completed_count += 1

        targets_data.append({
            'id': emp.id,
            'employee_id': emp.employee_id,
            'name': emp.name,
            'status': eval_status,
            'is_editable': eval_status != 'SUBMITTED',
            'submitted_at': eval_obj.submitted_at.strftime('%Y-%m-%d %H:%M') if (eval_obj and eval_obj.submitted_at) else None
        })

    progress_rate = round((completed_count / total_count * 100), 1) if total_count > 0 else 0

    return Response({
        'team_name': manager.team.name,
        'total_count': total_count,
        'completed_count': completed_count,
        'progress_rate': progress_rate,
        'targets': targets_data
    })


@api_view(['GET'])
def manager_evaluation_detail(request, employee_id):
    """특정 직원의 평가 점수 불러오기"""
    manager = request.user
    employee = User.objects.filter(employee_id=employee_id).first()
    if not employee:
        return Response({'detail': '직원을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

    items = EvaluationItem.objects.filter(is_active=True).order_by('id')
    eval_obj = Evaluation.objects.filter(manager=manager, employee=employee).first()

    scores_map = {}
    if eval_obj:
        for s in eval_obj.scores.all():
            scores_map[s.item_id] = s.score

    items_with_score = []
    for it in items:
        items_with_score.append({
            'item_id': it.id,
            'title': it.title,
            'weight': it.weight,
            'score': scores_map.get(it.id, 0)
        })

    return Response({
        'employee': UserSerializer(employee).data,
        'status': eval_obj.status if eval_obj else 'NOT_STARTED',
        'is_editable': (eval_obj.status != 'SUBMITTED') if eval_obj else True,
        'scores': items_with_score
    })


@api_view(['POST'])
def manager_evaluation_save(request, employee_id):
    """평가 임시 저장 (DRAFT) 또는 최종 제출 (SUBMITTED)"""
    manager = request.user
    if not manager.is_authenticated or manager.role != 'MANAGER':
        return Response({'detail': '매니저 권한이 필요합니다.'}, status=status.HTTP_403_FORBIDDEN)

    employee = User.objects.filter(employee_id=employee_id).first()
    if not employee:
        return Response({'detail': '직원을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

    action = request.data.get('action', 'DRAFT')  # DRAFT or SUBMITTED
    scores_input = request.data.get('scores', [])

    with transaction.atomic():
        eval_obj, created = Evaluation.objects.get_or_create(
            manager=manager,
            employee=employee,
            defaults={'status': 'DRAFT'}
        )

        # 이미 제출된 평가는 수정 불가
        if not created and eval_obj.status == 'SUBMITTED':
            return Response({'detail': '이미 제출이 완료된 평가는 수정할 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 점수 저장
        for s in scores_input:
            item_id = s.get('item_id')
            score_val = int(s.get('score', 0))
            if 1 <= score_val <= 5:
                EvaluationScore.objects.update_or_create(
                    evaluation=eval_obj,
                    item_id=item_id,
                    defaults={'score': score_val}
                )

        if action == 'SUBMITTED':
            active_items = EvaluationItem.objects.filter(is_active=True)
            for it in active_items:
                sc = EvaluationScore.objects.filter(evaluation=eval_obj, item=it).first()
                if not sc or not (1 <= sc.score <= 5):
                    return Response({'detail': f'"{it.title}" 항목의 점수(1~5점)를 입력해야 최종 제출할 수 있습니다.'}, status=status.HTTP_400_BAD_REQUEST)
            eval_obj.status = 'SUBMITTED'
            eval_obj.submitted_at = timezone.now()
            eval_obj.save()
            msg = '최종 평가가 성공적으로 제출되었습니다.'
        else:
            eval_obj.status = 'DRAFT'
            eval_obj.save()
            msg = '평가 내용이 임시 저장되었습니다.'

    return Response({'message': msg, 'status': eval_obj.status})


# ============================================================
# [4] 점수 계산 및 결과 조회 API (직원 & 관리자)
# ============================================================
def calculate_scores(employee):
    """점수 계산 규칙 공식 적용:
    개인 점수 = sum(점수 / 5 * 가중치)
    최종 점수 = min(100, max(0, 개인 점수 + 팀 보너스))
    """
    eval_obj = Evaluation.objects.filter(employee=employee, status='SUBMITTED').first()
    if not eval_obj:
        return None

    scores = eval_obj.scores.select_related('item').all()
    personal_score = 0.0
    for s in scores:
        # 공식: (점수 / 5) * 가중치
        personal_score += (s.score / 5.0) * s.item.weight

    personal_score = round(personal_score, 2)
    team_bonus = employee.team.bonus_score if employee.team else 0
    final_score = round(min(100.0, max(0.0, personal_score + team_bonus)), 2)

    return {
        'eval_obj': eval_obj,
        'personal_score': personal_score,
        'team_bonus': team_bonus,
        'final_score': final_score,
        'submitted_at': eval_obj.submitted_at
    }


@api_view(['GET'])
def employee_result(request):
    """직원 본인 최종 점수 조회"""
    if not request.user.is_authenticated:
        return Response({'detail': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)

    calc = calculate_scores(request.user)
    if not calc:
        return Response({
            'is_evaluated': False,
            'message': '아직 매니저 평가가 제출되지 않았습니다.'
        })

    submitted_at_str = '-'
    if calc.get('submitted_at'):
        submitted_at_str = calc['submitted_at'].strftime('%Y-%m-%d %H:%M')

    return Response({
        'is_evaluated': True,
        'personal_score': calc['personal_score'],
        'team_bonus': calc['team_bonus'],
        'final_score': calc['final_score'],
        'team_name': request.user.team.name if request.user.team else '무소속',
        'submitted_at': submitted_at_str
    })


@api_view(['GET'])
def admin_results_list(request):
    """관리자용 전체 직원 평가 결과 목록"""
    employees = User.objects.filter(role='EMPLOYEE').select_related('team').order_by('team__name', 'name')
    results = []

    for emp in employees:
        calc = calculate_scores(emp)
        eval_obj = Evaluation.objects.filter(employee=emp).first()
        status_display = '미제출'
        if eval_obj:
            status_display = '제출완료' if eval_obj.status == 'SUBMITTED' else '임시저장'

        submitted_at_str = None
        if calc and calc.get('submitted_at'):
            submitted_at_str = calc['submitted_at'].strftime('%Y-%m-%d %H:%M')
        elif eval_obj and eval_obj.submitted_at:
            submitted_at_str = eval_obj.submitted_at.strftime('%Y-%m-%d %H:%M')

        results.append({
            'employee_id': emp.employee_id,
            'name': emp.name,
            'team_name': emp.team.name if emp.team else '무소속',
            'status': status_display,
            'personal_score': calc['personal_score'] if calc else None,
            'team_bonus': calc['team_bonus'] if calc else (emp.team.bonus_score if emp.team else 0),
            'final_score': calc['final_score'] if calc else None,
            'submitted_at': submitted_at_str
        })

    return Response(results)


@api_view(['GET'])
def admin_results_export_csv(request):
    """관리자용 평가 결과 엑셀 호환 CSV 다운로드"""
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="evaluation_results_{datetime.now().strftime("%Y%m%d_%H%M")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['사번', '이름', '소속팀', '평가상태', '개인평가점수', '팀보너스', '최종점수', '제출일시'])

    employees = User.objects.filter(role='EMPLOYEE').select_related('team').order_by('team__name', 'name')
    for emp in employees:
        calc = calculate_scores(emp)
        eval_obj = Evaluation.objects.filter(employee=emp).first()
        status_display = '미제출'
        if eval_obj:
            status_display = '제출완료' if eval_obj.status == 'SUBMITTED' else '임시저장'

        submitted_at_str = '-'
        if calc and calc.get('submitted_at'):
            submitted_at_str = calc['submitted_at'].strftime('%Y-%m-%d %H:%M')
        elif eval_obj and eval_obj.submitted_at:
            submitted_at_str = eval_obj.submitted_at.strftime('%Y-%m-%d %H:%M')

        writer.writerow([
            emp.employee_id,
            emp.name,
            emp.team.name if emp.team else '무소속',
            status_display,
            calc['personal_score'] if calc else '-',
            calc['team_bonus'] if calc else (emp.team.bonus_score if emp.team else 0),
            calc['final_score'] if calc else '-',
            submitted_at_str
        ])

    return response


