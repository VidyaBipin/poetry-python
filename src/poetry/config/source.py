from __future__ import annotations

import dataclasses
import warnings

from typing import TYPE_CHECKING

from poetry.repositories.repository_pool import Priority


if TYPE_CHECKING:
    from tomlkit.items import Table


@dataclasses.dataclass(order=True, eq=True)
class Source:
    name: str
    url: str = ""
    default: dataclasses.InitVar[bool] = False
    secondary: dataclasses.InitVar[bool] = False
    priority: Priority = (
        Priority.PRIMARY
    )  # cheating in annotation: str will be converted to Priority in __post_init__

    def __post_init__(self, default: bool, secondary: bool) -> None:
        if isinstance(self.priority, str):
            self.priority = Priority[self.priority.upper()]
        if default or secondary:
            warnings.warn(
                "Parameters 'default' and 'secondary' to"
                " 'Source' are deprecated. Please provide"
                " 'priority' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        if default:
            self.priority = Priority.DEFAULT
        elif secondary:
            self.priority = Priority.SECONDARY

    def to_dict(self) -> dict[str, str | bool]:
        return dataclasses.asdict(
            self,
            dict_factory=lambda x: {
                k: v if not isinstance(v, Priority) else v.name.lower()
                for (k, v) in x
                if v
            },
        )

    def to_toml_table(self) -> Table:
        from tomlkit import nl
        from tomlkit import table

        source_table: Table = table()
        for key, value in self.to_dict().items():
            source_table.add(key, value)
        source_table.add(nl())
        return source_table
