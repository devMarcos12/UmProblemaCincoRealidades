# ADR 0005: adotar operação local com sincronização assíncrona para UPAs offline

**Status:** aceito

**Contexto:** As Unidades de Pronto Atendimento (UPAs) enfrentam quedas diárias de internet que duram de minutos a horas. A UPA precisa continuar triando e classificando riscos em tempo real sem a rede, e os dados não podem ser perdidos nem duplicados quando a conexão retornar.

**Decisão:** Instalar um componente de borda (Edge) na rede local da UPA que inclua um banco de dados embarcado. O sistema atende offline gerando IDs únicos universais (UUIDs). Um conector de fluxo de dados local acumula os registros e os transmite para uma fila na nuvem usando apenas quando a internet é restabelecida.

**Alternativas consideradas:**
- Sincronização direta mestre-escravo de banco de dados via rede: descartado pois a alta instabilidade da conexão gera falhas constantes de replicação de banco, corrompendo a ordem das triagens.
- Service workers de cache de navegador: descartado pois a instabilidade pode durar horas, excedendo os limites seguros de armazenamento volátil do navegador de um único computador de triagem.

**Consequências:**
- Positivas: a triagem da UPA nunca para, mitigando riscos de vida; o uso de UUIDs na geração local atua como chave de idempotência na nuvem, bloqueando duplicações de registros quando a rede volta.
- Negativas: complexidade na resolução de eventuais conflitos temporais (paciente triado offline que é registrado na nuvem de forma atrasada em relação a outro evento sistêmico).