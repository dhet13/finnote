# apps/dashboard/views/pages.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from ..models import AssetLogUnified, PortfolioHolding, PortfolioSnapshot

@login_required
def total_page(request):
    """대시보드 총자산 현황 페이지"""
    
    try:
        # 로그인된 사용자 확인
        if not request.user.is_authenticated:
            return render(request, "total.html", {
                'page_title': '대시보드 - 총자산',
                'user': None,
                'login_required': True
            })
        
        # 기본 컨텍스트 데이터
        context = {
            'page_title': '대시보드 - 총자산',
            'user': request.user,
            'login_required': False
        }
        
        # 실제 total.html 템플릿 렌더링
        return render(request, "total.html", context)
        
    except Exception as e:
        import traceback
        return HttpResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🚨 Template Error</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial; padding: 20px; background: #ffe6e6; }}
                .error {{ background: white; padding: 20px; border-radius: 8px; border-left: 5px solid red; }}
                pre {{ background: #f5f5f5; padding: 10px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h1>🚨 Total.html 템플릿 오류!</h1>
                <p><strong>오류:</strong> {str(e)}</p>
                <h3>상세 오류:</h3>
                <pre>{traceback.format_exc()}</pre>
            </div>
        </body>
        </html>
        """)

@login_required
def total_content(request):
    """자산 현황 콘텐츠만 반환 (AJAX용)"""
    try:
        # 로그인된 사용자 확인
        if not request.user.is_authenticated:
            return HttpResponse("로그인이 필요합니다.")
        
        context = {
            'page_title': '대시보드 - 총자산',
            'user': request.user,
        }
        return render(request, "total_content.html", context)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")

@login_required
def portfolio_content(request):
    """포트폴리오 콘텐츠만 반환 (AJAX용)"""
    try:
        # 로그인된 사용자 확인
        if not request.user.is_authenticated:
            return HttpResponse("로그인이 필요합니다.")
        
        context = {
            'page_title': '대시보드 - 포트폴리오',
            'user': request.user,
        }
        return render(request, "portfolio_content.html", context)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")

@login_required
def portfolio_page(request):
    """대시보드 포트폴리오 페이지"""
    
    try:
        # 로그인된 사용자 확인
        if not request.user.is_authenticated:
            return render(request, "portfolio.html", {
                'page_title': '대시보드 - 포트폴리오',
                'user': None,
                'login_required': True
            })
        
        # 기본 컨텍스트 데이터
        context = {
            'page_title': '대시보드 - 포트폴리오',
            'user': request.user,
            'login_required': False
        }
        
        # 실제 portfolio.html 템플릿 렌더링
        return render(request, "portfolio.html", context)
        
    except Exception as e:
        import traceback
        return HttpResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🚨 Template Error</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial; padding: 20px; background: #ffe6e6; }}
                .error {{ background: white; padding: 20px; border-radius: 8px; border-left: 5px solid red; }}
                pre {{ background: #f5f5f5; padding: 10px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h1>🚨 Portfolio.html 템플릿 오류!</h1>
                <p><strong>오류:</strong> {str(e)}</p>
                <h3>상세 오류:</h3>
                <pre>{traceback.format_exc()}</pre>
            </div>
        </body>
        </html>
        """)