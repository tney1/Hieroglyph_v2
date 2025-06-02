from sqlalchemy.orm import Session
from .sqlite_models import SQLBatchJobs
import json
import logging
logger = logging.getLogger(__name__)


def create_batch_job(db: Session, name, dst_lang, image_type,
                     running, failure, success, completed,
                     internal_id, output_location):
    """
    Creates a new batch job in the database
    """
    # Create Job Instance
    new_job = SQLBatchJobs(
        name=name, dst_lang=dst_lang, image_type=image_type, running=running,
        failure=failure, success=success, completed=completed,
        internal_id=internal_id, output_location=output_location)

    # Add to DB, Commit Change, and Refresh Instance
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job


def get_batch_job_by_id(db: Session, id: int):
    """
    Retrieves a specific batch job record by ID
    """
    job_record = db.query(SQLBatchJobs).filter(SQLBatchJobs.id == id).first()
    return job_record


def get_batch_job_by_internal_id_non_serialized(db: Session, internal_id: str):
    """
    Retrieves a specific batch job record by the UUID without serializing
    """
    job_record = db.query(SQLBatchJobs).filter(SQLBatchJobs.internal_id == internal_id).first()

    return job_record


def get_batch_job_by_internal_id(db: Session, internal_id: str) -> dict:
    """
    Retrieves a specific batch job record by the UUID
    """
    job_record = db.query(SQLBatchJobs).filter(SQLBatchJobs.internal_id == internal_id).with_entities(
        SQLBatchJobs.internal_id, SQLBatchJobs.success,
        SQLBatchJobs.failure, SQLBatchJobs.completed, SQLBatchJobs.timestamp, SQLBatchJobs.output_location).first()

    return _serialize_running_jobs(tuple(job_record))


def get_all_running_jobs(db: Session) -> list:
    """
    Retrieves all batch job records that are marked as running and have not failed
    """
    job_record = db.query(SQLBatchJobs).with_entities(
        SQLBatchJobs.internal_id, SQLBatchJobs.success,
        SQLBatchJobs.failure, SQLBatchJobs.completed, SQLBatchJobs.timestamp, SQLBatchJobs.output_location).all()

    job_record = [_serialize_running_jobs(tuple(row)) for record in job_record]

    return json.dumps(job_record)


def _serialize_running_jobs(record: tuple) -> dict:
    return {
        "internal_id": record[0],
        "success": record[1],
        "failure": record[2],
        "completed": record[3],
        "timestamp": str(record[4]),
        "output_location": record[5]
    }


def delete_job(db: Session, id: int):
    """
    Deletes a specific job record by ID
    """
    try:
        job_record = get_batch_job_by_id(db=db, id=id)
        db.delete(job_record)
        db.commit()
        return True
    except:
        return False


def get_all_batch_jobs(db: Session):
    """
    Returns all existing job records in the table
    """
    all_jobs = db.query(SQLBatchJobs).all()
    return all_jobs


def update_job(db: Session, id: int, name, dst_lang, image_type,
               running, failure, success, completed):
    """
    Updates all the attributes of a specific job record by ID
    """

    job_record = get_batch_job_by_id(db=db, id=id)
    job_record.name = name
    job_record.dst_lang = dst_lang
    job_record.image_type = image_type
    job_record.running = running
    job_record.failure = failure
    job_record.success = success
    job_record.completed = completed

    # Add to DB, Commit Change, and Refresh Instance
    db.commit()
    db.refresh(job_record)
    return job_record


def update_job_status_flags(db: Session, internal_id, running, failure, success, completed):
    """
    Updates the running, failure, and completed attributes of a specific job record by UUID
    """

    job_record = get_batch_job_by_internal_id_non_serialized(db=db, internal_id=internal_id)
    job_record.running = running
    job_record.failure = failure
    job_record.success = success
    job_record.completed = completed

    # Add to DB, Commit Change, and Refresh Instance
    db.commit()
    db.refresh(job_record)
    return job_record
