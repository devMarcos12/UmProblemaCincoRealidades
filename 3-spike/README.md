# Spike — ADR 05: operação offline e sincronização assíncrona

Este spike prova a decisão registrada no **ADR 05 — “adotar operação local com sincronização assíncrona para UPAs offline”**, identificada no mapa de restrições como a decisão arquitetural mais arriscada. O risco central é permitir que a UPA continue registrando triagens durante uma queda de internet e, depois, sincronize os dados sem criar registros duplicados. O programa reduz esse cenário ao mecanismo essencial: um banco local embarcado, uma rede simulada, um destino em nuvem e um worker de sincronização.

O arquivo `exemplo.py` usa somente a biblioteca padrão do Python. O banco local é implementado com `sqlite3`, representando o componente Edge da UPA. Cada triagem recebe um UUID, usado como chave de idempotência no destino em nuvem. Para tornar a execução totalmente reproduzível, o spike usa `uuid.uuid5` com entradas fixas; em produção, a geração poderia usar outro tipo de UUID adequado ao sistema sem alterar o mecanismo demonstrado.

O cenário força a situação mais perigosa para uma sincronização “ao menos uma vez”: a internet volta, a nuvem aceita a primeira triagem, mas a confirmação (ACK) se perde antes de o Edge marcar o item como sincronizado. Assim, o worker precisa reenviar o mesmo registro. A nuvem reconhece o mesmo UUID, devolve `DUPLICATA_IGNORADA` e não cria uma segunda triagem. Em seguida, os itens restantes são sincronizados normalmente.

## Como rodar

A partir desta pasta, com **Python 3.12**:

```bash
python3 exemplo.py
```

A saída deve ser exatamente a registrada em `saida-esperada.txt`. O resultado final esperado é `PROVA: SUCESSO`, com duas triagens criadas localmente, duas triagens únicas na nuvem e uma duplicata bloqueada durante a reentrega.

## O que aconteceria se a decisão estivesse errada

Se o UUID não fosse preservado entre as tentativas, ou se a nuvem não tratasse esse UUID como chave de idempotência, a perda do ACK faria o worker reenviar a triagem e o destino a gravaria novamente. Nesse caso, duas triagens locais poderiam virar três registros remotos, provando que a estratégia não é segura para as quedas de rede descritas no ADR. Da mesma forma, se não existisse armazenamento local, a indisponibilidade da rede impediria a triagem ou causaria perda de dados. O spike, portanto, testa diretamente os dois pressupostos essenciais do ADR 05: **continuidade offline** e **sincronização idempotente após reconexão**.
