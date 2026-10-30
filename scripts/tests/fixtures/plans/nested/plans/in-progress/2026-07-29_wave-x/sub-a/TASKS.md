## Backlog

| ID | Stream | Owner | Area | Branch | Pri | Attivita' | Descrizione | Dip. | Effort |
|---|---|---|---|---|---|---|---|---|---|
| `T-001` | core | Alice | BE | — | P0 | Censimento | Elenco iniziale | — | 1,5 |
| `T-002` | core | Alice | BE | — | P0 | Import | Import da file a\|b | `T-001` | ~~`3 gg`~~ **0** |
| **T-003** | core | Bruno | FE | — | P1 | Maschera | Form di ricerca | T-002 | `4 gg` **+3,0 gg** → **7,0 gg** |
| T-004 | core | Bruno | FE | — | P1 | Esportazione | CSV | T-003 | (in T-003) |
| T-051-fix | core | Carla | BE | — | P2 | Correzione | Fix import | T-002, ext/T-010 | 1.0-1.5 |

## Seconda tranche

| ID | Owner | Layer | Prio | Titolo | Dipendenze | Effort |
|---|---|---|---|---|---|---|
| T-010 | Dario | BE | P1 | Notifiche | T-004 | 2
| T-011 | Dario | BE | P2 | Report | T-077 | parecchio |

## Domande al funzionale

| ID | Stato | Trasmesso il | Risposta |
|---|---|---|---|
| D-01 | Aperta | 2026-10-01 | — |
| D-02 | Chiusa | 2026-10-02 | Sì |
