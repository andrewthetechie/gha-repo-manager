from typing import Optional

from pydantic import BaseModel  # pylint: disable=E0611
from pydantic import Field
from pydantic.color import Color

OptBool = Optional[bool]
OptStr = Optional[str]


class Label(BaseModel):
    name: OptStr = Field(None, description="Label's name.")
    color: Color | None = Field(None, description="Color of this label")
    description: OptStr = Field(None, description="Description of the label")
    new_name: OptStr = Field(None, description="If set, rename a label from name to new_name.")
    exists: OptBool = Field(True, description="Set to false to delete a label")

    @property
    def expected_name(self) -> str:
        """What the expected label name of this label is. If new_name is set, it will be new_name. Otherwise, name"""
        return self.new_name if self.new_name is not None else self.name

    @property
    def color_no_hash(self) -> str:
        """Returns the color without the leader # if it exists"""
        return self.color if self.color is None else str(self.color.as_hex()).replace("#", "")
