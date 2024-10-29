import sqlite3
from datetime import datetime

class DatabaseClient:
    def __init__(self, db_path="chatbot_stats.db"):
        self.connection = sqlite3.connect(db_path)
        self.create_table()
        self.create_common_keywords_table()

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

    def create_common_keywords_table(self):
        # Create a table for common keywords if it doesn't exist
        with self.connection:
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS common_keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT UNIQUE,
                    count INTEGER
                )
            ''')

    def add_statistic(self, statistic, value = 0):
        # Insert a statistic entry
        with self.connection:
            self.connection.execute('''
                INSERT INTO statistics (timestamp, statistic, value) 
                VALUES (?, ?, ?)
            ''', (datetime.now().isoformat(), statistic, value))

    def get_latest_stat(self, statistic):
        # Retrieve the most recent value for a statistic
        if statistic == 'common_keywords':
            return self.get_common_keywords()
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT value FROM statistics 
            WHERE statistic = ? 
            ORDER BY timestamp DESC LIMIT 1
        ''', (statistic,))
        result = cursor.fetchone()
        return result[0] if result else ""  # Default to "" if no data
    
    def get_common_keywords(self, limit=5):
        # Retrieve the most common keywords
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT keyword, count FROM common_keywords 
            ORDER BY count DESC LIMIT ?
        ''', (limit,))

        result = cursor.fetchall()
        if result is None or result == []:
            return None
        
        # Convert the list of tuples to a comma separated string
        # for example, [('keyword1', 5), ('keyword2', 3)] -> 'keyword1, keyword2'
        keywords_list = [keyword for keyword, _ in result]
        keywords = ', '.join(keywords_list)
        return keywords
    
    def insert_common_keywords(self, keywords):
        if keywords is None:
            return
        with self.connection:
            for keyword in keywords:
                self.connection.execute('''
                    INSERT INTO common_keywords (keyword, count)
                    VALUES (?, 1)
                    ON CONFLICT(keyword) DO UPDATE SET count = count + 1
                    ''', (keyword,))

    def increment_statistic(self, statistic, increment_value=1):
        """
        Increment or decrement the value of a statistic.
    
        Args:
            statistic (str): The statistic to be updated.
            increment_value (int): The amount to increment or decrement the statistic by.
        """
        current_value = self.get_latest_stat(statistic)
        current_value = float(current_value) if isinstance(current_value, (int, float)) else 0
        self.add_statistic(statistic, current_value + increment_value)
