import sqlite3
import uuid


# UUID fixo para que o resultado seja sempre igual em toda execução.
NAMESPACE = uuid.UUID("3f6d9ec7-4d4a-4d52-bf22-df4a9fd35e17")


def criar_banco_local():
    banco = sqlite3.connect(":memory:")
    banco.row_factory = sqlite3.Row
    banco.execute(
        """
        CREATE TABLE triagens (
            id TEXT PRIMARY KEY,
            paciente TEXT NOT NULL,
            risco TEXT NOT NULL,
            horario TEXT NOT NULL,
            sincronizado INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    return banco


def criar_id(chave):
    return str(uuid.uuid5(NAMESPACE, chave))


def salvar_triagem(banco, chave, paciente, risco, horario):
    triagem_id = criar_id(chave)
    banco.execute(
        """
        INSERT INTO triagens (id, paciente, risco, horario)
        VALUES (?, ?, ?, ?)
        """,
        (triagem_id, paciente, risco, horario),
    )
    banco.commit()
    return triagem_id


def buscar_pendentes(banco):
    linhas = banco.execute(
        """
        SELECT id, paciente, risco, horario
        FROM triagens
        WHERE sincronizado = 0
        ORDER BY horario
        """
    ).fetchall()
    return [dict(linha) for linha in linhas]


def marcar_como_sincronizado(banco, triagem_id):
    banco.execute(
        "UPDATE triagens SET sincronizado = 1 WHERE id = ?",
        (triagem_id,),
    )
    banco.commit()


def total_local(banco):
    return banco.execute("SELECT COUNT(*) FROM triagens").fetchone()[0]


def enviar_para_nuvem(triagem, nuvem, rede):
    if not rede["online"]:
        return "SEM_REDE"

    rede["tentativas"] += 1
    triagem_id = triagem["id"]

    # Se o mesmo id já chegou antes, não grava de novo.
    if triagem_id in nuvem:
        rede["duplicatas"] += 1
        return "DUPLICATA"

    nuvem[triagem_id] = triagem

    # Simula o caso em que a nuvem recebeu o dado,
    # mas a confirmação não chegou de volta para a UPA.
    if rede["perder_proximo_ack"]:
        rede["perder_proximo_ack"] = False
        return "ACK_PERDIDO"

    return "OK"


def sincronizar(banco, nuvem, rede):
    mensagens = []

    for triagem in buscar_pendentes(banco):
        resultado = enviar_para_nuvem(triagem, nuvem, rede)
        paciente = triagem["paciente"]

        if resultado == "SEM_REDE":
            mensagens.append(f"{paciente}: sem rede, continua pendente")
            break

        if resultado == "ACK_PERDIDO":
            mensagens.append(f"{paciente}: confirmacao perdida, sera reenviado")
            continue

        if resultado == "DUPLICATA":
            marcar_como_sincronizado(banco, triagem["id"])
            mensagens.append(f"{paciente}: duplicata detectada e ignorada")
            continue

        marcar_como_sincronizado(banco, triagem["id"])
        mensagens.append(f"{paciente}: sincronizado")

    return mensagens


def mostrar_mensagens(mensagens):
    for mensagem in mensagens:
        print("  " + mensagem)


def main():
    banco = criar_banco_local()
    nuvem = {}
    rede = {
        "online": False,
        "perder_proximo_ack": True,
        "tentativas": 0,
        "duplicatas": 0,
    }

    print("=== SPIKE ADR 05 ===")
    print("\n1) UPA sem internet")

    id1 = salvar_triagem(
        banco,
        "upa-17/001",
        "PAC-001",
        "VERMELHO",
        "2026-09-25T10:00:00",
    )
    id2 = salvar_triagem(
        banco,
        "upa-17/002",
        "PAC-002",
        "AMARELO",
        "2026-09-25T10:02:00",
    )

    print(f"  PAC-001 salvo localmente | id={id1}")
    print(f"  PAC-002 salvo localmente | id={id2}")
    print(f"  pendentes: {len(buscar_pendentes(banco))}")

    print("\n2) Tentativa de sincronizar ainda sem internet")
    mostrar_mensagens(sincronizar(banco, nuvem, rede))
    print(f"  registros na nuvem: {len(nuvem)}")

    print("\n3) Internet volta, mas a primeira confirmacao se perde")
    rede["online"] = True
    mostrar_mensagens(sincronizar(banco, nuvem, rede))
    print(f"  pendentes: {len(buscar_pendentes(banco))}")
    print(f"  registros na nuvem: {len(nuvem)}")

    print("\n4) Nova tentativa de sincronizacao")
    mostrar_mensagens(sincronizar(banco, nuvem, rede))
    print(f"  pendentes: {len(buscar_pendentes(banco))}")
    print(f"  registros na nuvem: {len(nuvem)}")

    print("\n5) Resultado final")
    print(f"  triagens locais: {total_local(banco)}")
    print(f"  tentativas de envio: {rede['tentativas']}")
    print(f"  duplicatas bloqueadas: {rede['duplicatas']}")
    print(f"  triagens unicas na nuvem: {len(nuvem)}")

    deu_certo = (
        total_local(banco) == 2
        and len(buscar_pendentes(banco)) == 0
        and len(nuvem) == 2
        and rede["duplicatas"] == 1
    )

    if deu_certo:
        print("\nPROVA: SUCESSO")
        print("A reentrega nao criou uma triagem duplicada.")
    else:
        print("\nPROVA: FALHA")


if __name__ == "__main__":
    main()
