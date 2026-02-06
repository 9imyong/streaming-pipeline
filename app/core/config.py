"""
공통 설정. Pydantic Settings + .env 로딩.
- dev/prod: ENVIRONMENT 로 구분, 기본값 dev.
- 비즈니스 로직 없음. Kafka/DB/ffmpeg 설정값만 보관.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


EnvKind = Literal["dev", "prod"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        env_ignore_empty=True,
    )

    # 환경 구분 (dev: 로그 상세, prod: JSON/간소화)
    environment: EnvKind = Field(default="dev", description="dev | prod")
    log_level: str = Field(default="INFO", description="로그 레벨")
    tz: str = Field(default="Asia/Seoul", description="타임존")

    # DB (연결 문자열/호스트만 보관, 쿼리/비즈니스 로직은 infrastructure)
    db_host: str = Field(default="localhost", alias="HOST")
    db_port: int = Field(default=3306, alias="PORT")
    db_user: str = Field(default="", alias="USERNAME")
    db_password: str = Field(default="", alias="PASSWORD")
    db_name: str = Field(default="streaming_pipeline_dev", alias="DBNAME")

    # Redis
    redis_host: str = Field(default="redis", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")

    # Kafka (연결 정보만, 발행/소비 로직은 infrastructure)
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        alias="KAFKA_BOOTSTRAP_SERVERS",
    )

    # 앱 노출용 (헬스/메트릭 등)
    host_ip: str = Field(default="localhost", alias="HOST_IP")

    @property
    def is_dev(self) -> bool:
        return self.environment == "dev"

    @property
    def is_prod(self) -> bool:
        return self.environment == "prod"


@lru_cache
def get_settings() -> Settings:
    """캐시된 Settings. 환경 변수 변경 시 프로세스 재시작 필요."""
    return Settings()
