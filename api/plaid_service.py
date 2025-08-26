import os
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from django.conf import settings
from datetime import datetime, timedelta
import json

class PlaidService:
    def __init__(self):
        client_id = os.getenv('PLAID_CLIENT_ID')
        secret = os.getenv('PLAID_SECRET')
        
        if not client_id or not secret:
            raise ValueError("PLAID_CLIENT_ID and PLAID_SECRET environment variables must be set")
        
        print(f"PlaidService: Initializing with client_id: {client_id[:10]}...")
        
        self.client = plaid.ApiClient(
            plaid.Configuration(
                host=plaid.Environment.production,  # Change to Development or Production
                api_key={
                    'clientId': client_id,
                    'secret': secret,
                }
            )
        )
        self.plaid_api = plaid_api.PlaidApi(self.client)

    def create_link_token(self, user_id):
        """Create a link token for Plaid Link"""
        print(f"PlaidService: Creating link token for user {user_id}")
        print(f"PlaidService: Client ID: {os.getenv('PLAID_CLIENT_ID', 'NOT_SET')}")
        print(f"PlaidService: Secret: {os.getenv('PLAID_SECRET', 'NOT_SET')[:10]}..." if os.getenv('PLAID_SECRET') else "NOT_SET")
        
        request = LinkTokenCreateRequest(
            products=[Products("transactions")],
            client_name="Spending Tracker",
            country_codes=[CountryCode("US")],
            language="en",
            user=LinkTokenCreateRequestUser(
                client_user_id=str(user_id)
            )
        )
        
        print(f"PlaidService: Sending request to Plaid API")
        response = self.plaid_api.link_token_create(request)
        print(f"PlaidService: Response received, link_token: {response.link_token[:20]}..." if response.link_token else "No token")
        return response.link_token

    def exchange_public_token(self, public_token):
        """Exchange public token for access token"""
        request = ItemPublicTokenExchangeRequest(
            public_token=public_token
        )
        
        response = self.plaid_api.item_public_token_exchange(request)
        return response.access_token, response.item_id

    def get_accounts(self, access_token):
        """Get user's bank accounts"""
        request = AccountsBalanceGetRequest(
            access_token=access_token
        )
        
        response = self.plaid_api.accounts_balance_get(request)
        return response.accounts

    def sync_transactions(self, access_token, cursor=None):
        """Sync transactions from Plaid"""
        if cursor:
            request = TransactionsSyncRequest(
                access_token=access_token,
                cursor=cursor
            )
        else:
            request = TransactionsSyncRequest(
                access_token=access_token
            )
        
        response = self.plaid_api.transactions_sync(request)
        return response

    def get_transactions(self, access_token, start_date, end_date, account_ids=None):
        """Get transactions for a date range"""
        options = TransactionsGetRequestOptions()
        if account_ids:
            options.account_ids = account_ids

        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
            options=options
        )
        
        response = self.plaid_api.transactions_get(request)
        return response.transactions

    def categorize_transaction(self, transaction_name, amount):
        """Enhanced categorization logic for Plaid sandbox and real transactions"""
        name_lower = transaction_name.lower()
        
        # Food and Dining
        if any(keyword in name_lower for keyword in ['mcdonalds', 'starbucks', 'restaurant', 'food', 'dining', 'grubhub', 'doordash', 'uber eats', 'pizza', 'burger', 'coffee', 'cafe', 'bakery', 'deli']):
            return 'Food & Dining'
        
        # Transportation
        elif any(keyword in name_lower for keyword in ['uber', 'lyft', 'taxi', 'gas', 'shell', 'exxon', 'chevron', 'parking', 'metro', 'bus', 'train', 'subway', 'airport', 'car', 'auto']):
            return 'Transportation'
        
        # Shopping
        elif any(keyword in name_lower for keyword in ['amazon', 'walmart', 'target', 'costco', 'best buy', 'apple', 'nike', 'adidas', 'store', 'shop', 'mall', 'outlet', 'retail']):
            return 'Shopping'
        
        # Entertainment
        elif any(keyword in name_lower for keyword in ['netflix', 'spotify', 'hulu', 'disney', 'movie', 'theater', 'concert', 'game', 'entertainment', 'amusement', 'park', 'zoo', 'museum']):
            return 'Entertainment'
        
        # Utilities
        elif any(keyword in name_lower for keyword in ['electric', 'water', 'gas', 'internet', 'phone', 'cable', 'utility', 'power', 'energy', 'heating', 'cooling']):
            return 'Utilities'
        
        # Healthcare
        elif any(keyword in name_lower for keyword in ['pharmacy', 'doctor', 'hospital', 'medical', 'dental', 'vision', 'health', 'clinic', 'physician', 'therapy']):
            return 'Healthcare'
        
        # Banking and Financial
        elif any(keyword in name_lower for keyword in ['bank', 'atm', 'withdrawal', 'deposit', 'transfer', 'payment', 'fee', 'interest', 'credit', 'debit']):
            return 'Banking & Financial'
        
        # Income
        elif amount > 0:
            return 'Income'
        
        # Plaid Sandbox specific patterns
        elif any(keyword in name_lower for keyword in ['plaid', 'sandbox', 'test', 'demo']):
            return 'Test Transactions'
        
        else:
            return 'Other'
