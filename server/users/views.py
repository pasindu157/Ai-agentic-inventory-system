from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser, AuditLog
from .serializers import UserRegistrationSerializer, UserSerializer
from .utils import log_audit_event

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        log_audit_event(user, 'USER_REGISTERED', f"New store registered: {user.username}", self.request)

class UserProfileView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            log_audit_event(request.user, 'USER_LOGOUT', 'User logged out', request)
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class UpgradePlanView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        new_plan = request.data.get('plan')
        
        valid_plans = ['STARTER', 'PRO', 'ENTERPRISE']
        if new_plan not in valid_plans:
            return Response({'error': f'Invalid plan choice. Choose from {valid_plans}'}, status=status.HTTP_400_BAD_REQUEST)

        if not hasattr(user, 'store'):
            return Response({'error': 'No store associated with this account.'}, status=status.HTTP_400_BAD_REQUEST)

        old_plan = user.store.subscription_plan
        user.store.subscription_plan = new_plan
        user.store.save()

        log_audit_event(user, 'PLAN_UPGRADED', f"Upgraded plan from {old_plan} to {new_plan}", request)

        return Response({
            'message': f'Subscription upgraded to {new_plan} successfully!',
            'subscription_plan': user.store.subscription_plan,
            'store': {
                'id': user.store.id,
                'name': user.store.name,
                'subscription_plan': user.store.subscription_plan
            }
        }, status=status.HTTP_200_OK)

class AdminPlatformOverviewView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        if not (user.is_superuser or user.role == 'ADMIN'):
            return Response({'error': 'Permission denied. Admin access required.'}, status=status.HTTP_403_FORBIDDEN)
        
        from .models import Store
        from inventory.models import Product

        total_stores = Store.objects.count()
        total_active_products = Product.objects.filter(is_active=True).count()
        
        starter_count = Store.objects.filter(subscription_plan='STARTER').count()
        pro_count = Store.objects.filter(subscription_plan='PRO').count()
        enterprise_count = Store.objects.filter(subscription_plan='ENTERPRISE').count()
        
        mrr = (pro_count * 29) + (enterprise_count * 79)

        stores_qs = Store.objects.select_related('owner').all()
        stores_data = []
        for store in stores_qs:
            p_count = Product.objects.filter(store=store, is_active=True).count()
            stores_data.append({
                'id': store.id,
                'name': store.name,
                'owner_id': store.owner.id,
                'owner_username': store.owner.username,
                'owner_email': store.owner.email,
                'subscription_plan': store.subscription_plan,
                'is_active': store.is_active,
                'created_at': store.created_at,
                'active_products_count': p_count
            })

        return Response({
            'kpis': {
                'total_stores': total_stores,
                'total_active_products': total_active_products,
                'starter_count': starter_count,
                'pro_count': pro_count,
                'enterprise_count': enterprise_count,
                'mrr': mrr
            },
            'stores': stores_data
        }, status=status.HTTP_200_OK)

class AdminChangeStorePlanView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        if not (user.is_superuser or user.role == 'ADMIN'):
            return Response({'error': 'Permission denied. Admin access required.'}, status=status.HTTP_403_FORBIDDEN)
        
        from .models import Store
        store_id = request.data.get('store_id')
        plan = request.data.get('plan')
        
        valid_plans = ['STARTER', 'PRO', 'ENTERPRISE']
        if plan not in valid_plans:
            return Response({'error': f'Invalid plan choice. Choose from {valid_plans}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            store = Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            return Response({'error': 'Store not found'}, status=status.HTTP_404_NOT_FOUND)

        old_plan = store.subscription_plan
        store.subscription_plan = plan
        store.save()

        log_audit_event(user, 'ADMIN_PLAN_CHANGED', f"Admin changed Store '{store.name}' plan from {old_plan} to {plan}", request)

        return Response({
            'message': f"Store '{store.name}' subscription updated to {plan}",
            'store_id': store.id,
            'new_plan': store.subscription_plan
        }, status=status.HTTP_200_OK)

class AdminToggleStoreActiveView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        if not (user.is_superuser or user.role == 'ADMIN'):
            return Response({'error': 'Permission denied. Admin access required.'}, status=status.HTTP_403_FORBIDDEN)
        
        from .models import Store
        store_id = request.data.get('store_id')
        try:
            store = Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            return Response({'error': 'Store not found'}, status=status.HTTP_404_NOT_FOUND)

        store.is_active = not store.is_active
        store.save()

        status_str = "activated" if store.is_active else "suspended"
        log_audit_event(user, f'STORE_{status_str.upper()}', f"Admin {status_str} Store '{store.name}' (ID: {store.id})", request)

        return Response({
            'message': f"Store '{store.name}' has been {status_str}.",
            'store_id': store.id,
            'is_active': store.is_active
        }, status=status.HTTP_200_OK)

class AdminAuditLogView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        if not (user.is_superuser or user.role == 'ADMIN'):
            return Response({'error': 'Permission denied. Admin access required.'}, status=status.HTTP_403_FORBIDDEN)
        
        logs = AuditLog.objects.select_related('user').all()[:100]
        data = [{
            'id': log.id,
            'user': log.user.username if log.user else 'Anonymous',
            'action': log.action,
            'details': log.details,
            'ip_address': log.ip_address,
            'created_at': log.created_at
        } for log in logs]

        return Response(data, status=status.HTTP_200_OK)

import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny

stripe.api_key = settings.STRIPE_SECRET_KEY

# Bypass strict SSL verification for local development (solves antivirus/VPN EOF errors)
stripe.verify_ssl_certs = False

class CreateStripeCheckoutSessionView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        plan = request.data.get('plan')
        
        if plan == 'PRO':
            price_id = settings.STRIPE_PRO_PRICE_ID
        elif plan == 'ENTERPRISE':
            price_id = settings.STRIPE_ENTERPRISE_PRICE_ID
        else:
            return Response({'error': 'Invalid plan.'}, status=400)

        if not hasattr(user, 'store'):
            return Response({'error': 'No store associated.'}, status=400)

        domain = "http://localhost:5173"
        try:
            customer_id = user.store.stripe_customer_id
            if not customer_id:
                customer = stripe.Customer.create(email=user.email, name=user.store.name)
                customer_id = customer.id
                user.store.stripe_customer_id = customer_id
                user.store.save()

            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                line_items=[{'price': price_id, 'quantity': 1}],
                mode='subscription',
                success_url=domain + '/payment/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain + '/payment/cancel',
                client_reference_id=str(user.store.id),
                metadata={'plan': plan}
            )
            return Response({'checkout_url': checkout_session.url})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    permission_classes = (AllowAny,) 

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            return Response(status=400)
        except stripe.error.SignatureVerificationError as e:
            return Response(status=400)
        except Exception as e:
            # If STRIPE_WEBHOOK_SECRET is empty locally, allow it to pass temporarily if not testing actual webhooks
            if not settings.STRIPE_WEBHOOK_SECRET:
                return Response(status=200)
            return Response(status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            store_id = session.get('client_reference_id')
            plan = session.get('metadata', {}).get('plan')
            sub_id = session.get('subscription')

            if store_id and plan:
                from .models import Store
                store = Store.objects.filter(id=store_id).first()
                if store:
                    old_plan = store.subscription_plan
                    store.subscription_plan = plan
                    store.stripe_subscription_id = sub_id
                    store.save()
                    log_audit_event(store.owner, 'PLAN_UPGRADED', f"Stripe webhook upgraded plan from {old_plan} to {plan}", None)

        return Response(status=200)
