"""
SQLite dummy data seeding script for local development.
Inserts realistic test data into the Charting AI database.
"""
import os
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

# Sample data pools
REGIONS = ['East', 'West', 'North', 'South']
INDUSTRIES = ['Tech', 'Finance', 'Retail', 'Health', None]
ROLES = ['Manager', 'Developer', 'Analyst', 'Sales Rep']
LEAD_SOURCES = ['Web', 'Email Campaign', 'Phone Call', 'Partner']
LEAD_STATUSES = ['New', 'Contacted', 'Qualified', 'Lost']
OPPORTUNITY_STAGES = ['Qualify', 'Proposal', 'Closed Won', 'Closed Lost']

# Realistic first and last names
FIRST_NAMES = [
    'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
    'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
    'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Nancy', 'Daniel', 'Lisa',
    'Matthew', 'Betty', 'Anthony', 'Margaret', 'Mark', 'Sandra'
]

LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Wilson', 'Anderson', 'Thomas', 'Taylor',
    'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White', 'Harris', 'Sanchez',
    'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker', 'Young'
]


def get_db_path():
    """Get SQLite database path from environment or use default."""
    from backend.config import get_absolute_sqlite_path
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///./backend/data/charting_ai.db')
    
    # Use absolute path function (single source of truth)
    if database_url.startswith('sqlite:///'):
        db_path = get_absolute_sqlite_path(database_url)
    else:
        db_path = database_url
    
    return db_path


def random_date(start_year=2023, end_year=2025):
    """Generate a random date between start_year and end_year."""
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    random_date = start_date + timedelta(days=random_days)
    return random_date.strftime('%Y-%m-%d')


def seed_accounts(cursor):
    """Seed Account table with 30 rows."""
    inserted = 0
    for account_id in range(1, 31):
        account_name = f'Account_{account_id}'
        region = random.choice(REGIONS)
        industry = random.choice(INDUSTRIES)
        revenue = round(random.uniform(10000, 1000000), 2) if random.random() > 0.1 else None
        created_date = random_date()
        
        cursor.execute("""
            INSERT OR IGNORE INTO Account 
            (AccountID, AccountName, Region, Industry, Revenue, CreatedDate)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (account_id, account_name, region, industry, revenue, created_date))
        
        if cursor.rowcount > 0:
            inserted += 1
    
    return inserted


def seed_contacts(cursor):
    """Seed Contact table with 30 rows."""
    inserted = 0
    for contact_id in range(1, 31):
        account_id = random.randint(1, 30)  # Random existing AccountID
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        full_name = f'{first_name} {last_name}'
        role = random.choice(ROLES)
        email = f'{first_name.lower()}.{last_name.lower()}@example.com'
        created_date = random_date()
        
        cursor.execute("""
            INSERT OR IGNORE INTO Contact 
            (ContactID, AccountID, FullName, Role, Email, CreatedDate)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (contact_id, account_id, full_name, role, email, created_date))
        
        if cursor.rowcount > 0:
            inserted += 1
    
    return inserted


def seed_leads(cursor):
    """Seed Lead table with 20 rows."""
    inserted = 0
    for lead_id in range(1, 21):
        account_id = random.randint(1, 30)  # Random existing AccountID
        lead_source = random.choice(LEAD_SOURCES)
        status = random.choice(LEAD_STATUSES)
        budget = round(random.uniform(5000, 500000), 2) if random.random() > 0.15 else None
        created_date = random_date()
        
        cursor.execute("""
            INSERT OR IGNORE INTO Lead 
            (LeadID, AccountID, LeadSource, Status, Budget, CreatedDate)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (lead_id, account_id, lead_source, status, budget, created_date))
        
        if cursor.rowcount > 0:
            inserted += 1
    
    return inserted


def seed_opportunities(cursor):
    """Seed Opportunity table with 20 rows."""
    inserted = 0
    for opp_id in range(1, 21):
        account_id = random.randint(1, 30)  # Random existing AccountID
        opportunity_name = f'Opportunity_{opp_id}'
        stage = random.choice(OPPORTUNITY_STAGES)
        value = round(random.uniform(10000, 2000000), 2) if random.random() > 0.1 else None
        # Expected close date should be in the future or recent past
        expected_close_date = random_date(2024, 2026)
        
        cursor.execute("""
            INSERT OR IGNORE INTO Opportunity 
            (OpportunityID, AccountID, OpportunityName, Stage, Value, ExpectedCloseDate)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (opp_id, account_id, opportunity_name, stage, value, expected_close_date))
        
        if cursor.rowcount > 0:
            inserted += 1
    
    return inserted


def main():
    """Main seeding function."""
    db_path = get_db_path()
    
    # Ensure data directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        Path(db_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Seed data
        accounts_inserted = seed_accounts(cursor)
        contacts_inserted = seed_contacts(cursor)
        leads_inserted = seed_leads(cursor)
        opportunities_inserted = seed_opportunities(cursor)
        
        # Commit changes
        conn.commit()
        conn.close()
        
        # Print summary
        print("=" * 50)
        print("SQLite Data Seeding Summary")
        print("=" * 50)
        print(f"Inserted {accounts_inserted} Accounts")
        print(f"Inserted {contacts_inserted} Contacts")
        print(f"Inserted {leads_inserted} Leads")
        print(f"Inserted {opportunities_inserted} Opportunities")
        print("=" * 50)
        print(f"Total rows inserted: {accounts_inserted + contacts_inserted + leads_inserted + opportunities_inserted}")
        print(f"Database: {db_path}")
        print("=" * 50)
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        exit(1)


if __name__ == '__main__':
    main()

