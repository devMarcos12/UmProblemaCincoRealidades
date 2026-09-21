# Mapeamento de Restrições e Decisões Arquiteturais

| Restrição / Requisito que aperta | Origem | Decisão Arquitetural |
| :--- | :--- | :--- |
| **SLA de 99,9% com multa por indisponibilidade** | Envelope B | Infraestrutura Multi-AZ na AWS, serviços com *failover* automático e conectores assíncronos (filas/eventos) entre domínios críticos para evitar falhas em cascata. |
| **40 desenvolvedores em 5 times** | Envelope B | Estilo estrutural de Microsserviços. Cada time é dono de um subdomínio, com pipeline de CI/CD e unidade de implantação independentes no Kubernetes (Amazon EKS). |
| **UPA: internet instável, funcionar offline e sincronizar** | Caso Saúde | **A Decisão Mais Arriscada:** Componente de borda local na UPA (*Edge*) com banco embarcado (ex: SQLite) e conector do tipo fila assíncrona. Sincroniza em lote com a nuvem quando a rede volta. |
| **Prontuário: LGPD, retenção 20 anos, quem viu/alterou** | Caso Saúde | Estilo de dados *Event Sourcing*. O prontuário não atualiza linhas em um banco; anexa eventos clínicos imutáveis (*Append-only*) em um banco de alta durabilidade (DynamoDB). |
| **Regulação: disputa em tempo real e sistema legado ativo por 2 anos** | Caso Saúde | Padrão Camada Anticorrupção (ACL) para o legado. Uso de conectores de acesso a dado compartilhado com lock otimista/distribuído para garantir que dois hospitais não reservem o mesmo leito. |
| **Vigilância: notificar em 24h mesmo com sistema federal fora** | Caso Saúde | Conector do tipo evento/fila (Amazon SQS + EventBridge). A notificação é salva localmente e o consumidor faz *retries* exponenciais com *Dead Letter Queue* (DLQ) até o sistema federal aceitar. |
| **Agendamento: campanhas com pico de 20x o acesso** | Caso Saúde | Estilo de computação *Serverless* (Amazon API Gateway + AWS Lambda). Escala do zero a milhares de requisições instantaneamente sem provisionamento prévio, absorvendo a carga da campanha. |