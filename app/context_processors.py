from django.conf import settings

def theme_context(request):
    if request.user.is_authenticated:
        return {
            'current_theme': request.user.theme_preference,
            'available_themes': settings.AVAILABLE_THEMES,
            'unlocked_themes': request.user.unlocked_themes or [],
        }
    return {}