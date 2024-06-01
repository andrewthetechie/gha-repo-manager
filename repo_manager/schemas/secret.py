import os
from typing import Optional

from pydantic import (
    BaseModel,  # pylint: disable=E0611
    Field,
    ValidationInfo,
    field_validator,
)

OptBool = Optional[bool]
OptStr = Optional[str]


class SecretEnvError(Exception): ...


class Secret(BaseModel):
    type: str = Field(
        "actions",
        description="Type of secret, can be `dependabot` or `actions` or an `environment` path",
    )
    key: str = Field(None, description="Secret's name.")
    env: OptStr = Field(None, description="Environment variable to pull the secret from")
    value: OptStr = Field(None, description="Value to set this secret to", validate_default=True)
    required: OptBool = Field(
        True,
        description="Setting a value as not required allows you to not pass in an env var without causing an error",
    )
    exists: OptBool = Field(True, description="Set to false to delete a secret")

    @field_validator("value")
    def validate_value(cls, v, info: ValidationInfo) -> OptStr:
        if v is None:
            return None

        if info.data["env"] is not None:
            raise ValueError("Cannot set an env and a value in the same secret, remove one.")

        return v

    @property
    def expected_value(self):
        if self.value is None:
            env_var = os.environ.get(self.env)
            if env_var is None:
                raise SecretEnvError(f"{self.env} is not set")
            return env_var
        return self.value
