"""Workflow helpers for running WEPP.

This module provides data models and utilities for WEPP job management,
particularly for job queuing and execution workflows.

Integration Example
-------------------
To use WeppJobPayload in your scripts::

    from dailyerosion.workflows.wepprun import WeppJobPayload
    import json
    import pika

    # Create the payload
    payload = WeppJobPayload(
        wepprun=runfile_content,
        weppexe="wepp20240930"
    )

    # Send to RabbitMQ (replaces manual dict creation)
    channel.basic_publish(
        exchange="",
        routing_key="dep",
        body=payload.model_dump_json(),  # Validated JSON
        properties=pika.BasicProperties(delivery_mode=2)
    )

    # On the worker side, validate incoming messages
    payload = WeppJobPayload.model_validate_json(body)
    # Now you have validated data with proper types

"""

from io import StringIO

from pydantic import BaseModel, Field


class WeppJobPayload(BaseModel):
    """Pydantic model for WEPP job payload submitted to RabbitMQ.

    This model describes the JSON structure that gets queued for WEPP
    execution workers to process.

    Attributes
    ----------
    errorfn: str
        The filename to write error logs to if the WEPP run fails. This
        prevents downstream guessing as to what it should be.
    weppexe : str
        The WEPP executable name/version to use (e.g., 'wepp20240930').
        This allows the worker to select the appropriate WEPP binary.
    wepprun : str
        The complete WEPP runfile content as a string. This multi-line
        string contains all the parameters and file paths WEPP needs to
        execute a simulation.
    """

    errorfn: str = Field(
        ...,
        description="Filename to write error logs if WEPP run fails",
        min_length=1,
    )
    wepprun: str = Field(
        ...,
        description="Complete WEPP runfile content",
        min_length=1,
    )
    weppexe: str = Field(
        ...,
        description="WEPP executable name/version",
        min_length=1,
        examples=["wepp20240930"],
    )


class WeppRunConfig(BaseModel):
    """Description on how we are to run weep."""

    units: str = Field(default="E", title="Units for WEPP run")
    is_hillslope: bool = Field(
        default=True, title="Whether to run hillslope model"
    )
    is_continuous: bool = Field(
        default=True, title="Whether to run continuous simulation"
    )
    hillslope_version: int = Field(default=1, title="Hillslope model version")
    enable_pass_file: bool = Field(
        default=False, title="Enable Passfile output"
    )
    abbreviated_annual_output: int = Field(default=1, title="Annual Output")
    enable_initialcond_file: bool = Field(
        default=False, title="Enable Initial Conditions file"
    )
    soilloss_output_filepath: str = Field(
        default="/dev/null", title="Soil Loss Filepath."
    )
    enable_waterbalance_file: bool = Field(
        default=True, title="Enable Water Balance file"
    )
    enable_crop_file: bool = Field(
        default=False, title="Enable Crop output file"
    )
    enable_soil_file: bool = Field(
        default=False, title="Enable Soil output file"
    )
    enable_sed_file: bool = Field(
        default=False, title="Enable Distance and Sediment output file"
    )
    enable_graph_file: bool = Field(
        default=False, title="Enable Graphics output file"
    )
    enable_env_file: bool = Field(
        default=True, title="Enable Event output file"
    )
    enable_ofe_file: bool = Field(
        default=False, title="Enable OFE output file"
    )
    enable_summary_file: bool = Field(
        default=False, title="Enable Final Summary output file"
    )
    enable_winter_file: bool = Field(
        default=False, title="Enable Daily Winter output file"
    )
    enable_yield_file: bool = Field(
        default=True, title="Enable Plant Yield output file"
    )
    irrigation: int = Field(default=0, title="Irrigation Control")
    years: int = Field(..., title="Number of Years to Simulate")
    route_all_events: int = Field(default=0)


def build_runfile(
    config: WeppRunConfig,
    input_path_template: str,
    output_path_template: str,
    climate_filepath: str,
    irrigation_filewpath: str,
) -> str:
    """Generate the run file based on the given config."""

    def _output_logic(enabled: bool, prefix: str) -> str:
        """Boilerplate for enabled and filenames."""
        if not enabled:
            return "N"
        return "Y\n" + output_path_template.format(prefix=prefix)

    def _input_logic(prefix: str) -> str:
        """Boilerplate for enabled and filenames."""
        return input_path_template.format(prefix=prefix)

    sio = StringIO()
    sio.write(f"{config.units}\n")
    sio.write(f"{'Y' if config.is_hillslope else 'N'}\n")
    sio.write(f"{'1' if config.is_continuous else '2'}\n")
    sio.write(f"{config.hillslope_version}\n")
    sio.write(f"{_output_logic(config.enable_pass_file, 'pass')}\n")
    sio.write(f"{config.abbreviated_annual_output}\n")
    sio.write(f"{_output_logic(config.enable_initialcond_file, 'initcond')}\n")
    sio.write(f"{config.soilloss_output_filepath}\n")
    sio.write(f"{_output_logic(config.enable_waterbalance_file, 'wb')}\n")
    sio.write(f"{_output_logic(config.enable_crop_file, 'crop')}\n")
    sio.write(f"{_output_logic(config.enable_soil_file, 'soil')}\n")
    sio.write(f"{_output_logic(config.enable_sed_file, 'sed')}\n")
    sio.write(f"{_output_logic(config.enable_graph_file, 'grph')}\n")
    sio.write(f"{_output_logic(config.enable_env_file, 'env')}\n")
    sio.write(f"{_output_logic(config.enable_ofe_file, 'ofe')}\n")
    sio.write(f"{_output_logic(config.enable_summary_file, 'summary')}\n")
    sio.write(f"{_output_logic(config.enable_winter_file, 'wntr')}\n")
    sio.write(f"{_output_logic(config.enable_yield_file, 'yld')}\n")
    sio.write(f"{_input_logic('man')}\n")
    sio.write(f"{_input_logic('slp')}\n")
    sio.write(f"{climate_filepath}\n")
    sio.write(f"{_input_logic('sol')}\n")
    sio.write(f"{config.irrigation}\n")
    if config.irrigation == 2:
        sio.write(f"{irrigation_filewpath}\n")
    sio.write(f"{config.years}\n")
    sio.write(f"{config.route_all_events}\n")

    return sio.getvalue()
