from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://nfdp:nfdp@localhost:5432/nfdp"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    app_env: str = "development"
    app_debug: bool = True
    ncbi_submission_url: str = "https://submit.ncbi.nlm.nih.gov/api/2.0/submissions/"
    ncbi_api_key: str = ""
    ncbi_submitter_email: str = ""
    ncbi_center_name: str = "NFDP"

    # Root admin (seeded on startup)
    root_admin_email: str = "genome@nfdp.gov.sa"
    root_admin_password: str = "nfdproot"

    # OIDC / Keycloak
    oidc_enabled: bool = False
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_discovery_url: str = ""  # e.g. https://keycloak.nfdp.dev/realms/nfdp/.well-known/openid-configuration
    oidc_redirect_uri: str = "http://localhost:3000/auth/callback"

    model_config = {"env_file": ".env"}


settings = Settings()
