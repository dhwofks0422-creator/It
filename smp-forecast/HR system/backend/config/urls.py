from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

def frontend_view(request):
    """Vue.js 3 프론트엔드 대시보드 서빙 (Vue 머스태시 구문과 장고 템플릿 충돌 방지)"""
    index_path = settings.BASE_DIR.parent / 'frontend' / 'index.html'
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html; charset=utf-8')
    return HttpResponse('index.html을 찾을 수 없습니다.', status=404)

def health_check(request):
    """API 서버 헬스체크"""
    return JsonResponse({
        "status": "ok",
        "service": "HR 인사평가 시스템 API",
        "version": "1.0.0"
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health-check'),
    path('api/', include('apps.core.urls')),
    path('', frontend_view, name='frontend-home'),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATICFILES_DIRS[0]}),
]



