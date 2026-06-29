import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from feature_store.config import settings
from feature_store.drift.detector import detector
from feature_store.retraining.trigger import trigger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_drift_check():
    """
    Scheduled job:
    1. Run drift check
    2. If drift threshold exceeded — trigger retraining
    3. Log everything
    """
    logger.info(
        f"Scheduled drift check starting at {datetime.utcnow().isoformat()}"
    )

    try:
        # Step 1 — run drift check
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

        # Step 2 — trigger retraining if needed
        if report.get("trigger_retraining"):
            logger.warning(
                f"DRIFT DETECTED — "
                f"max_psi={report['max_psi']:.4f}. "
                f"Starting retraining pipeline..."
            )
            result = trigger.run(report)

            if result["status"] == "success":
                logger.info(
                    f"Retraining SUCCESS — "
                    f"version={result['version']}, "
                    f"accuracy={result['accuracy_after']:.4f} "
                    f"(delta={result['accuracy_delta']:+.4f})"
                )
            elif result["status"] == "skipped":
                logger.info(f"Retraining skipped: {result['reason']}")
            elif result["status"] == "rejected":
                logger.warning(f"Retraining rejected: {result['reason']}")
            else:
                logger.error(f"Retraining failed: {result.get('error')}")

    except Exception as e:
        logger.error(f"Scheduled job failed: {e}", exc_info=True)


def start_scheduler():
    interval = settings.drift.CHECK_INTERVAL_MINUTES
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_drift_check,
        trigger=IntervalTrigger(minutes=interval),
        id="drift_check",
        name="Drift Detection + Auto Retraining",
        replace_existing=True,
    )
    logger.info(
        f"Scheduler started — "
        f"drift check + retraining every {interval} minutes."
    )
    logger.info("Running initial check now...")
    run_drift_check()

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped.")
        scheduler.shutdown()


if __name__ == "__main__":
    start_scheduler()