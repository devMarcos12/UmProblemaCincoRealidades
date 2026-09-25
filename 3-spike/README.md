# Spike — ADR 05: operação offline e sincronização assíncrona

Este programa foi feito para provar o **ADR 05**, que define que a UPA deve continuar funcionando mesmo quando estiver sem internet e sincronizar os dados depois que a conexão voltar.

O ponto que eu quis testar é o seguinte: uma triagem é salva localmente, depois é enviada para a nuvem. Só que pode acontecer de a nuvem receber o registro e a confirmação não voltar para a UPA. Nesse caso, a UPA entende que ainda precisa enviar e tenta novamente. Se não existir um controle de duplicidade, a mesma triagem poderia ficar salva duas vezes.

No `exemplo.py`, o banco local da UPA é simulado com `sqlite3` e a nuvem é simulada com um dicionário do Python. Cada triagem recebe um UUID. Quando a mesma triagem é enviada de novo, a nuvem verifica esse UUID e percebe que aquele registro já foi recebido, então ignora a duplicata.

A rede também é simulada. No começo ela está offline. Depois ela volta, mas a confirmação do primeiro envio é perdida de propósito. Isso faz o programa reenviar a primeira triagem e permite testar se a duplicidade é realmente evitada.

## Como rodar

Na pasta `3-spike`, usando Python 3.12:

```bash
python3 exemplo.py
```

A saída deve ser igual ao arquivo `saida-esperada.txt`. No final deve aparecer:

```text
PROVA: SUCESSO
A reentrega nao criou uma triagem duplicada.
```

## Se a decisão estivesse errada

Se o sistema não mantivesse o mesmo UUID no reenvio, ou se a nuvem não verificasse esse UUID antes de salvar, a primeira triagem seria gravada duas vezes. Nesse exemplo, teríamos duas triagens criadas na UPA, mas três registros na nuvem. Isso mostraria que a solução não é segura para uma situação real de queda de conexão.

Também seria um problema se a UPA dependesse da internet para registrar a triagem, porque durante uma queda de rede o atendimento poderia parar ou os dados poderiam ser perdidos. Por isso o spike testa justamente as duas partes mais importantes do ADR: salvar localmente e sincronizar sem duplicar.
