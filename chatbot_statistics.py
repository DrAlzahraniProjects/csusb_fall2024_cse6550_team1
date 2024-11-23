import sqlite3
from logger import Logger
from datetime import datetime

PERFORMANCE_METRICS_ROW_ID = 1
class DatabaseClient:
    """
    A class to interact with the SQLite database for storing performance metrics
    """
    def __init__(self, db_path="chatbot_stats.db"):
        self.connection = sqlite3.connect(db_path)
        self.logger = Logger("chatbot_statistics")
        
    def create_performance_metrics_table(self):
        """
        Create a table for performance metrics if it doesn't exist
        """
        with self.connection:
            self.connection.execute("DROP TABLE IF EXISTS performance_metrics;")
            self.connection.execute('''
            CREATE TABLE performance_metrics (
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
        self.logger.debug("Created table 'performance_metrics'.")

    def insert_default_performance_metrics(self):
        """
        Insert a default row of performance metrics into the database
        """
        with self.connection:
            self.connection.execute('''
                    INSERT INTO performance_metrics (id, true_positive, true_negative, false_positive, false_negative, accuracy, precision, sensitivity, specificity, f1_score)
                    VALUES (1, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)
                ''')
            self.logger.debug("Inserted default row into 'performance_metrics' table.")


    def increment_performance_metric(self, metric: str, increment_value: int = 1):
        """
        Increment a performance metric by a given value

        Args:
            metric (str): The metric to be incremented.
            increment_value (int, optional): The amount to increment the metric by. Defaults to 1.
        """

        valid_metrics = {'true_positive', 'true_negative', 'false_positive', 'false_negative'}
        if metric not in valid_metrics:
            self.logger.error(f"Invalid metric: {metric}")
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
            self.logger.debug(f"Incremented {metric} by {increment_value}.")
    def safe_divide(self, numerator: int, denominator: int, default: float = None):
        """
        Safely divide two numbers and return the result. If the denominator is zero, return the default value.

        Args:
            numerator (int): The numerator of the division.
            denominator (int): The denominator of the division.
            default (float, optional): The default value to return if the denominator is zero. Defaults to None.

        Returns:
            float: The result of the division, or None if the denominator is zero
        """
        if denominator == 0:
            self.logger.error(f"Division by zero")
            return default
        return round(numerator / denominator, 3)


    def update_performance_metrics(self):
        """
        Update the performance metrics based on the current values of true positive, true negative, false positive, and false negative
        """
        self.logger.info("Updating performance metrics")
        metrics = self.get_performance_metrics('true_positive, true_negative, false_positive, false_negative')
        accuracy = self.safe_divide(metrics['true_positive'] + metrics['true_negative'], metrics['true_positive'] + metrics['true_negative'] + metrics['false_positive'] + metrics['false_negative'])
        precision = self.safe_divide(metrics['true_positive'], metrics['true_positive'] + metrics['false_positive'])
        sensitivity = self.safe_divide(metrics['true_positive'], metrics['true_positive'] + metrics['false_negative'])
        specificity = self.safe_divide(metrics['true_negative'], metrics['true_negative'] + metrics['false_positive'])
        if precision is None or sensitivity is None:
            f1_score = None
        else:
            f1_score = self.safe_divide(2 * precision * sensitivity, precision + sensitivity)

        with self.connection:
            self.connection.execute('''
                UPDATE performance_metrics
                SET accuracy = ?, precision = ?, sensitivity = ?, specificity = ?, f1_score = ?
                WHERE id = ?
            ''', (accuracy, precision, sensitivity, specificity, f1_score, PERFORMANCE_METRICS_ROW_ID))


    def get_performance_metrics(self, columns: str='*'):
        """
        Get the performance metrics from the database

        Args:
            columns (str, optional): The columns to retrieve. Defaults to '*'.

        Returns:
            dict: A dictionary containing the performance metrics
        """
        self.logger.info(f"Retrieving performance metrics")
        allowed_columns = ["true_positive", "true_negative", "false_positive", "false_negative", "accuracy", "precision", "sensitivity", "specificity", "f1_score"]
        if columns == '*':
            validated_columns = columns
        else:
            validated_columns = ", ".join([column for column in columns.split(',') if column.strip() in allowed_columns])
        cursor = self.connection.cursor()
        cursor.row_factory = sqlite3.Row
        cursor.execute(f'''
            SELECT {validated_columns} FROM performance_metrics
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
        self.logger.debug("Resetting performance metrics to zero.")
        with self.connection:
            self.connection.execute('''
                UPDATE performance_metrics
                SET true_positive = 0, true_negative = 0, false_positive = 0, false_negative = 0, accuracy = 0.0, precision = 0.0, sensitivity = 0.0, specificity = 0.0, f1_score = 0.0
                WHERE id = ?
            ''', (PERFORMANCE_METRICS_ROW_ID,))
