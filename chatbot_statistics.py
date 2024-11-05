import sqlite3
from datetime import datetime

PERFORMANCE_METRICS_ROW_ID = 1
class DatabaseClient:
    def __init__(self, db_path="chatbot_stats.db"):
        self.connection = sqlite3.connect(db_path)

    def create_stats_table(self):
        # Create a table for statistics if it doesn't exist
        with self.connection:
            self.connection.execute("DROP TABLE IF EXISTS statistics;")  # Drop the table if it exists
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
            self.connection.execute("DROP TABLE IF EXISTS common_keywords;")  # Drop the table if it exists
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS common_keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT UNIQUE,
                    count INTEGER
                )
            ''')
        
    def create_performance_metrics_table(self):
        # Create a table for metrics if it doesn't exist
        with self.connection:
            self.connection.execute("DROP TABLE IF EXISTS performance_metrics;")
            self.connection.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                true_positive INTEGER,
                true_negative INTEGER,
                false_positive INTEGER,
                false_negative INTEGER,
                accuracy REAL,
                precision REAL,
                sensitivity REAL,
                specificity REAL,
                f1_score REAL
            )
        ''')
        # Insert a default row if the table is empty
            self.connection.execute('''
                INSERT INTO performance_metrics (id, true_positive, true_negative, false_positive, false_negative, accuracy, precision, sensitivity, specificity, f1_score)
                VALUES (1, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)
            ''')

    def increment_performance_metric(self, metric, increment_value=1):
        """
        Increment a performance metric by a given value

        Args:
            metric (str): The metric to be incremented.
            increment_value (int, optional): The amount to increment the metric by. Defaults to 1.
        """

        valid_metrics = {'true_positive', 'true_negative', 'false_positive', 'false_negative'}
        if metric not in valid_metrics:
            raise ValueError(f"Invalid metric: {metric}. Valid metrics are {valid_metrics}")

        # Increment a metric by a given value
        with self.connection:
            self.connection.execute(f'''
                UPDATE performance_metrics
                SET {metric} = CASE
                    WHEN {metric} + ? < 0 THEN 0
                    ELSE {metric} + ?
                END
                WHERE id = ?
            ''', (increment_value, increment_value, PERFORMANCE_METRICS_ROW_ID))

    def safe_division(self, numerator, denominator, default=None):
        # Perform division and return a default value if the denominator is zero
        if denominator == 0:
            return default
        return round(numerator / denominator, 3)


    def update_performance_metrics(self):
        """
        Update the performance metrics with the provided values

        Args:
            metrics (dict): A dictionary containing the performance metrics
        """
        metrics = self.get_performance_metrics('true_positive, true_negative, false_positive, false_negative')
        accuracy = self.safe_division(metrics['true_positive'] + metrics['true_negative'], metrics['true_positive'] + metrics['true_negative'] + metrics['false_positive'] + metrics['false_negative'])
        precision = self.safe_division(metrics['true_positive'], metrics['true_positive'] + metrics['false_positive'])
        sensitivity = self.safe_division(metrics['true_positive'], metrics['true_positive'] + metrics['false_negative'])
        specificity = self.safe_division(metrics['true_negative'], metrics['true_negative'] + metrics['false_positive'])
        if precision is None or sensitivity is None:
            f1_score = None
        else:
            f1_score = self.safe_division(2 * precision * sensitivity, precision + sensitivity)

        with self.connection:
            self.connection.execute('''
                UPDATE performance_metrics
                SET accuracy = ?, precision = ?, sensitivity = ?, specificity = ?, f1_score = ?
                WHERE id = ?
            ''', (accuracy, precision, sensitivity, specificity, f1_score, PERFORMANCE_METRICS_ROW_ID))


    def get_performance_metrics(self, columns='*'):
        """
        Fetch the performance metrics from the database

        Returns:
            result(dict): A dictionary containing the performance metrics
        """
        cursor = self.connection.cursor()
        cursor.row_factory = sqlite3.Row
        cursor.execute(f'''
            SELECT {columns} FROM performance_metrics
            WHERE id = ?
        ''', (PERFORMANCE_METRICS_ROW_ID,))
        result = cursor.fetchone()
        if not result:
            return {}
        return dict(result)
    
    def reset_performance_metrics(self):
        """
        Reset the performance metrics to zero
        """
        with self.connection:
            self.connection.execute('''
                UPDATE performance_metrics
                SET true_positive = 0, true_negative = 0, false_positive = 0, false_negative = 0, accuracy = 0.0, precision = 0.0, sensitivity = 0.0, specificity = 0.0, f1_score = 0.0
                WHERE id = ?
            ''', (PERFORMANCE_METRICS_ROW_ID,))

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
