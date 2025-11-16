"""
Template Matcher Agent

Finds the best matching educational template based on visual guidance
and key concepts from script.
"""
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.database import Template
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TemplateMatcher:
    """Matches script content to educational templates."""

    def __init__(self):
        self.db: Optional[Session] = None

    def _get_db(self) -> Session:
        """Get database session."""
        if self.db is None:
            self.db = SessionLocal()
        return self.db

    def match_template(
        self,
        visual_guidance: str,
        key_concepts: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Find best matching template based on visual guidance and concepts.

        Args:
            visual_guidance: Description of what visual should show
            key_concepts: List of key concepts to visualize

        Returns:
            Template dict or None if no match found
        """
        try:
            db = self._get_db()

            # Load all templates
            templates = db.query(Template).all()

            if not templates:
                logger.warning("No templates found in database")
                return None

            # Score each template based on keyword matches
            best_match = None
            best_score = 0

            for template in templates:
                score = self._calculate_match_score(
                    template,
                    visual_guidance,
                    key_concepts
                )

                if score > best_score:
                    best_score = score
                    best_match = template

            # Require minimum score threshold
            if best_score < 1:
                logger.debug("No template matched above threshold")
                return None

            if best_match:
                logger.info(
                    f"Matched template: {best_match.name} "
                    f"(score: {best_score})"
                )

                return {
                    'id': best_match.id,
                    'template_id': best_match.template_id,
                    'name': best_match.name,
                    'category': best_match.category,
                    'psd_url': best_match.psd_url,
                    'preview_url': best_match.preview_url,
                    'editable_layers': best_match.editable_layers,
                    'keywords': best_match.keywords
                }

            return None

        except Exception as e:
            logger.error(f"Template matching error: {e}")
            return None

    def _calculate_match_score(
        self,
        template: Template,
        visual_guidance: str,
        key_concepts: List[str]
    ) -> int:
        """
        Calculate match score for a template.

        Args:
            template: Template to score
            visual_guidance: Visual description
            key_concepts: Key concepts list

        Returns:
            Match score (higher is better)
        """
        score = 0
        template_keywords = template.keywords or []

        # Combine all text to search
        search_text = (
            f"{visual_guidance} {' '.join(key_concepts)}"
        ).lower()

        # Check keyword matches
        for keyword in template_keywords:
            if keyword.lower() in search_text:
                score += 2  # Weight keyword matches heavily

        # Check category in text
        if template.category.lower().replace('_', ' ') in search_text:
            score += 1

        return score

    def close(self):
        """Close database connection."""
        if self.db:
            self.db.close()
            self.db = None

    def __del__(self):
        """Cleanup on deletion."""
        self.close()
