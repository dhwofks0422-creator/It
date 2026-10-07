from rest_framework import serializers
from .models import Team, User, EvaluationItem, Evaluation, EvaluationScore

class TeamSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ['id', 'name', 'bonus_score', 'member_count']

    def get_member_count(self, obj):
        return obj.members.count()


class UserSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'employee_id', 'name', 'role', 'team', 'team_name', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_password('1234')  # 기본 임시 비밀번호
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class EvaluationItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationItem
        fields = ['id', 'title', 'weight', 'is_active', 'created_at']


class EvaluationScoreSerializer(serializers.ModelSerializer):
    item_title = serializers.CharField(source='item.title', read_only=True)
    item_weight = serializers.IntegerField(source='item.weight', read_only=True)

    class Meta:
        model = EvaluationScore
        fields = ['id', 'item', 'item_title', 'item_weight', 'score']

