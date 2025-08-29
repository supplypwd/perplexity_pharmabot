from typing import Any, Dict
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PPLX_API_KEY: str
    PPLX_ENDPOINT: str = "https://api.perplexity.ai/chat/completions"
    PPLX_MODEL: str = "sonar-pro"
    TIMEOUT: int = 60

    RESPONSE_FORMAT: Dict[str, Any] = {
        "type": "json_schema",
        "json_schema": {
            "name": "pharmabot_answer",
            "strict": True,  # force le modèle à respecter le schéma
            "schema": {
                # Optionnel mais recommandé :
                # "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "answer": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "paragraph": {"type": "string"},
                                "source_indices": {
                                    "type": "array",
                                    "items": {"type": "integer"},
                                    "minItems": 1,
                                    "maxItems": 3
                                }
                            },
                            "required": ["paragraph", "source_indices"]
                        }
                    }
                },
                "required": ["answer"]
            }
        }
    }

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
