#!/usr/bin/env python3
"""
Test script to retrieve a script from the database
"""
from app.database import SessionLocal
from app.models.database import Script
import json

# Get database session
db = SessionLocal()

try:
    # Get all scripts (or filter by script_id)
    scripts = db.query(Script).all()

    if not scripts:
        print("No scripts found in database")
    else:
        print(f"Found {len(scripts)} script(s):\n")

        for script in scripts:
            print(f"{'='*60}")
            print(f"Script ID: {script.id}")
            print(f"User ID: {script.user_id}")
            print(f"Created: {script.created_at}")
            print(f"\nHook: {json.dumps(script.hook, indent=2)}")
            print(f"\nConcept: {json.dumps(script.concept, indent=2)}")
            print(f"\nProcess: {json.dumps(script.process, indent=2)}")
            print(f"\nConclusion: {json.dumps(script.conclusion, indent=2)}")
            print(f"{'='*60}\n")

finally:
    db.close()
