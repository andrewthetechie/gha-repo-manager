import os
from typing import List
from typing import Optional
from typing import Union

from pydantic import BaseModel  # pylint: disable=E0611
from pydantic import Field
from pydantic import HttpUrl  # pylint: disable=E0611
from pydantic import validator

OptBool = Optional[bool]
OptStr = Optional[str]


class SecretEnvError(Exception):
    ...


class Secret(BaseModel):
    key: OptStr = Field(None, description="Secret's name.")
    env: OptStr = Field(None, description="Environment variable to pull the secret from")
    value: OptStr = Field(None, description="Value to set this secret to")
    required: OptBool = Field(
        True,
        description="Setting a value as not required allows you to not pass in an env var without causing an error",
    )
    exists: OptBool = Field(True, description="Set to false to delete a secret")

    @validator("value", always=True)
    def validate_value(cls, v, values) -> OptStr:
        if v is None:
            return None

        if values["env"] is not None:
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
