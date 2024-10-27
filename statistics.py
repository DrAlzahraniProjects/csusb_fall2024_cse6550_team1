import sqlite3
from datetime import datetime

class DatabaseClient:
    def __init__(self, db_path="chatbot_stats.db"):
        self.connection = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        # Create a table for statistics if it doesn't exist
        with self.connection:
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    statistic TEXT,
                    value REAL
                )
            ''')

    def add_statistic(self, statistic_name, value):
        # Insert a statistic entry
        with self.connection:
            self.connection.execute('''
                INSERT INTO statistics (timestamp, statistic, value) 
                VALUES (?, ?, ?)
            ''', (datetime.now().isoformat(), statistic_name, value))

    def get_latest_stat(self, statistic_name):
        # Retrieve the most recent value for a statistic
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT value FROM statistics 
            WHERE statistic = ? 
            ORDER BY timestamp DESC LIMIT 1
        ''', (statistic_name,))
        result = cursor.fetchone()
        return result[0] if result else ""  # Default to "" if no data

    def increment_statistic(self, statistic_name, increment_value=1):
        """
        Increment or decrement the value of a statistic.
    
        Args:
            statistic_name (str): The name of the statistic to update.
            increment_value (int): The amount to increment or decrement the statistic by.
        """
        current_value = self.get_latest_stat(statistic_name)
        current_value = float(current_value) if isinstance(current_value, (int, float)) else 0
        self.add_statistic(statistic_name, current_value + increment_value)
