# ADR 03: implementar camada anticorrupção para a integração de leitos legado

**Status:** aceito

**Contexto:** O sistema atual de regulação de leitos não pode ser desligado antes de dois anos. As unidades de saúde disputam vagas em tempo real, exigindo consistência forte. O novo sistema precisa coordenar essas reservas sem que o modelo de banco de dados antigo dite a arquitetura do novo sistema.

**Decisão:** Desenvolver um conector do tipo adaptador implementando o padrão Camada Anticorrupção (Anti-corruption Layer) entre o novo microsserviço de regulação e o sistema legado, fazendo a tradução bidirecional das entidades de domínio.

**Alternativas consideradas:**
- Acesso direto ao banco de dados legado (Acesso a dado compartilhado): descartado porque espalharia um modelo de domínio obsoleto por todo o novo código, fundindo os quanta arquiteturais e engessando o microsserviço.

**Consequências:**
- Positivas: o novo sistema evolui com seu próprio modelo de domínio livre do legado; o desligamento do sistema antigo daqui a dois anos exigirá mudanças apenas na camada adaptadora, sem tocar no core do negócio.
- Negativas: esforço imediato de desenvolvimento maior para projetar e manter a camada de tradução em tempo real.