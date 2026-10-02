from rest_framework import serializers
from .models import CustomUser, Store
from django.contrib.auth.password_validation import validate_password

class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('id', 'name', 'subscription_plan', 'created_at')

class UserSerializer(serializers.ModelSerializer):
    store = StoreSerializer(read_only=True)
    role = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'role', 'store')

    def get_role(self, obj):
        if obj.is_superuser:
            return 'ADMIN'
        return obj.role

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    store_name = serializers.CharField(write_only=True, required=True, max_length=255)

    class Meta:
        model = CustomUser
        fields = ('username', 'password', 'email', 'store_name')

    def create(self, validated_data):
        store_name = validated_data.pop('store_name')
        
        user = CustomUser.objects.create(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            role=CustomUser.STORE_OWNER
        )
        user.set_password(validated_data['password'])
        user.save()
        
        Store.objects.create(name=store_name, owner=user)
        
        return user
