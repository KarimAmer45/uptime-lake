"""Validated table naming and pipeline configuration."""

from __future__ import annotations

import re
from dataclasses import dataclass

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def validate_identifier(value: str, label: str) -> str:
    """Allow only simple Unity Catalog identifiers before interpolating SQL."""
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"Invalid {label} {value!r}; use letters, numbers, and underscores only")
    return value


@dataclass(frozen=True)
class PipelineConfig:
    catalog: str
    bronze_schema: str = "bronze"
    silver_schema: str = "silver"
    gold_schema: str = "gold"
    audit_schema: str = "audit"
    equipment_id: str = "metro_apu_01"

    def __post_init__(self) -> None:
        for label in ("catalog", "bronze_schema", "silver_schema", "gold_schema", "audit_schema"):
            validate_identifier(getattr(self, label), label)

    def table(self, layer: str, name: str) -> str:
        schemas = {
            "bronze": self.bronze_schema,
            "silver": self.silver_schema,
            "gold": self.gold_schema,
            "audit": self.audit_schema,
        }
        if layer not in schemas:
            raise ValueError(f"Unknown layer: {layer}")
        validate_identifier(name, "table")
        return f"`{self.catalog}`.`{schemas[layer]}`.`{name}`"

