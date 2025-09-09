# apps/dashboard/views/page.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse

# @login_required  # 임시로 주석 처리
def total_page(request):
    # 템플릿 렌더링 디버깅
    try:
        result = render(request, "base.html")
        return result
    except Exception as e:
        import traceback
        return HttpResponse(f"""
        <h1>🚨 템플릿 렌더링 오류</h1>
        <p><strong>오류:</strong> {str(e)}</p>
        <h2>상세 오류:</h2>
        <pre style="background: #f0f0f0; padding: 10px; overflow: auto;">{traceback.format_exc()}</pre>
        """)