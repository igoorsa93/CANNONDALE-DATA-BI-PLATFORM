"""Sales ETL (placeholder documental): lógica de sazonalidade/categoria.

A geração pesada roda via SQL (database/seeds/08_generate_vendas.sql).
Este módulo documenta a regra e pode exportar parâmetros de simulação.
"""
from dataclasses import dataclass


@dataclass
class SalesSimConfig:
    start_date: str = "2024-01-01"
    end_date: str = "2026-10-05"
    peak_months: tuple = (11, 12, 1, 2)     # verão BR = alta
    low_months: tuple = (6, 7)               # inverno = baixa
    channels: tuple = ("Loja Física", "Online", "Revenda")
    payments: tuple = ("Cartão de Crédito", "PIX", "Financiamento", "Boleto")


def seasonality_weight(month: int) -> int:
    if month in (11, 12, 1, 2):
        return 3
    if month in (3, 4, 9, 10):
        return 2
    return 1


if __name__ == "__main__":
    cfg = SalesSimConfig()
    print("Config Simulação Vendas:", cfg)
    print("Pesos por mês:", {m: seasonality_weight(m) for m in range(1, 13)})
