#!/usr/bin/env python
"""
Script to initialize default spending categories
Run this after setting up the database and running migrations
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import SpendingCategory

def init_categories():
    """Initialize default spending categories"""
    
    default_categories = [
        {
            'name': 'Food & Dining',
            'description': 'Restaurants, groceries, and food delivery',
            'color': '#FF6B6B',
            'icon': '🍽️'
        },
        {
            'name': 'Transportation',
            'description': 'Gas, public transit, rideshare, and parking',
            'color': '#4ECDC4',
            'icon': '🚗'
        },
        {
            'name': 'Shopping',
            'description': 'Retail purchases, online shopping, and clothing',
            'color': '#45B7D1',
            'icon': '🛍️'
        },
        {
            'name': 'Entertainment',
            'description': 'Movies, streaming services, and leisure activities',
            'color': '#96CEB4',
            'icon': '🎬'
        },
        {
            'name': 'Utilities',
            'description': 'Electricity, water, internet, and phone bills',
            'color': '#FFEAA7',
            'icon': '💡'
        },
        {
            'name': 'Healthcare',
            'description': 'Medical expenses, prescriptions, and insurance',
            'color': '#DDA0DD',
            'icon': '🏥'
        },
        {
            'name': 'Income',
            'description': 'Salary, bonuses, and other income sources',
            'color': '#98D8C8',
            'icon': '💰'
        },
        {
            'name': 'Other',
            'description': 'Miscellaneous expenses and uncategorized items',
            'color': '#F7DC6F',
            'icon': '📦'
        }
    ]
    
    created_count = 0
    for category_data in default_categories:
        category, created = SpendingCategory.objects.get_or_create(
            name=category_data['name'],
            defaults={
                'description': category_data['description'],
                'color': category_data['color'],
                'icon': category_data['icon']
            }
        )
        if created:
            created_count += 1
            print(f"Created category: {category.name}")
        else:
            print(f"Category already exists: {category.name}")
    
    print(f"\nTotal categories created: {created_count}")
    print(f"Total categories in database: {SpendingCategory.objects.count()}")

if __name__ == '__main__':
    print("Initializing default spending categories...")
    init_categories()
    print("Done!")
