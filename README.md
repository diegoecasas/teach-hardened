# teach-hardened

Fork endurecido del skill [`teach`](https://github.com/mattpocock/skills/tree/main/skills/productivity/teach)
de Matt Pocock, para Claude Code y otros harnesses compatibles con Agent Skills.

El skill original convierte una sesión de Claude en un espacio de estudio con estado:
misión, recursos, glosario, registros de aprendizaje y lecciones en HTML que se acumulan
en un directorio a lo largo de meses. La pedagogía es buena y se conserva intacta. Lo que
cambia aquí es la postura frente a tres cosas que el original no acota.

## Por qué

**Escribía en el directorio actual sin preguntar.** El original dice literalmente que trate
el directorio actual como workspace y crea siete entradas — `MISSION.md`, `NOTES.md`,
`RESOURCES.md`, `lessons/`, `assets/`, `reference/`, `learning-records/` — sin confirmación
ni comprobación de colisiones. Lanzarlo desde tu home o desde un repo de trabajo te lo
siembra ahí, y `NOTES.md` es un nombre lo bastante genérico como para chocar con algo tuyo.

**No distinguía contenido descargado de instrucciones.** El skill ordena no fiarse del
conocimiento paramétrico y salir a buscar fuentes, y luego escribe lo aprendido en archivos
que se releen en sesiones posteriores como estado de confianza del workspace. Eso es una vía
de persistencia: contenido no confiable → archivo local → contexto confiable de la próxima
sesión. El original no dedicaba una sola línea al problema.

**Generaba HTML sin restricciones.** Las lecciones llevan JavaScript, se derivan en parte de
material descargado, y se abren en tu navegador desde `file://`. Sin CSP, sin prohibición de
llamadas de red, sin revisión.

## Qué cambia

| | |
|---|---|
| **Frontera del workspace** | Se niega a inicializar en `$HOME`, dentro de un repo git o en un directorio ocupado. Propone subdirectorio y espera confirmación. Nunca sobrescribe un archivo que no creó. Escribe `.gitignore`. |
| **Frontera de confianza** | El contenido descargado es dato, no instrucción — y sigue siéndolo al releerlo en sesiones futuras. No sigue URLs sugeridas por contenido descargado. `RESOURCES.md` exige procedencia. |
| **Lecciones autocontenidas** | Cero peticiones de red, cero `eval`, meta CSP con `default-src 'none'` obligatoria. Los enlaces salientes a fuentes primarias siguen permitidos. |
| **Citación verificable** | Solo se citan fuentes efectivamente recuperadas y registradas. Prohibido citar de memoria. Lo no verificado se declara. |
| **Seguridad en temas físicos** | Cribado de lesiones y condiciones antes de diseñar práctica física; no diagnosticar; derivar. |
| **Privacidad** | `MISSION.md` registra el objetivo, no la biografía. |

Más consistencia estructural: el glosario estaba huérfano, había deriva de vocabulario y
sintaxis de enlaces mezclada. El detalle completo, delta a delta, está en
[CHANGES-VS-UPSTREAM.md](./CHANGES-VS-UPSTREAM.md).

## Instalación

Como plugin:

```
/plugin marketplace add diegoecasas/teach-hardened
```

```
/plugin install teach-hardened
```

O a mano:

```bash
git clone https://github.com/diegoecasas/teach-hardened.git
cp -R teach-hardened/skills/teach-hardened ~/.claude/skills/
```

El skill se llama `teach-hardened`, no `teach`, para que conviva sin pisar al original si
tienes los dos.

## Uso

```
/teach-hardened <lo que quieras aprender>
```

Lleva `disable-model-invocation: true`: solo lo invocas tú, el modelo no puede lanzarlo por
su cuenta. Lo primero que hará es preguntarte **por qué** quieres aprender eso, y no te
dejará avanzar con una respuesta vaga. Es deliberado.

## Verificación

Dos auditores deterministas:

```bash
python3 tests/audit-skill.py --check-upstream
```

Comprueba que el endurecimiento sigue en su sitio — útil sobre todo después de traer cambios
de upstream, donde el riesgo es perderlo en silencio en un merge. Falla por nombre:
`hardening 'trust-boundary' missing`.

```bash
python3 tests/audit-workspace.py <dir-del-workspace>
```

Audita el resultado real: CSP, ausencia de red y `eval` en cada lección y asset, `.gitignore`,
workspace fuera de repo, procedencia en `RESOURCES.md`, y texto dirigido a agentes que haya
aterrizado en el workspace.

Ambos están validados en las dos direcciones: contra una copia mutada del skill (10 hallazgos
sobre 5 clases de mutación) y contra un workspace deliberadamente malo (9 fallos) y uno
conforme (0). Un linter que nunca ha fallado no prueba nada.

## Estado

| Prueba | Estado |
|---|---|
| Auditor de skill | Pasa |
| Auditor de workspace | Pasa |
| T1 — frontera del home | **Pasa** |
| T2 — repo git | Sin ejecutar |
| T3 — colisión de archivos | Sin ejecutar |
| T4 — inyección de prompt | Sin ejecutar |

**El endurecimiento contra inyección no está probado en ejecución.** Está revisado, no
verificado. [tests/TESTPLAN.md](./tests/TESTPLAN.md) tiene los cuatro escenarios con criterios
de paso y fallo; `tests/make-fixtures.sh` genera los fixtures. Los tests conductuales necesitan
que una persona invoque el skill, porque el modelo no puede.

## Créditos y licencia

El skill original es de [Matt Pocock](https://github.com/mattpocock), MIT. Este fork mantiene
esa licencia y añade el copyright de las modificaciones — ver [LICENSE](./LICENSE). Si te
interesa el trabajo original, su repo tiene [otros veinticuatro
skills](https://github.com/mattpocock/skills).

Los cambios de consistencia estructural de este fork no son opinables y encajarían en el repo
original; los de postura de seguridad sí lo son, y por eso viven aquí.
