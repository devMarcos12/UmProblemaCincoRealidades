# ADR 0002: utilizar event sourcing para o armazenamento do prontuário eletrônico

**Status:** aceito

**Contexto:** O prontuário clínico é um dado sensível regulado pela LGPD, com guarda obrigatória por 20 anos. O sistema exige a capacidade inquestionável de demonstrar quem visualizou e quem alterou cada registro médico ao longo de toda a vida do paciente, de forma auditável e segura.

**Decisão:** Adotar o estilo Event Sourcing para o subdomínio de prontuários, armazenando o estado não como linhas em tabelas, mas como uma sequência imutável de eventos clínicos em um log. 

**Alternativas consideradas:**
- Banco de dados relacional tradicional (CRUD) com tabelas de log: descartado pois um administrador de banco de dados poderia alterar os registros de log com operações manuais direto no banco de dados, invalidando a garantia criptográfica de imutabilidade exigida para uma guarda de 20 anos.

**Consequências:**
- Positivas: auditoria nativa, absoluta e imutável; conformidade direta com a LGPD no rastreio de alterações; o estado passado do prontuário pode ser reconstruído a qualquer momento.
- Negativas: curva de aprendizado mais íngreme para os desenvolvedores e necessidade de introduzir CQRS para manter o desempenho nas projeções de leitura do prontuário.