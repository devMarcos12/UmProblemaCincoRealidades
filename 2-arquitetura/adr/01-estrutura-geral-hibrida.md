# ADR 0001: estruturar o sistema em microsserviços com agendamento serverless

**Status:** aceito

**Contexto:** O projeto é mantido por um consórcio de 5 times trabalhando em paralelo (40 desenvolvedores) e possui um contrato rigoroso de SLA de 99,9% com multa. Além disso, o subdomínio de agendamento sofre picos sazonais de acesso na ordem de 20 vezes o tráfego normal durante campanhas de vacinação. O restante da rede exige evolução independente e alta resiliência por subdomínio.

**Decisão:** Adotar o estilo arquitetural de microsserviços para os subdomínios centrais (prontuário, farmácia, regulação, vigilância) e o estilo serverless exclusivamente para o subdomínio de agendamento e cidadão. As fronteiras se dão pela separação das unidades de implantação e a comunicação inter-domínios será assíncrona por eventos sempre que possível.

**Alternativas consideradas:**
- Monolito modular: descartado porque a unidade única de implantação limitaria severamente o pipeline de entrega concorrente dos 5 times e criaria um ponto único de falha global, causando diversos gargalos pela quantidade de desenvolvedores trabalhando simultaneamente em um único repositório.
- Tudo em serverless: descartado pois o tempo de aquecimento (cold start) em nuvem pública prejudicaria o desempenho de domínios sensíveis à latência, como a regulação de leitos, isso poderia ser revertido com alguma estrategis para evitar o cold start, porém acaberia sendo custoso.

**Consequências:**
- Positivas: autonomia de implantação por time (reduzindo gargalos), isolamento de falhas favorecendo a SLA de 99,9% e escalabilidade absoluta nos picos de vacinação.
- Negativas: alta complexidade operacional para manter e monitorar ambientes heterogêneos; necessidade de observabilidade distribuída para rastrear requisições.