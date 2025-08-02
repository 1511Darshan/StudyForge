#!/usr/bin/env python3
"""
Database initialization script for StudyForge Answer Analyzer
Run this script to set up the database and load sample data
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.models.analyzer.database import DatabaseManager
from backend.models.analyzer.sample_data import initialize_sample_data


def main():
    """Initialize the database"""
    print("Initializing StudyForge Answer Analyzer Database...")
    
    # Initialize database
    db_manager = DatabaseManager("studyforge_analyzer.db")
    print("✅ Database tables created successfully")
    
    # Load sample rubric data
    print("Loading sample rubric data...")
    initialize_sample_data(db_manager)
    print("✅ Sample data loaded successfully")
    
    print("\n🎉 Database initialization complete!")
    print("Database file: studyforge_analyzer.db")
    print("\nSample rubrics available for:")
    print("- Mathematics (2 questions)")
    print("- Physics (1 question)")  
    print("- Chemistry (1 question)")


if __name__ == "__main__":
    main()
