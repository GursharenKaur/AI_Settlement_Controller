import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import TextIOWrapper
from typing import Iterator

from app.schemas.ingestion import IngestionError
from app.schemas.settlement import SettlementCreate
from pydantic import ValidationError

REQUIRED_COLUMNS = {
    "settlement_id",
    "payment_id",
    "settled_amount",
    "currency",
    "status",
    "settled_at",
}


def parse_settlement_csv(
    file,
) -> Iterator[tuple[SettlementCreate | None, IngestionError | None]]:
    text_file = TextIOWrapper(file, encoding="utf-8", newline="")
    reader = csv.DictReader(text_file)

    if reader.fieldnames is None:
        yield None, IngestionError(
            row=1,
            field="header",
            message="CSV file is missing a header row.",
        )
        return

    missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames)

    if missing_columns:
        yield None, IngestionError(
            row=1,
            field="header",
            message=(
                "Missing required columns: "
                + ", ".join(sorted(missing_columns))
            ),
        )
        return

    for row_number, row in enumerate(reader, start=2):
        try:
            settlement = SettlementCreate(
                settlement_id=row.get("settlement_id", ""),
                payment_id=row.get("payment_id", ""),
                settled_amount=Decimal(
                    row.get("settled_amount", "")
                ),
                currency=row.get("currency", ""),
                status=row.get("status", ""),
                settled_at=datetime.fromisoformat(
                    row.get("settled_at", "").replace("Z", "+00:00")
                ),
            )

            yield settlement, None

        except ValidationError as exc:
            error = exc.errors()[0]

            yield None, IngestionError(
                row=row_number,
                field=str(error["loc"][0]),
                message=str(error["msg"]),
            )

        except (ValueError, InvalidOperation) as exc:
            yield None, IngestionError(
                row=row_number,
                field="row",
                message=str(exc),
            )