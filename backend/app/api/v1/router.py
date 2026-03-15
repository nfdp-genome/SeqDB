from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.projects import router as projects_router
from app.api.v1.samples import router as samples_router
from app.api.v1.experiments import router as experiments_router
from app.api.v1.runs import router as runs_router
from app.api.v1.upload import router as upload_router
from app.api.v1.submissions import router as submissions_router
from app.api.v1.search import router as search_router
from app.api.v1.checklists import router as checklists_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.templates import router as templates_router
from app.api.v1.staging import router as staging_router
from app.api.v1.bulk_submit import router as bulk_submit_router
from app.api.v1.filereport import router as filereport_router
from app.api.v1.ontologies import router as ontologies_router
from app.api.v1.archive_submissions import router as archive_submissions_router
from app.api.v1.ncbi import router as ncbi_router
from app.api.v1.eutils import router as eutils_router
from app.api.v1.samplesheet import router as samplesheet_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(samples_router)
api_router.include_router(experiments_router)
api_router.include_router(runs_router)
api_router.include_router(upload_router)
api_router.include_router(submissions_router)
api_router.include_router(search_router)
api_router.include_router(checklists_router)
api_router.include_router(integrations_router)
api_router.include_router(templates_router)
api_router.include_router(staging_router)
api_router.include_router(bulk_submit_router)
api_router.include_router(filereport_router)
api_router.include_router(ontologies_router)
api_router.include_router(archive_submissions_router)
api_router.include_router(ncbi_router)
api_router.include_router(eutils_router)
api_router.include_router(samplesheet_router)


@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}
