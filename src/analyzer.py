import pandas as pd
import logging
from pathlib import Path


class OrderAnalyzer:
    def __init__(self, data_dir, reports_dir, logs_dir,
                 output_filename, log_filename,
                 status_column, status_value, amount_column,
                 required_columns):
        self.data_dir = Path(data_dir)
        self.reports_dir = Path(reports_dir)
        self.logs_dir = Path(logs_dir)
        self.output_filename = output_filename
        self.status_column = status_column
        self.status_value = status_value
        self.amount_column = amount_column
        self.required_columns = list(required_columns)

        self.processed_count = 0
        self.error_count = 0

        self.logger = self._setup_logger(log_filename)

    def _setup_logger(self, log_filename):
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        logger = logging.getLogger("order_analyzer")
        logger.setLevel(logging.ERROR)
        if not logger.handlers:
            handler = logging.FileHandler(self.logs_dir / log_filename, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            logger.addHandler(handler)
        return logger

    def load_file(self, path):
        """Читает CSV и проверяет формат. Ошибки не ловит, а передаёт выше."""
        df = pd.read_csv(path)

        missing = set(self.required_columns) - set(df.columns)
        if missing:
            raise ValueError(f"Нет обязательных колонок: {sorted(missing)}")

        # при нечисловых значениях бросит ValueError
        df[self.amount_column] = pd.to_numeric(df[self.amount_column])

        # строки без суммы не участвуют в расчётах, чтобы метрики были согласованы
        return df.dropna(subset=[self.amount_column])

    def filter_delivered(self, df):
        return df[df[self.status_column] == self.status_value]

    def calculate_metrics(self, df):
        count = len(df)
        return {
            "total_revenue": float(df[self.amount_column].sum()),
            "average_check": float(df[self.amount_column].mean()) if count else 0.0,
            "orders_count": count,
        }

    def process_file(self, path):
        """Возвращает словарь с метриками или None, если файл не обработан."""
        path = Path(path)
        try:
            df = self.load_file(path)
            delivered = self.filter_delivered(df)
            metrics = self.calculate_metrics(delivered)
        except (pd.errors.EmptyDataError, pd.errors.ParserError,
                ValueError, KeyError) as e:
            self.logger.error("%s: %s: %s", path.name, type(e).__name__, e)
            self.error_count += 1
            return None
        except Exception:
            self.logger.exception("%s: непредвиденная ошибка", path.name)
            self.error_count += 1
            return None

        self.processed_count += 1
        return {"file": path.name, **metrics}

    def process_all(self):
        self.processed_count = 0
        self.error_count = 0

        results = []
        for path in sorted(self.data_dir.glob("*.csv")):
            result = self.process_file(path)
            if result is not None:
                results.append(result)

        self._save_report(results)
        return results

    def _save_report(self, results):
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        columns = ["file", "total_revenue", "average_check", "orders_count"]
        df = pd.DataFrame(results, columns=columns)
        df.to_csv(self.reports_dir / self.output_filename, index=False)