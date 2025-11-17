"""
Seed sample educational templates for testing.

These are placeholder templates - replace with real templates later.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.database import Template

def seed_templates():
    """Add sample educational templates to database."""
    db = SessionLocal()

    # Sample templates (using placeholder URLs)
    templates = [
        {
            "template_id": "biology_photosynthesis_01",
            "name": "Photosynthesis Process Diagram",
            "category": "biology",
            "keywords": ["photosynthesis", "chlorophyll", "plant", "sunlight", "CO2", "oxygen", "glucose"],
            "psd_url": None,
            "preview_url": "https://via.placeholder.com/1792x1024/4CAF50/FFFFFF?text=Photosynthesis+Template",
            "editable_layers": ["title", "labels"]
        },
        {
            "template_id": "biology_cell_01",
            "name": "Cell Structure Diagram",
            "category": "biology",
            "keywords": ["cell", "nucleus", "mitochondria", "membrane", "organelle"],
            "psd_url": None,
            "preview_url": "https://via.placeholder.com/1792x1024/8BC34A/FFFFFF?text=Cell+Structure+Template",
            "editable_layers": ["title", "labels"]
        },
        {
            "template_id": "astronomy_solar_system_01",
            "name": "Solar System Overview",
            "category": "astronomy",
            "keywords": ["solar system", "planet", "sun", "orbit", "space"],
            "psd_url": None,
            "preview_url": "https://via.placeholder.com/1792x1024/2196F3/FFFFFF?text=Solar+System+Template",
            "editable_layers": ["title", "labels"]
        },
        {
            "template_id": "earth_science_water_cycle_01",
            "name": "Water Cycle Diagram",
            "category": "earth_science",
            "keywords": ["water cycle", "evaporation", "condensation", "precipitation", "rain"],
            "psd_url": None,
            "preview_url": "https://via.placeholder.com/1792x1024/03A9F4/FFFFFF?text=Water+Cycle+Template",
            "editable_layers": ["title", "labels"]
        },
        {
            "template_id": "physics_energy_01",
            "name": "Energy Transfer Diagram",
            "category": "physics",
            "keywords": ["energy", "kinetic", "potential", "transfer", "conservation"],
            "psd_url": None,
            "preview_url": "https://via.placeholder.com/1792x1024/FF5722/FFFFFF?text=Energy+Template",
            "editable_layers": ["title", "labels"]
        },
        {
            "template_id": "chemistry_atoms_01",
            "name": "Atomic Structure",
            "category": "chemistry",
            "keywords": ["atom", "electron", "proton", "neutron", "nucleus"],
            "psd_url": None,
            "preview_url": "https://via.placeholder.com/1792x1024/9C27B0/FFFFFF?text=Atom+Template",
            "editable_layers": ["title", "labels"]
        }
    ]

    # Check if templates already exist
    existing = db.query(Template).count()
    if existing > 0:
        print(f"Database already has {existing} templates")
        choice = input("Do you want to clear and reseed? (y/n): ")
        if choice.lower() == 'y':
            db.query(Template).delete()
            db.commit()
            print("Cleared existing templates")
        else:
            print("Keeping existing templates")
            db.close()
            return

    # Insert templates
    for t in templates:
        template = Template(**t)
        db.add(template)

    db.commit()

    print(f"\n✓ Seeded {len(templates)} templates:")
    for t in templates:
        print(f"  - {t['name']} ({t['category']})")

    db.close()

if __name__ == "__main__":
    seed_templates()
