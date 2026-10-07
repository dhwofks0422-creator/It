from django.core.management.base import BaseCommand
from apps.core.models import User, Team, EvaluationItem

class Command(BaseCommand):
    help = '기본 관리자 계정(ADMIN/admin1234!) 및 초기 실습 데이터 자동 생성'

    def handle(self, *args, **options):
        # 1. 기본 관리자 계정 생성 (사번: ADMIN, 암호: admin1234!)
        admin_user, created = User.objects.get_or_create(
            employee_id='ADMIN',
            defaults={
                'name': '최고관리자',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin1234!')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("기본 관리자 계정 생성 완료: ADMIN / admin1234!"))
        else:
            self.stdout.write("기본 관리자 계정(ADMIN)이 이미 존재합니다.")

        # 2. 실습용 팀 생성
        dev_team, _ = Team.objects.get_or_create(name='개발팀', defaults={'bonus_score': 5})
        mkt_team, _ = Team.objects.get_or_create(name='마케팅팀', defaults={'bonus_score': 3})

        # 3. 실습용 평가 항목 생성 (합계 100% 가중치)
        items_data = [
            ('업무 성과 달성도', 50),
            ('협업 및 팀워크', 30),
            ('직무 전문성 및 혁신', 20),
        ]
        for title, weight in items_data:
            EvaluationItem.objects.get_or_create(title=title, defaults={'weight': weight, 'is_active': True})

        # 4. 실습용 매니저 및 직원 계정 생성 (비밀번호: 1234)
        sample_users = [
            ('M001', '김팀장', 'MANAGER', dev_team),
            ('E001', '이개발', 'EMPLOYEE', dev_team),
            ('E002', '박코딩', 'EMPLOYEE', dev_team),
            ('M002', '최팀장', 'MANAGER', mkt_team),
            ('E003', '정마케팅', 'EMPLOYEE', mkt_team),
        ]
        for emp_id, name, role, team in sample_users:
            u, u_created = User.objects.get_or_create(
                employee_id=emp_id,
                defaults={'name': name, 'role': role, 'team': team}
            )
            if u_created:
                u.set_password('1234')
                u.save()

        self.stdout.write(self.style.SUCCESS("초기 실습 데이터(팀, 사용자, 평가 항목) 세팅 완료!"))

