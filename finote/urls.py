"""
URL configuration for finnote project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def home_redirect(request):
    return redirect('dashboard:page_total')

def debug_urls(request):
    from django.http import HttpResponse
    from django.urls import get_resolver
    
    resolver = get_resolver()
    url_patterns = []
    
    def extract_patterns(pattern_list, prefix=''):
        for pattern in pattern_list:
            if hasattr(pattern, 'url_patterns'):
                # URLconf include
                extract_patterns(pattern.url_patterns, prefix + str(pattern.pattern))
            else:
                # Regular URL pattern
                url_patterns.append(prefix + str(pattern.pattern))
    
    extract_patterns(resolver.url_patterns)
    
    html = "<h1>🔍 Django URL 패턴 디버깅</h1><ul>"
    for pattern in url_patterns:
        html += f"<li><code>{pattern}</code></li>"
    html += "</ul>"
    
    return HttpResponse(html)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect, name='home'),
    path('debug-urls/', debug_urls, name='debug_urls'),  # 디버깅용 임시 URL
    path('dashboard/', include('dashboard.urls')),
]
