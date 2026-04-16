from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class GenerationConfig:
    org_slug: str = "demo"
    org_name: str | None = None
    seed: int = 42
    n_transactions: int = 25_000
    n_contracts: int = 80
    n_prs: int = 500
    n_pos: int = 400
    n_grs: int = 350
    n_invoices: int = 300
    n_violations: int = 150
    start_date: date = field(default_factory=lambda: date(2022, 1, 1))
    end_date: date = field(default_factory=date.today)

    def to_dict(self) -> dict:
        return {
            "org_slug": self.org_slug,
            "org_name": self.org_name,
            "seed": self.seed,
            "n_transactions": self.n_transactions,
            "n_contracts": self.n_contracts,
            "n_prs": self.n_prs,
            "n_pos": self.n_pos,
            "n_grs": self.n_grs,
            "n_invoices": self.n_invoices,
            "n_violations": self.n_violations,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GenerationConfig":
        return cls(
            org_slug=data.get("org_slug", "demo"),
            org_name=data.get("org_name"),
            seed=int(data.get("seed", 42)),
            n_transactions=int(data.get("n_transactions", 25_000)),
            n_contracts=int(data.get("n_contracts", 80)),
            n_prs=int(data.get("n_prs", 500)),
            n_pos=int(data.get("n_pos", 400)),
            n_grs=int(data.get("n_grs", 350)),
            n_invoices=int(data.get("n_invoices", 300)),
            n_violations=int(data.get("n_violations", 150)),
            start_date=date.fromisoformat(data.get("start_date", "2022-01-01")),
            end_date=date.fromisoformat(data.get("end_date", date.today().isoformat())),
        )


def supplier_id(idx: int) -> str:
    return f"SUP-{idx:05d}"


def category_id(idx: int) -> str:
    return f"CAT-{idx:03d}"


def transaction_id(idx: int) -> str:
    return f"TXN-{idx:08d}"


def violation_id(idx: int) -> str:
    return f"VIO-{idx:06d}"


def contract_id(org: str, year: int, idx: int) -> str:
    return f"CT-{org.upper()}-{year}-{idx:04d}"


def pr_id(org: str, year: int, idx: int) -> str:
    return f"PR-{org.upper()}-{year}-{idx:05d}"


def po_id(org: str, year: int, idx: int) -> str:
    return f"PO-{org.upper()}-{year}-{idx:05d}"


def gr_id(org: str, year: int, idx: int) -> str:
    return f"GR-{org.upper()}-{year}-{idx:05d}"


def invoice_id(org: str, year: int, idx: int) -> str:
    return f"INV-{org.upper()}-{year}-{idx:06d}"


def policy_id(idx: int) -> str:
    return f"POL-{idx:03d}"
