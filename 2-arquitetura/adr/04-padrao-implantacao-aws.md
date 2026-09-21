# ADR 04: padronizar a implantação em kubernetes em nuvem pública multizona

**Status:** aceito

**Contexto:** O contrato estabelece um SLA de disponibilidade de 99,9% com aplicação de multas. O envelope garante um orçamento robusto e infraestrutura em nuvem pública, que será operada por uma equipe própria de infraestrutura.

**Decisão:** Implantar as cargas de trabalho conteinerizadas dos microsserviços em um cluster Kubernetes (AWS EKS) distribuído nativamente em três zonas de disponibilidade, declarando toda a infraestrutura como código (IaC).

**Alternativas consideradas:**
- Máquinas Virtuais simples provisionadas manualmente: descartado pois a recuperação de falhas é lenta e manual, o que arriscaria frequentemente a perda da SLA de 99,9%.
- Plataformas gerenciadas de entrada (PaaS): descartado por falta de controle granular de rede e segurança que a integração com os sistemas federais de saúde e a vigilância exigem.

**Consequências:**
- Positivas: resiliência de classe empresarial com autorrecuperação (self-healing) de contêineres inativos; zero downtime durante atualizações das 5 equipes.
- Negativas: acréscimo considerável na complexidade de infraestrutura, exigindo que a equipe de operação domine o Kubernetes e orquestração de malha de serviços.