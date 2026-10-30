| ID | Stream | Owner | Area | Branch | Priorità | Attività | Descrizione | Dipendenze | Effort |
|---|---|---|---|---|---|---|---|---|---|
| T-001 | fnd | Alice | BE | — | P0 | Modello dati | Tabelle base | — | `2 gg` |
| T-002 | fnd | Alice | BE | — | P0 | API elenco | Endpoint GET | T-001 | `1 gg` |
| T-003 | ui | Bruno | FE | — | P1 | Pagina elenco | Vista tabellare | T-002 | `2 gg` |
| T-004 | ui | Bruno | FE | — | P1 | Filtri | Filtri per stato | T-003 | `1,5 gg` |
| T-005 | qa | Carla | QA | — | P2 | Test e2e | Percorso principale | T-003, T-004 | `1 gg` |
| T-MERGE-003 | merge | Bruno | FE | — | P1 | Merge pagina | Unione in develop | T-003 | `0,5 gg` |
