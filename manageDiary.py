import sqlite3


class ManageDiary:
    def __init__(self):
        DB_FILE_PATH = "diary.db"
        self.db_file = DB_FILE_PATH
        self.create_table()

    def create_table(self):
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS diary (
                    date INTEGER PRIMARY KEY,
                    content TEXT,
                    img_file_name TEXT,
                    audio_file_name TEXT
                )
            """
            )
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")
        finally:
            conn.close()

    def add_entry(self, date, content, img_file_name, audio_file_name):
        result = False
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO diary (date, content, img_file_name, audio_file_name)
                VALUES (?, ?, ?, ?)
            """,
                (date, content, img_file_name, audio_file_name),
            )
            conn.commit()
            result = True
        except sqlite3.Error as e:
            print(f"Error adding entry: {e}")
        finally:
            conn.close()
            return result

    def view_entries(self):
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute(
                """
                SELECT * FROM diary
            """
            )
            entries = c.fetchall()
            return entries
        except sqlite3.Error as e:
            print(f"Error viewing entries: {e}")
        finally:
            conn.close()

    def view_entry(self, date):
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute(
                """
                SELECT * FROM diary WHERE date = ?
            """,
                [date],
            )
            entry = c.fetchone()
            return entry
        except sqlite3.Error as e:
            print(f"Error viewing entry: {e}")
        finally:
            conn.close()

    def update_entry(self, date, content, img_file_name, audio_file_name):
        result = False
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute(
                """
                UPDATE diary
                SET content = ?, img_file_name = ?, audio_file_name = ?
                WHERE date = ?
            """,
                (content, img_file_name, audio_file_name, date),
            )
            conn.commit()
            result = True
        except sqlite3.Error as e:
            print(f"Error updating entry: {e}")
        finally:
            conn.close()
            return result

    def delete_entry(self, entry_id):
        result = False
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute(
                """
                DELETE FROM diary
                WHERE date = ?
            """,
                (entry_id,),
            )
            conn.commit()
            result = True
        except sqlite3.Error as e:
            print(f"Error deleting entry: {e}")
        finally:
            conn.close()
            return result
