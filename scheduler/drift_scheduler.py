import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from feature_store.config import settings
from feature_store.drift.detector import detector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_drift_check():
    """Job executed by APScheduler every N minutes."""
    logger.info(f"Scheduled drift check starting at {datetime.utcnow().isoformat()}")
    try:
        report = detector.run_check(window_minutes=60)

        if report.get("error"):
            logger.warning(f"Drift check skipped: {report['error']}")
            return

        if report.get("note"):
            logger.info(f"Drift check note: {report['note']}")
            return

        logger.info(
            f"Drift check done — "
            f"max_psi={report['max_psi']:.4f}, "
            f"drifted={report['n_features_drifted']}/{report['n_features_checked']}, "
            f"trigger_retraining={report['trigger_retraining']}"
        )

        if report.get("trigger_retraining"):
            logger.warning(
                f"DRIFT THRESHOLD EXCEEDED — "
                f"max_psi={report['max_psi']:.4f} >= {settings.drift.PSI_THRESHOLD}. "
                f"Retraining will be triggered in Phase 7."
            )
            if report.get("drifted_features"):
                logger.warning(
                    f"Drifted features: {report['drifted_features'][:5]}"
                )

    except Exception as e:
        logger.error(f"Drift check failed with error: {e}", exc_info=True)


def start_scheduler():
    interval = settings.drift.CHECK_INTERVAL_MINUTES
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_drift_check,
        trigger=IntervalTrigger(minutes=interval),
        id="drift_check",
        name="Drift Detection Check",
        replace_existing=True,
    )
    logger.info(
        f"Drift scheduler started — "
        f"running every {interval} minutes."
    )
    logger.info("Running initial drift check now...")
    run_drift_check()

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Drift scheduler stopped by user.")
        scheduler.shutdown()


if __name__ == "__main__":
    start_scheduler()