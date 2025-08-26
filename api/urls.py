from django.urls import path
from . import views

urlpatterns = [
    # API Root
    path('', views.api_root, name='api-root'),
    
    # Authentication
    path('register/', views.CreateUser.as_view(), name='register'),
    path('login/', views.login_view, name='login'),
    path('verify-email/', views.verify_email, name='verify-email'),
    path('resend-verification/', views.resend_verification, name='resend-verification'),
    path('check-user-status/', views.check_user_status, name='check-user-status'),
    path('delete-unverified-user/', views.delete_unverified_user, name='delete-unverified-user'),
    path('test-email/', views.test_email, name='test-email'),
    
    # User Profile
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    
    # Consent Management
    path('consent/status/', views.get_consent_status, name='get-consent-status'),
    path('consent/update/', views.update_consent, name='update-consent'),
    
    # Security Management
    path('security/audit/', views.security_audit, name='security-audit'),
    path('security/status/', views.security_status, name='security-status'),
    
    # Plaid Integration
    path('plaid/create-link-token/', views.create_link_token, name='create-link-token'),
    path('plaid/exchange-token/', views.exchange_token, name='exchange-token'),
    path('plaid/sync-transactions/', views.sync_transactions, name='sync-transactions'),
    
    # Bank Accounts
    path('accounts/', views.BankAccountList.as_view(), name='accounts'),
    
    # Spending Categories
    path('categories/', views.SpendingCategoryList.as_view(), name='categories'),
    
    # Transactions
    path('transactions/', views.TransactionList.as_view(), name='transactions'),
    
    # Auto Tag Rules
    path('auto-tag-rules/', views.AutoTagRuleList.as_view(), name='auto-tag-rules'),
    path('auto-tag-rules/<int:pk>/', views.AutoTagRuleDetail.as_view(), name='auto-tag-rule-detail'),
    path('auto-tag-rules/apply/', views.apply_auto_tags, name='apply-auto-tags'),
    
    # Analytics
    path('spending-summary/', views.spending_summary, name='spending-summary'),
    
    # Debug
    path('debug/transactions/', views.debug_transactions, name='debug-transactions'),
    
    # Security Attestations
    path('security/attestations/', views.security_attestations, name='security-attestations'),
]
