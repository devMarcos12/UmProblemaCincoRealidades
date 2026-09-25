"""Spike do ADR 05: operação offline e sincronização assíncrona idempotente.

O programa simula uma UPA que continua registrando triagens sem internet. Quando a
rede volta, o primeiro envio chega à nuvem, mas a confirmação se perde. Isso força
uma reentrega do mesmo evento. A nuvem usa o UUID como chave de idempotência e
impede que a triagem seja gravada duas vezes.

Compatível com Python 3.12 e somente com biblioteca padrão.
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from enum import Enum


NAMESPACE_SPIKE = uuid.UUID("3f6d9ec7-4d4a-4d52-bf22-df4a9fd35e17")


class RedeIndisponivel(RuntimeError):
    """Indica que a UPA não consegue alcançar a nuvem."""


class ConfirmacaoPerdida(RuntimeError):
    """Indica que a nuvem recebeu o registro, mas o ACK não voltou à UPA."""


class ResultadoNuvem(str, Enum):
    ACEITO = "ACEITO"
    DUPLICATA_IGNORADA = "DUPLICATA_IGNORADA"


@dataclass(frozen=True)
class Triagem:
    evento_id: str
    paciente: str
    risco: str
    instante_local: str


class BancoLocal:
    """Banco embarcado que representa o componente Edge da UPA."""

    def __init__(self) -> None:
        self._conexao = sqlite3.connect(":memory:")
        self._conexao.row_factory = sqlite3.Row
        self._conexao.execute(
            """
            CREATE TABLE triagens (
                evento_id TEXT PRIMARY KEY,
                paciente TEXT NOT NULL,
                risco TEXT NOT NULL,
                instante_local TEXT NOT NULL,
                sincronizado INTEGER NOT NULL DEFAULT 0
            )
            """
        )

    def registrar(self, triagem: Triagem) -> None:
        self._conexao.execute(
            """
            INSERT INTO triagens(evento_id, paciente, risco, instante_local)
            VALUES (?, ?, ?, ?)
            """,
            (
                triagem.evento_id,
                triagem.paciente,
                triagem.risco,
                triagem.instante_local,
            ),
        )
        self._conexao.commit()

    def pendentes(self) -> list[Triagem]:
        linhas = self._conexao.execute(
            """
            SELECT evento_id, paciente, risco, instante_local
            FROM triagens
            WHERE sincronizado = 0
            ORDER BY instante_local, evento_id
            """
        ).fetchall()
        return [Triagem(**dict(linha)) for linha in linhas]

    def marcar_sincronizada(self, evento_id: str) -> None:
        self._conexao.execute(
            "UPDATE triagens SET sincronizado = 1 WHERE evento_id = ?",
            (evento_id,),
        )
        self._conexao.commit()

    def total(self) -> int:
        return int(self._conexao.execute("SELECT COUNT(*) FROM triagens").fetchone()[0])


class NuvemSimulada:
    """Destino remoto mínimo: rejeita reentregas pelo evento_id."""

    def __init__(self) -> None:
        self._triagens: dict[str, Triagem] = {}
        self.tentativas = 0
        self.duplicatas_bloqueadas = 0

    def receber(self, triagem: Triagem) -> ResultadoNuvem:
        self.tentativas += 1
        if triagem.evento_id in self._triagens:
            self.duplicatas_bloqueadas += 1
            return ResultadoNuvem.DUPLICATA_IGNORADA

        self._triagens[triagem.evento_id] = triagem
        return ResultadoNuvem.ACEITO

    def total_unico(self) -> int:
        return len(self._triagens)


class RedeSimulada:
    """Simula queda de rede e uma perda de confirmação após o primeiro aceite."""

    def __init__(self, nuvem: NuvemSimulada) -> None:
        self.online = False
        self._nuvem = nuvem
        self._perder_proximo_ack = True

    def enviar(self, triagem: Triagem) -> ResultadoNuvem:
        if not self.online:
            raise RedeIndisponivel("sem conexão")

        resultado = self._nuvem.receber(triagem)
        if resultado == ResultadoNuvem.ACEITO and self._perder_proximo_ack:
            self._perder_proximo_ack = False
            raise ConfirmacaoPerdida("registro aceito; confirmação perdida")
        return resultado


class Sincronizador:
    """Worker local que entrega ao menos uma vez e só confirma após receber ACK."""

    def __init__(self, banco: BancoLocal, rede: RedeSimulada) -> None:
        self._banco = banco
        self._rede = rede

    def sincronizar(self) -> list[str]:
        mensagens: list[str] = []
        for triagem in self._banco.pendentes():
            try:
                resultado = self._rede.enviar(triagem)
            except RedeIndisponivel:
                mensagens.append(f"{triagem.paciente}: aguardando rede")
                break
            except ConfirmacaoPerdida:
                mensagens.append(f"{triagem.paciente}: ACK perdido; continuará pendente")
                continue

            self._banco.marcar_sincronizada(triagem.evento_id)
            mensagens.append(f"{triagem.paciente}: {resultado.value}")
        return mensagens


def criar_triagem(chave: str, paciente: str, risco: str, instante: str) -> Triagem:
    """Gera UUID determinístico apenas para tornar a saída do spike reproduzível."""
    evento_id = str(uuid.uuid5(NAMESPACE_SPIKE, chave))
    return Triagem(evento_id, paciente, risco, instante)


def main() -> None:
    banco = BancoLocal()
    nuvem = NuvemSimulada()
    rede = RedeSimulada(nuvem)
    sincronizador = Sincronizador(banco, rede)

    triagens = [
        criar_triagem("upa-17/001", "PAC-001", "VERMELHO", "2026-09-25T10:00:00"),
        criar_triagem("upa-17/002", "PAC-002", "AMARELO", "2026-09-25T10:02:00"),
    ]

    print("=== SPIKE ADR 05: UPA OFFLINE + SINCRONIZACAO IDEMPOTENTE ===")
    print("\n1) Internet indisponivel: a triagem continua localmente")
    for triagem in triagens:
        banco.registrar(triagem)
        print(f"   salvo {triagem.paciente} | risco={triagem.risco} | id={triagem.evento_id}")
    print(f"   pendentes locais: {len(banco.pendentes())}")

    print("\n2) Tentativa ainda offline")
    for mensagem in sincronizador.sincronizar():
        print(f"   {mensagem}")
    print(f"   pendentes locais: {len(banco.pendentes())}")
    print(f"   registros unicos na nuvem: {nuvem.total_unico()}")

    print("\n3) Internet volta, mas o ACK do primeiro envio se perde")
    rede.online = True
    for mensagem in sincronizador.sincronizar():
        print(f"   {mensagem}")
    print(f"   pendentes locais: {len(banco.pendentes())}")
    print(f"   registros unicos na nuvem: {nuvem.total_unico()}")

    print("\n4) Worker tenta novamente")
    for mensagem in sincronizador.sincronizar():
        print(f"   {mensagem}")
    print(f"   pendentes locais: {len(banco.pendentes())}")
    print(f"   registros unicos na nuvem: {nuvem.total_unico()}")

    print("\n5) Resultado")
    print(f"   triagens criadas localmente: {banco.total()}")
    print(f"   tentativas de entrega: {nuvem.tentativas}")
    print(f"   duplicatas bloqueadas: {nuvem.duplicatas_bloqueadas}")
    print(f"   triagens unicas na nuvem: {nuvem.total_unico()}")

    sucesso = (
        banco.total() == 2
        and len(banco.pendentes()) == 0
        and nuvem.total_unico() == 2
        and nuvem.duplicatas_bloqueadas == 1
    )
    print(f"\nPROVA: {'SUCESSO' if sucesso else 'FALHA'}")
    print("O UUID permitiu reentrega sem duplicar a triagem na nuvem.")


if __name__ == "__main__":
    main()
