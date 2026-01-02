"""
Database Migration Script
Migrates existing database to new schema:
- Drops procedures, steps, and procedureprogress tables
- Updates startup_procedures to remove FK and add progress_percent
- Updates sources table with richer fields
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("./scos.db")

def migrate():
    """Run database migration"""
    if not DB_PATH.exists():
        print("No database found. Run init_db() to create fresh schema.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Starting database migration...")
    
    try:
        # 1. Create backup of startup_procedures data
        print("1. Backing up startup_procedures...")
        cursor.execute("""
            CREATE TEMPORARY TABLE startup_procedures_backup AS 
            SELECT id, startup_id, procedure_id, completed_step_ids, assigned_at 
            FROM startup_procedures
        """)
        
        # 2. Drop deprecated tables
        print("2. Dropping deprecated tables...")
        cursor.execute("DROP TABLE IF EXISTS steps")
        cursor.execute("DROP TABLE IF EXISTS procedures")
        cursor.execute("DROP TABLE IF EXISTS procedureprogress")
        
        # 3. Drop and recreate startup_procedures without FK
        print("3. Recreating startup_procedures table...")
        cursor.execute("DROP TABLE IF EXISTS startup_procedures")
        cursor.execute("""
            CREATE TABLE startup_procedures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                startup_id INTEGER NOT NULL,
                procedure_id INTEGER NOT NULL,
                completed_step_ids TEXT NOT NULL DEFAULT '[]',
                progress_percent REAL NOT NULL DEFAULT 0.0,
                assigned_at TEXT NOT NULL,
                FOREIGN KEY (startup_id) REFERENCES startups(id)
            )
        """)
        
        # 4. Restore startup_procedures data with progress_percent
        print("4. Restoring startup_procedures data...")
        cursor.execute("""
            INSERT INTO startup_procedures (id, startup_id, procedure_id, completed_step_ids, progress_percent, assigned_at)
            SELECT id, startup_id, procedure_id, completed_step_ids, 0.0, assigned_at
            FROM startup_procedures_backup
        """)
        
        # 5. Update sources table
        print("5. Updating sources table...")
        # Check if old sources table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sources'")
        if cursor.fetchone():
            # Backup old data
            cursor.execute("PRAGMA table_info('sources')")
            columns = {row[1] for row in cursor.fetchall()}

            title_col = "title" if "title" in columns else "name"
            description_expr = "description" if "description" in columns else "NULL AS description"
            type_expr = "type" if "type" in columns else "NULL AS type"
            country_expr = "country" if "country" in columns else "NULL AS country"
            language_expr = "language" if "language" in columns else "NULL AS language"
            last_verified_expr = "last_verified" if "last_verified" in columns else "NULL AS last_verified"

            backup_sql = f"""
                CREATE TEMPORARY TABLE sources_backup AS 
                SELECT id,
                       {title_col} AS name,
                       url,
                       {description_expr},
                       {type_expr},
                       {country_expr},
                       {language_expr},
                       {last_verified_expr}
                FROM sources
            """
            cursor.execute(backup_sql)
            
            cursor.execute("DROP TABLE sources")
        
        # Create new sources table
        cursor.execute("""
            CREATE TABLE sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                description TEXT,
                type TEXT NOT NULL,
                country TEXT NOT NULL DEFAULT 'Tunisia',
                language TEXT NOT NULL DEFAULT 'fr',
                last_verified TEXT
            )
        """)
        
        # Restore old data if it existed (map name->title)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sources_backup'")
        if cursor.fetchone():
            cursor.execute("""
                INSERT INTO sources (id, title, url, description, type, country, language, last_verified)
                SELECT id, name, url, description, COALESCE(type, 'portal'), COALESCE(country, 'Tunisia'), COALESCE(language, 'fr'), last_verified
                FROM sources_backup
            """)
            print("   - Migrated existing sources data")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("   - Dropped: procedures, steps, procedureprogress tables")
        print("   - Updated: startup_procedures (removed FK, added progress_percent)")
        print("   - Updated: sources (expanded fields)")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
