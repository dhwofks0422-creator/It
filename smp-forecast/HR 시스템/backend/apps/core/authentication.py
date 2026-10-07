from rest_framework.authentication import SessionAuthentication

class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    캡스톤 실습 환경을 위한 CSRF 면제 세션 인증 클래스.
    프론트엔드 fetch API 호출 시 CSRF 토큰 누락 오류(CSRF Failed)를 방지합니다.
    """
    def enforce_csrf(self, request):
        return  # CSRF 검증 생략

