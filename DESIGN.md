# DESIGN.md — Notas de Diseño

## Branch Queue: Gestor de Cola por Servicio

### Estudiante: [Tu Nombre]

### Curso: [Nombre del Curso]

---

## 1. Estructura de datos: ¿Por qué una cola separada por tipo de servicio?

### El problema con una única lista compartida

Si mantuviésemos **una única lista ordenada** con todos los clientes sin importar su tipo de servicio, cuando un agente de, por ejemplo, `deposito` terminase con su cliente actual y quisiera llamar al siguiente, tendría que **recorrer toda la lista** desde el principio hasta encontrar el primer cliente cuyo `service_type` sea `deposito`.

En el peor caso —si los clientes de `retiro` y `gestion_cuenta` llegan constantemente— el agente de `deposito` podría tener que examinar cientos de tickets antes de encontrar al siguiente cliente de `deposito`. Esto hace que `call_next` sea una operación **O(n)**, donde `n` es el número total de clientes en todas las colas, lo cual **no escala** a medida que la sucursal se llena.

### La solución: una cola independiente por servicio

En nuestro diseño, mantenemos **un `collections.deque` por cada tipo de servicio**. Así, cuando un agente llama a `call_next("deposito")`, simplemente hace `popleft()` en la cola de depósitos, que es una operación **O(1)** — instantánea y de tiempo constante, sin importar cuántas personas estén esperando para `retiro` o `gestion_cuenta`.

| Operación               | Cola única compartida        | Colas separadas por servicio    |
| ----------------------- | ---------------------------- | ------------------------------- |
| `call_next("deposito")` | O(n) — recorre toda la lista | O(1) — `popleft()` directo      |
| `issue_ticket(...)`     | O(1) — append al final       | O(1) — append al deque correcto |
| `list_waiting()`        | O(n) — filtrar por servicio  | O(n) — concatenar deques        |
| `stats()`               | O(n) — contar por servicio   | O(n) — `len()` de cada deque    |

Además, **cada cola mantiene automáticamente el orden FIFO** porque usamos `deque`: los tickets se agregan por la derecha (`.append()`) y se retiran por la izquierda (`.popleft()`). Esto garantiza que dentro de cada servicio, los clientes sean atendidos en estricto orden de llegada.

### Contador global secuencial

Aunque tenemos colas separadas, el número de ticket es **globalmente secuencial** a través de todos los servicios. Esto se logra con un único contador `self.ticket_counter` en la clase `BranchQueue` que se incrementa cada vez que se emite un ticket, sin importar el servicio. Así, el ticket #5 emitido para `retiro` y el ticket #6 emitido para `deposito` mantienen el orden histórico de llegada a la sucursal, aunque estén en colas diferentes.

---

## 2. Concurrencia: ¿Qué ocurre si dos agentes del mismo servicio llaman a `call_next` al mismo tiempo?

### El escenario

Imaginemos que tenemos dos agentes asignados al servicio `retiro` (algo que no contemplamos explícitamente en el enunciado, pero que es un caso de concurrencia interesante). Ambos agentes terminan su atención casi simultáneamente y ambos ejecutan `call_next("retiro")`.

### El problema

Si ambos agentes ejecutan el método concurrentemente (por ejemplo, en un sistema con hilos/threads), existe una **condición de carrera**:

1. Agente A lee el primer ticket de la cola de `retiro`.
2. Agente B también lee el primer ticket de la misma cola.
3. Ambos ven el **mismo cliente** como el siguiente a atender.
4. El mismo cliente sería llamado **dos veces** por dos agentes distintos.

### La solución: orden de mutación

Para garantizar que el mismo cliente no sea atendido dos veces, la **mutación del estado (desencolar) debe ocurrir antes de devolver el ticket al agente**. En nuestro método `call_next()`:

```python
def call_next(self, service_type):
    # 1. PRIMERO: Validar que la cola no esté vacía
    # 2. PRIMERO (mutación): Desencolar el ticket (popleft)
    ticket = self.queues[service_type].popleft()
    # 3. DESPUÉS: Retornar el ticket al agente
    return ticket
```

El orden crítico es: **desencolar primero, retornar después**. Una vez que `popleft()` se ejecuta, ese ticket ya no está disponible para ningún otro agente. Cualquier llamada concurrente posterior encontrará la cola con un elemento menos (o vacía).

En un entorno **multihilo real**, incluso este orden no es suficiente porque `popleft()` y la lectura de la cola no son atómicas entre dos hilos. Para un sistema productivo, se necesitarían mecanismos de sincronización como:

1. **Lock/Mutex**: Envolver la operación de `call_next` en un `threading.Lock()` para que solo un agente a la vez pueda modificar el estado de las colas.
2. **Cola thread-safe**: Usar `queue.Queue` en lugar de `collections.deque`, que ya incluye locks internos.

Sin embargo, para nuestro proyecto de terminal (monohilo), el orden de mutación presentado es suficiente y correcto: la operación `popleft()` es atómica dentro de un solo hilo de ejecución.

---

## Resumen de decisiones de diseño

| Decisión                        | Alternativa descartada | Razón                                            |
| ------------------------------- | ---------------------- | ------------------------------------------------ |
| Colas separadas por servicio    | Única cola global      | Eficiencia O(1) en `call_next`                   |
| `collections.deque` para colas  | `list` con `pop(0)`    | `deque.popleft()` es O(1); `list.pop(0)` es O(n) |
| `dataclass` para Ticket         | Diccionario simple     | Código más legible y tipado                      |
| Contador global único           | Contador por servicio  | Tickets secuenciales globalmente                 |
| `datetime.now()` para timestamp | `time.time()`          | Más legible y formateable                        |

---

_Documento generado como parte del proyecto Branch Queue — 4Geeks Academy._
