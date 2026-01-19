from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, BankAccount, SpendingCategory, Transaction, APIKey

class User_Serialzier(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, value):
        # Check if username exists but user is not verified
        if User.objects.filter(username=value, is_active=False).exists():
            # Allow re-registration for unverified users
            return value
        elif User.objects.filter(username=value, is_active=True).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate_email(self, value):
        # Check if email exists but user is not verified
        if User.objects.filter(email=value, is_active=False).exists():
            # Allow re-registration for unverified users
            return value
        elif User.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        # Don't create UserProfile here - it will be created in the view
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at', 'consent_date')

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = '__all__'
        read_only_fields = ('user', 'last_updated')

class SpendingCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SpendingCategory
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    category_names = serializers.SerializerMethodField()
    primary_category_name = serializers.SerializerMethodField()
    account_name = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

    def get_category_names(self, obj):
        return [cat.name for cat in obj.category.all()]

    def get_primary_category_name(self, obj):
        return obj.primary_category.name if obj.primary_category else None

    def get_account_name(self, obj):
        return obj.account.name


class APIKeySerializer(serializers.ModelSerializer):
    """Serializer for API Key model"""
    key = serializers.CharField(read_only=True, help_text="The API key (only shown on creation)")
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = APIKey
        fields = [
            'id', 'name', 'key', 'user', 'is_active', 
            'rate_limit_per_minute', 'rate_limit_per_hour', 'rate_limit_per_day',
            'last_used', 'created_at', 'expires_at', 'is_expired', 'is_valid'
        ]
        read_only_fields = ('key', 'user', 'last_used', 'created_at')



