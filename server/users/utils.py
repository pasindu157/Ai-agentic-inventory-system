from .models import AuditLog

def get_client_ip(request):
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_audit_event(user, action, details='', request=None):
    try:
        ip_address = get_client_ip(request)
        user_obj = user if user and getattr(user, 'is_authenticated', False) else None
        
        AuditLog.objects.create(
            user=user_obj,
            action=action,
            details=str(details),
            ip_address=ip_address
        )
    except Exception as e:
        print(f"[AuditLog Error]: {e}")
