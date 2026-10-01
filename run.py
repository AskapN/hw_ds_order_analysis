import config
from src.analyzer import OrderAnalyzer


def main():
    analyzer = OrderAnalyzer(
        data_dir=config.DATA_DIR,
        reports_dir=config.REPORTS_DIR,
        logs_dir=config.LOGS_DIR,
        output_filename=config.OUTPUT_FILENAME,
        log_filename=config.LOG_FILENAME,
        status_column=config.STATUS_COLUMN,
        status_value=config.STATUS_VALUE,
        amount_column=config.AMOUNT_COLUMN,
        required_columns=config.REQUIRED_COLUMNS,
    )
    analyzer.process_all()
    print(f"Обработано файлов: {analyzer.processed_count}")
    print(f"Файлов с ошибками: {analyzer.error_count}")


if __name__ == "__main__":
    main()