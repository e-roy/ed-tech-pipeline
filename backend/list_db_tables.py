#!/usr/bin/env python3
"""
List all tables in the gauntlet_pipeline database.
"""
import sys
from sqlalchemy import create_engine, inspect, text
from app.config import get_settings

def list_tables():
    """List all tables in the database."""
    settings = get_settings()
    
    print(f"Connecting to database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    print()
    
    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Create inspector
        inspector = inspect(engine)
        
        # Get all table names
        table_names = inspector.get_table_names()
        
        if not table_names:
            print("No tables found in the database.")
            return
        
        print(f"Found {len(table_names)} table(s) in database 'gauntlet_pipeline':\n")
        print("=" * 80)
        
        # List tables with details
        for i, table_name in enumerate(sorted(table_names), 1):
            print(f"\n{i}. {table_name}")
            
            # Get columns for this table
            columns = inspector.get_columns(table_name)
            print(f"   Columns ({len(columns)}):")
            for col in columns:
                col_type = str(col['type'])
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                default = f" DEFAULT {col['default']}" if col.get('default') is not None else ""
                primary_key = " [PRIMARY KEY]" if col.get('primary_key') else ""
                print(f"      - {col['name']}: {col_type} {nullable}{default}{primary_key}")
            
            # Get foreign keys
            foreign_keys = inspector.get_foreign_keys(table_name)
            if foreign_keys:
                print(f"   Foreign Keys ({len(foreign_keys)}):")
                for fk in foreign_keys:
                    print(f"      - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
            
            # Get indexes
            indexes = inspector.get_indexes(table_name)
            if indexes:
                print(f"   Indexes ({len(indexes)}):")
                for idx in indexes:
                    unique = "UNIQUE " if idx.get('unique') else ""
                    print(f"      - {unique}{idx['name']} on {idx['column_names']}")
        
        print("\n" + "=" * 80)
        print(f"\nSummary: {len(table_names)} table(s) total")
        
        # Also show table row counts if possible
        print("\nRow counts:")
        with engine.connect() as conn:
            for table_name in sorted(table_names):
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    print(f"   {table_name}: {count:,} row(s)")
                except Exception as e:
                    print(f"   {table_name}: Unable to count rows ({e})")
        
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running")
        print("  2. Database 'gauntlet_pipeline' exists")
        print("  3. DATABASE_URL in .env is correct")
        sys.exit(1)


if __name__ == '__main__':
    list_tables()

