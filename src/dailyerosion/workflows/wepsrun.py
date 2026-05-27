"""Elements of WEPS Run."""

from datetime import date
from typing import Annotated

from pydantic import BaseModel, Field


class WEPSJobPayload(BaseModel):
    """Payload for a WEPS2Sweep job."""

    wepsexe: Annotated[str, Field(description="Name of wepsexe to use")]
    huc_12: Annotated[str, Field(description="HUC12 code")]
    clifile: Annotated[str, Field(description="DEP breakpoint CLI file")]
    scenario: Annotated[int, Field(description="Scenario ID")] = 0
    field_id: Annotated[int, Field(description="Database Field Identifier")]
    fpath: Annotated[int, Field(description="Flowpath identifier in HUC12")]
    dt: Annotated[date, Field(description="Date to Run for")]
    lon: Annotated[float, Field(description="Longitude of Point")]
    lat: Annotated[float, Field(description="Latitude of Point")]
