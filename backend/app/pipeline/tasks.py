from app.pipeline.celery_app import celery_app
import time

@celery_app.task(bind=True)
def run_pipeline(self, video_id: str, visual_engine: str):
    # placeholder for pipeline task
    self.update_state(state='PROGRESS', meta={'stage': 'starting', 'percent': 0})
    time.sleep(1)
    self.update_state(state='PROGRESS', meta={'stage': 'audio', 'percent': 30})
    time.sleep(1)
    self.update_state(state='PROGRESS', meta={'stage': 'visuals', 'percent': 70})
    time.sleep(1)
    return {'stage': 'completed', 'percent': 100}
