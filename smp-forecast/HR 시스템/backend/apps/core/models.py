from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator

# ============================================================
# 1. 팀 모델 (Team)
# ============================================================
class Team(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="팀명")
    bonus_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="팀 보너스 점수 (0~10점)"
    )

    class Meta:
        verbose_name = "팀"
        verbose_name_plural = "팀 목록"

    def __str__(self):
        return f"{self.name} (보너스: {self.bonus_score}점)"


# ============================================================
# 2. 사용자 모델 매니저 및 커스텀 유저 모델 (User)
# ============================================================
class UserManager(BaseUserManager):
    def create_user(self, employee_id, name, password=None, role='EMPLOYEE', team=None):
        if not employee_id:
            raise ValueError('사번은 필수 항목입니다.')
        user = self.model(
            employee_id=employee_id,
            name=name,
            role=role,
            team=team
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, employee_id, name, password=None):
        user = self.create_user(
            employee_id=employee_id,
            name=name,
            password=password,
            role='ADMIN'
        )
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('ADMIN', '관리자'),
        ('MANAGER', '매니저'),
        ('EMPLOYEE', '직원'),
    ]

    employee_id = models.CharField(max_length=50, unique=True, verbose_name="사번")
    name = models.CharField(max_length=100, verbose_name="이름")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='EMPLOYEE', verbose_name="역할")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='members', verbose_name="소속팀")
    
    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")
    is_staff = models.BooleanField(default=False, verbose_name="관리자 사이트 접근 권한")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")

    objects = UserManager()

    USERNAME_FIELD = 'employee_id'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = "사용자"
        verbose_name_plural = "사용자 목록"

    def __str__(self):
        team_name = self.team.name if self.team else '무소속'
        return f"[{self.get_role_display()}] {self.name} ({self.employee_id}, {team_name})"


# ============================================================
# 3. 평가 항목 모델 (EvaluationItem)
# ============================================================
class EvaluationItem(models.Model):
    title = models.CharField(max_length=200, verbose_name="평가 항목명")
    weight = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name="가중치 (%)"
    )
    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")

    class Meta:
        verbose_name = "평가 항목"
        verbose_name_plural = "평가 항목 목록"
        ordering = ['id']

    def __str__(self):
        return f"{self.title} (가중치: {self.weight}%)"


# ============================================================
# 4. 평가 마스터 모델 (Evaluation)
# ============================================================
class Evaluation(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', '임시저장'),
        ('SUBMITTED', '제출완료'),
    ]

    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='manager_evaluations', verbose_name="평가 매니저")
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='employee_evaluations', verbose_name="평가 대상 직원")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="진행 상태")
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="제출 일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정 일시")

    class Meta:
        verbose_name = "평가"
        verbose_name_plural = "평가 목록"
        unique_together = ('manager', 'employee')  # 매니저와 직원 1:1 평가 중복 방지

    def __str__(self):
        return f"{self.manager.name} -> {self.employee.name} ({self.get_status_display()})"


# ============================================================
# 5. 항목별 점수 모델 (EvaluationScore)
# ============================================================
class EvaluationScore(models.Model):
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='scores', verbose_name="평가 마스터")
    item = models.ForeignKey(EvaluationItem, on_delete=models.PROTECT, verbose_name="평가 항목")
    score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="점수 (1~5점)"
    )

    class Meta:
        verbose_name = "평가 점수"
        verbose_name_plural = "평가 점수 목록"
        unique_together = ('evaluation', 'item')

    def __str__(self):
        return f"{self.evaluation} - {self.item.title}: {self.score}점"

