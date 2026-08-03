#!/usr/bin/env python3
"""
Load generated content JSON to PostgreSQL database

Usage:
  python scripts/load_content_to_db.py --file output/sprint1_month_1_*.json
"""
import json
import psycopg2
from pathlib import Path
from datetime import datetime


class ContentLoader:
    def __init__(self, db_config=None):
        if not db_config:
            db_config = {
                "host": "localhost",
                "database": "aif369_master",
                "user": "postgres",
                "password": "",
                "port": 5432,
            }
        self.db_config = db_config
        self.conn = None
        self.cursor = None

    def connect(self):
        """Connect to PostgreSQL"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            print("✓ Connected to PostgreSQL")
        except psycopg2.Error as e:
            print(f"❌ Connection failed: {e}")
            return False
        return True

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("✓ Database connection closed")

    def load_lessons(self, month_data):
        """Load lessons from month data"""
        lessons = month_data.get("lessons", {})
        count = 0

        for lesson_id, lesson in lessons.items():
            try:
                # Insert lesson
                self.cursor.execute(
                    """
                    INSERT INTO lessons
                    (id, title, summary, estimated_minutes, content, learning_objectives,
                     status, requires_legal_review, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        lesson.get("id"),
                        lesson.get("title"),
                        lesson.get("summary"),
                        lesson.get("estimated_minutes"),
                        json.dumps(lesson.get("content_sections", [])),
                        json.dumps(lesson.get("learning_objectives", [])),
                        "draft",
                        lesson.get("requires_legal_review", False),
                        datetime.now(),
                    ),
                )
                count += 1
                print(f"  ✓ Loaded: {lesson.get('title')[:50]}")

            except psycopg2.Error as e:
                print(f"  ❌ Error loading lesson {lesson_id}: {e}")

        self.conn.commit()
        return count

    def load_labs(self, month_data):
        """Load labs from month data"""
        labs = month_data.get("labs", {})
        count = 0

        for lab_id, lab in labs.items():
            try:
                self.cursor.execute(
                    """
                    INSERT INTO labs
                    (id, title, description, difficulty, estimated_hours,
                     setup_instructions, steps, validation_criteria, tools_required,
                     status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        lab.get("id"),
                        lab.get("title"),
                        lab.get("description"),
                        lab.get("difficulty"),
                        lab.get("estimated_hours"),
                        lab.get("setup_instructions"),
                        json.dumps(lab.get("steps", [])),
                        json.dumps(lab.get("validation_criteria", [])),
                        json.dumps(lab.get("tools_required", [])),
                        "draft",
                        datetime.now(),
                    ),
                )
                count += 1
                print(f"  ✓ Loaded: {lab.get('title')[:50]}")

            except psycopg2.Error as e:
                print(f"  ❌ Error loading lab {lab_id}: {e}")

        self.conn.commit()
        return count

    def load_json_file(self, filepath):
        """Load content from JSON file"""
        print(f"\n📂 Loading: {filepath}")

        with open(filepath, "r") as f:
            data = json.load(f)

        total_lessons = 0
        total_labs = 0

        for month_key, month_data in data.get("content", {}).items():
            month_num = month_data.get("month")
            print(f"\n  📚 Month {month_num}: {month_data.get('title')}")

            lessons_count = self.load_lessons(month_data)
            labs_count = self.load_labs(month_data)

            total_lessons += lessons_count
            total_labs += labs_count

        return {
            "total_lessons": total_lessons,
            "total_labs": total_labs,
            "total_items": total_lessons + total_labs,
        }

    def get_stats(self):
        """Get database stats"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM lessons")
            lessons_count = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT COUNT(*) FROM labs")
            labs_count = self.cursor.fetchone()[0]

            return {
                "lessons": lessons_count,
                "labs": labs_count,
                "total": lessons_count + labs_count,
            }
        except:
            return None


def main():
    import argparse
    import glob

    parser = argparse.ArgumentParser(description="Load generated content to database")
    parser.add_argument(
        "--file",
        type=str,
        help="JSON file to load (or pattern like output/sprint1_*.json)",
    )
    parser.add_argument(
        "--db-host", default="localhost", help="PostgreSQL host"
    )
    parser.add_argument(
        "--db-name", default="aif369_master", help="Database name"
    )
    parser.add_argument(
        "--db-user", default="postgres", help="Database user"
    )

    args = parser.parse_args()

    # Find files
    files = []
    if args.file:
        if "*" in args.file:
            files = sorted(glob.glob(args.file))
        else:
            files = [args.file]

    if not files:
        print("❌ No files found. Usage: --file output/sprint1_*.json")
        return

    # Connect to database
    loader = ContentLoader(
        {
            "host": args.db_host,
            "database": args.db_name,
            "user": args.db_user,
            "port": 5432,
        }
    )

    if not loader.connect():
        return

    try:
        print("\n" + "=" * 60)
        print("  LOADING CONTENT TO DATABASE")
        print("=" * 60)

        total_lessons = 0
        total_labs = 0

        for filepath in files:
            results = loader.load_json_file(filepath)
            total_lessons += results["total_lessons"]
            total_labs += results["total_labs"]

        # Get final stats
        stats = loader.get_stats()

        print("\n" + "=" * 60)
        print("  ✓ LOAD COMPLETE")
        print("=" * 60)
        print(f"  Lessons loaded: {total_lessons}")
        print(f"  Labs loaded:    {total_labs}")
        print(f"  Total items:    {total_lessons + total_labs}")
        if stats:
            print(f"\n  Database stats:")
            print(f"    Total lessons in DB: {stats['lessons']}")
            print(f"    Total labs in DB:    {stats['labs']}")
            print(f"    Total items in DB:   {stats['total']}")
        print("=" * 60 + "\n")

    finally:
        loader.close()


if __name__ == "__main__":
    main()
