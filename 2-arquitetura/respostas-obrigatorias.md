# Decisões Arquiteturais e Respostas Técnicas

## 1. Operação Offline e Sincronização na UPA
Como a UPA continua triando e atendendo com a internet fora do ar, e o que acontece quando ela volta?

A UPA utiliza um componente de borda (Edge) na rede local com um banco de dados embarcado (como SQLite). Durante a queda, o sistema atende offline e gera IDs únicos universais (UUIDs) para cada paciente e triagem. Um processo local (fila/worker) acumula esses registros. Quando a internet é restabelecida, o worker empurra os dados para a AWS (ex: via Amazon SQS). O backend na nuvem utiliza o UUID como chave de idempotência para garantir que nenhum registro seja duplicado caso o envio falhe no meio do caminho.

* **Sustentação:** [ADR 0005] (operação local com sincronização) e Diagrama C4 Nível 3 (Componentes do App Local da UPA).


## 2. Gestão de Concorrência de Leitos com Sistema Legado
Como duas unidades disputando o mesmo leito nunca conseguem reservá-lo ao mesmo tempo, com o sistema legado ainda no circuito?

Como o legado é a fonte da verdade atual, a concorrência é gerenciada pela Camada Anticorrupção (ACL). Todas as requisições de reserva das UPAs batem em uma fila FIFO (First-In-First-Out, como o SQS FIFO) no microsserviço de regulação, que serializa os pedidos. A ACL consome essa fila um a um e aplica um lock otimista (ou transação ACID nativa) contra o banco legado. Se a unidade B tentar o leito frações de segundo após a unidade A, a fila garantirá que a ACL processe A primeiro, efetive a reserva no legado, e devolva um erro de "leito indisponível" para a requisição de B.

* **Sustentação:** [ADR 0003] (Camada Anticorrupção) e Diagrama C4 Nível 2 (Contêineres - Fila de Regulação e ACL).


## 3. Auditoria do Prontuário e Adequação à LGPD
Como o prontuário garante que se saiba quem acessou cada registro, e como convive a guarda de 20 anos com os direitos do paciente sob a LGPD?

O prontuário não utiliza um banco de dados tradicional (CRUD), mas sim um log imutável de eventos (Append-only), incluindo eventos de leitura (ex: `ProntuarioAcessadoPorMedicoX`). Isso garante a auditoria nativa exigida para os 20 anos. Para conviver com a LGPD (direito ao esquecimento vs. retenção legal), adota-se a técnica de *Crypto-shredding*: os dados clinicamente retidos por lei são mantidos em texto claro, mas dados estritamente de identificação pessoal que o paciente peça para apagar (quando a lei permitir) são encriptados, e a exclusão se dá apenas jogando fora a chave criptográfica, tornando os dados irreversivelmente anônimos sem quebrar o log imutável do sistema.

* **Sustentação:** [ADR 0002] (Event Sourcing) e Diagrama C4 Nível 2 (Contêineres - Banco de Eventos).

## 4. Notificação Compulsória e Resiliência Assíncrona

Como a notificação compulsória chega à vigilância em até 24 horas mesmo se o sistema federal estiver indisponível?

Utilizando o estilo de microsserviços com comunicação assíncrona. Quando o médico faz a notificação, o microsserviço de vigilância na AWS aceita a requisição, salva em seu banco próprio e publica o payload em uma fila de mensageria para integração externa. Um worker tenta enviar para a API federal. Se o sistema federal estiver fora, a mensagem não é descartada; ela entra em um ciclo de retries com *backoff* exponencial (espera 1 min, depois 2, depois 4...). Se falhar consecutivamente, vai para uma fila de mensagens mortas (*Dead Letter Queue* - DLQ) com um alarme no CloudWatch avisando a equipe de operação muito antes do prazo de 24h estourar.

* **Sustentação:** [ADR 0001] (Estrutura em Microsserviços/Assíncrona) e Diagrama C4 Nível 2 (Contêineres - Tópicos e DLQ).


## 5. Substituição Gradual do Sistema Legado
Como o sistema legado de regulação é substituído aos poucos sem interromper o serviço?

Através do padrão de Estrangulamento (*Strangler Fig Pattern*) operando em conjunto com a Camada Anticorrupção (ACL). O Amazon API Gateway atua como fachada para a rede. Novas funcionalidades de regulação (ex: visualização de painéis) são roteadas para o novo microsserviço, enquanto as reservas ainda são roteadas através da ACL para o legado. Mês a mês, as tabelas legadas são migradas para o banco novo, e o API Gateway ajusta o roteamento para o código novo. Após dois anos, o legado é estrangulado totalmente, a ACL é removida, e a operação ocorre 100% no novo ambiente sem o usuário final perceber a chaveada.

* **Sustentação:** [ADR 0003] (Camada Anticorrupção) e Diagrama C4 Nível 2 (Contêineres - API Gateway).