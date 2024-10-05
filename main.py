from src.database import Database
from src.restock_playstation import playstation_run
from src.logger_setup import setup_logger, delete_previous_logs_on_start



logger = setup_logger("RESTOCK_INFO", "bot")


restock_monitors = [playstation_run]


def main():
    try:
        db = Database()
    except Exception as error:
        logger.error(error)

    try:
        for monitor in restock_monitors:
            monitor(db)

    except Exception as error:
        logger.error(error)
    

if __name__ == "__main__":
    delete_previous_logs_on_start("bot")
    main()