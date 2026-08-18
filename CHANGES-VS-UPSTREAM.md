# Cambios respecto a upstream

Este repo es una obra derivada de [`mattpocock/skills`](https://github.com/mattpocock/skills),
skill `skills/productivity/teach`, bajo licencia MIT.

- **Upstream fijado:** `9c9f36ccd3995266cd675468af71639c8dde1ec5` (main, 2026-08-18)
- **Origen:** https://github.com/mattpocock/skills/tree/main/skills/productivity/teach

El skill original es bueno: la separación conocimiento/habilidad/sabiduría, la zona de
desarrollo próximo y los learning records son ideas sólidas y se conservan intactas. Lo
que cambia aquí es la postura frente a tres cosas que el original no acota: **dónde
escribe**, **qué hace con el contenido que descarga** y **qué HTML genera**.

## Fase 1 — contención

1. **Frontera del directorio de trabajo.** Sección nueva *Before You Begin: Choosing The
   Workspace Directory*. El original dice literalmente "trata el directorio actual como
   workspace de enseñanza" y crea siete entradas sin preguntar. Aquí se niega a inicializar
   en `$HOME`, dentro de un repo git o en un directorio ocupado; propone un subdirectorio y
   espera confirmación; comprueba colisiones antes de escribir `MISSION.md`, `NOTES.md` o
   `RESOURCES.md`; escribe un `.gitignore`.

2. **Frontera de confianza.** Sección nueva *Handling External Sources*. El original ordena
   no fiarse del conocimiento paramétrico y salir a buscar fuentes, pero no dice en ningún
   momento que lo descargado sea dato y no instrucción. Como `RESOURCES.md` y `NOTES.md` se
   releen en sesiones posteriores como estado de confianza del workspace, había una vía de
   persistencia: contenido no confiable → archivo local → contexto confiable de la próxima
   sesión. Aquí el contenido externo es dato explícitamente, la regla persiste entre
   sesiones, no se siguen URLs sugeridas por contenido descargado, y `RESOURCES.md` exige
   procedencia.

3. **Lecciones autocontenidas.** Sección nueva *Lessons Must Be Self-Contained*. Las
   lecciones son HTML con JavaScript, derivado en parte de contenido web, que se abre en el
   navegador desde `file://`. Aquí: cero peticiones de red, cero `eval`, y una meta CSP con
   `default-src 'none'` obligatoria en cada lección. Aplica igual a `./assets/`.

4. **Minimización de datos personales** en `MISSION.md` y `NOTES.md`.

## Fase 2 — contenido

5. **Citación verificable.** El original dice que las lecciones deben ir *"littered with
   citations… esto aumenta la confiabilidad"*. Aumenta la *apariencia* de confiabilidad. Sin
   ningún mecanismo de verificación, es una receta para citas alucinadas con aspecto
   autorizado. Aquí: citar solo fuentes recuperadas y registradas, prohibido citar de
   memoria, declarar explícitamente lo no verificado.

6. **Cribado de seguridad en temas físicos.** El original nombra yoga, posturas, fitness y
   rutinas como casos de uso de primera clase y no dice nada sobre lesiones ni límites
   médicos. Sección nueva *Topics Where Being Wrong Hurts*.

7. **Regla de quiz.** El original exige que todas las respuestas tengan exactamente el mismo
   número de caracteres, lo que fuerza a deformar los distractores. Aquí el objetivo es la
   indistinguibilidad de forma, con el contenido como desempate.

## Fase 3 — consistencia

8. `GLOSSARY-FORMAT.md` estaba huérfano: existía, era obligatorio según el texto, y `SKILL.md`
   no lo enlazaba ni listaba `GLOSSARY.md` entre los archivos del workspace. Cableado, y
   resuelta la contradicción entre `.md` en la raíz y `./reference/*.html`.
9. Deriva de vocabulario `explainers`/`exercises` → `lessons` en los cuatro format docs.
10. `[[wiki-links]]` → backticks, consistente con el resto.
11. Regla "escanea el máximo e incrementa" replicada en la numeración de lecciones.
12. `allowed-tools` en el frontmatter. **Si algo deja de funcionar, esta línea es la primera
    sospechosa** — bórrala y vuelves al comportamiento upstream.

## Fase 4 — verificación

13. `tests/audit-skill.py` — auditor estático: unicode invisible, 16 anclas de regresión del
    endurecimiento, frases revertidas de upstream, enlaces y anclas internas, allowlist de
    URLs, cordura del frontmatter, paridad con `openai.yaml`, deriva del SHA fijado.
14. `tests/audit-workspace.py` — auditor del resultado: CSP y ausencia de red o `eval` en cada
    lección, `.gitignore`, workspace fuera de repo, procedencia, texto dirigido a agentes.
15. `tests/make-fixtures.sh` y `tests/TESTPLAN.md` — los cuatro tests conductuales.

## Fase 5 — higiene frente a upstream

16. `tests/diff-upstream.py` — enseña qué cambió en upstream desde el SHA fijado, sin clonar
    nada. No compara upstream contra la copia local (ese diff sería enorme e inútil: el fork
    diverge a propósito), sino upstream consigo mismo entre dos puntos. Sale con 0 si no se
    movió y con 2 si hay algo que revisar. Validado en ambos casos, incluido un diff real
    contra un commit de junio de 2026.

Este fork es una copia, no symlinks al repo de upstream. Eso significa que no se actualiza
solo — deliberadamente: un `git pull` que cambie el skill sin revisión es exactamente el
riesgo que se quiere evitar. El precio es que hay que mirar a mano, y para eso están el
`--check-upstream` del auditor y este script.

## Estado de las pruebas

| Prueba | Estado |
|---|---|
| Auditor de skill | Pasa. Validado contra una copia mutada: 10 hallazgos sobre 5 clases de mutación |
| Auditor de workspace | Pasa. 0 fallos sobre un workspace conforme, 9 sobre uno deliberadamente malo |
| T1 — frontera del home | **Pasa** (2026-08-18, sesión limpia) |
| T2 — repo git | Sin ejecutar |
| T3 — colisión de archivos | Sin ejecutar |
| T4 — inyección de prompt | Sin ejecutar |

El delta 2, la frontera de confianza, es el más importante y **sigue sin probarse en
ejecución**: está revisado, no verificado. Es lo que cubre T4.

`allowed-tools` (delta 12) tampoco está probado en ejecución.

## Aguas arriba

Nada de esto se ha enviado a `mattpocock/skills`. Los deltas 6 y 8–11 son correcciones
genéricas que encajarían en el repo original.
