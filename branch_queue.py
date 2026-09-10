#!/usr/bin/env python3
"""
branch_queue.py — Branch Queue: Gestor de Cola por Servicio

Sistema de gestión de colas para el Banco Meridional.
Cada tipo de servicio (deposito, retiro, gestion_cuenta) tiene su propia cola
independiente, permitiendo que los agentes trabajen en paralelo.

Autor: [Tu Nombre]
Curso: [Nombre del Curso]
"""

from dataclasses import dataclass
from datetime import datetime
from collections import deque
import sys

# =============================================================================
# CONSTANTES
# =============================================================================

# Tipos de servicio válidos para el banco
SERVICE_TYPES = ["deposito", "retiro", "gestion_cuenta"]


# =============================================================================
# MODELO DE DATOS: Ticket
# =============================================================================

@dataclass
class Ticket:
    """
    Representa un ticket emitido a un cliente.

    Atributos:
        number (int): Número de ticket secuencial global (compartido entre
                      todos los servicios).
        client_name (str): Nombre del cliente que solicitó el ticket.
        service_type (str): Tipo de servicio solicitado ("deposito", "retiro"
                            o "gestion_cuenta").
        issued_at (datetime): Marca de tiempo del momento en que se emitió
                              el ticket.
    """
    number: int
    client_name: str
    service_type: str
    issued_at: datetime


# =============================================================================
# CLASE PRINCIPAL: BranchQueue
# =============================================================================

class BranchQueue:
    """
    Gestiona las colas de espera del banco, organizadas por tipo de servicio.

    En lugar de usar una única cola global (que requeriría recorrerla completa
    para encontrar al siguiente cliente de un servicio específico), mantenemos
    una cola independiente por cada tipo de servicio usando collections.deque.
    Esto hace que la operación call_next() sea O(1) — instantánea — sin
    importar cuántos clientes esperen en otros servicios.

    Atributos:
        queues (dict): Diccionario que mapea tipo de servicio -> deque de Tickets.
        ticket_counter (int): Contador global secuencial de tickets emitidos.
    """

    def __init__(self):
        """Inicializa el gestor de colas con una cola vacía por servicio."""
        # Creamos una cola (deque) para cada tipo de servicio
        self.queues = {service: deque() for service in SERVICE_TYPES}
        # Contador global de tickets: comienza en 0 (el primer ticket será el #1)
        self.ticket_counter = 0

    # -------------------------------------------------------------------------
    # issue_ticket
    # -------------------------------------------------------------------------

    def issue_ticket(self, client_name: str, service_type: str) -> Ticket:
        """
        Emite un nuevo ticket para un cliente y lo encola en el servicio
        correspondiente.

        Parámetros:
            client_name (str): Nombre del cliente.
            service_type (str): Tipo de servicio solicitado.

        Retorna:
            Ticket: El ticket recién creado y encolado.

        Lanza:
            ValueError: Si el tipo de servicio no es válido.
        """
        # Validar que el tipo de servicio sea uno de los permitidos
        if service_type not in SERVICE_TYPES:
            valid_services = ", ".join(SERVICE_TYPES)
            raise ValueError(
                f"Tipo de servicio inválido: '{service_type}'. "
                f"Los servicios válidos son: {valid_services}."
            )

        # Incrementar el contador global (secuencial entre todos los servicios)
        self.ticket_counter += 1

        # Crear el ticket con la marca de tiempo actual
        ticket = Ticket(
            number=self.ticket_counter,
            client_name=client_name,
            service_type=service_type,
            issued_at=datetime.now()
        )

        # Encolar el ticket en la cola correspondiente a su servicio
        self.queues[service_type].append(ticket)

        return ticket

    # -------------------------------------------------------------------------
    # call_next
    # -------------------------------------------------------------------------

    def call_next(self, service_type: str) -> Ticket:
        """
        Desencola y retorna el siguiente cliente en espera para un tipo de
        servicio dado. Los clientes son atendidos en estricto orden de llegada
        (FIFO).

        Parámetros:
            service_type (str): Tipo de servicio del agente que llama.

        Retorna:
            Ticket: El ticket del cliente que debe ser atendido ahora.

        Lanza:
            ValueError: Si el tipo de servicio no es válido.
            IndexError: Si no hay clientes esperando para ese servicio.
        """
        # Validar tipo de servicio
        if service_type not in SERVICE_TYPES:
            valid_services = ", ".join(SERVICE_TYPES)
            raise ValueError(
                f"Tipo de servicio inválido: '{service_type}'. "
                f"Los servicios válidos son: {valid_services}."
            )

        # Verificar si la cola está vacía
        if not self.queues[service_type]:
            raise IndexError(
                f"No hay clientes esperando para el servicio '{service_type}'."
            )

        # Desencolar el ticket más antiguo de esa cola (FIFO: pop left)
        ticket = self.queues[service_type].popleft()
        return ticket

    # -------------------------------------------------------------------------
    # peek_next
    # -------------------------------------------------------------------------

    def peek_next(self, service_type: str) -> Ticket:
        """
        Muestra quién es el siguiente cliente para un tipo de servicio sin
        retirarlo de la cola.

        Parámetros:
            service_type (str): Tipo de servicio a consultar.

        Retorna:
            Ticket: El siguiente ticket en la cola (sin desencolar).

        Lanza:
            ValueError: Si el tipo de servicio no es válido.
            IndexError: Si no hay clientes esperando para ese servicio.
        """
        # Validar tipo de servicio
        if service_type not in SERVICE_TYPES:
            valid_services = ", ".join(SERVICE_TYPES)
            raise ValueError(
                f"Tipo de servicio inválido: '{service_type}'. "
                f"Los servicios válidos son: {valid_services}."
            )

        # Verificar si la cola está vacía
        if not self.queues[service_type]:
            raise IndexError(
                f"No hay clientes esperando para el servicio '{service_type}'."
            )

        # Retornar el primer ticket sin desencolarlo
        ticket = self.queues[service_type][0]
        return ticket

    # -------------------------------------------------------------------------
    # list_waiting
    # -------------------------------------------------------------------------

    def list_waiting(self) -> dict:
        """
        Retorna todos los clientes en espera, agrupados por tipo de servicio,
        en el orden en que serán atendidos dentro de cada grupo.

        Retorna:
            dict: Diccionario con tipo de servicio como clave y lista ordenada
                  de Tickets como valor.
        """
        result = {}
        for service in SERVICE_TYPES:
            # Convertir el deque a lista para su presentación
            # (los tickets ya están en orden FIFO dentro del deque)
            result[service] = list(self.queues[service])
        return result

    # -------------------------------------------------------------------------
    # stats
    # -------------------------------------------------------------------------

    def stats(self) -> dict:
        """
        Reporta el número de clientes en espera por tipo de servicio y el
        total general.

        Retorna:
            dict: Diccionario con cantidad por servicio y clave "total".
        """
        stats_dict = {}
        total = 0
        for service in SERVICE_TYPES:
            count = len(self.queues[service])
            stats_dict[service] = count
            total += count
        stats_dict["total"] = total
        return stats_dict


# =============================================================================
# INTERFAZ DE LÍNEA DE COMANDOS (CLI)
# =============================================================================

def print_header():
    """Imprime el encabezado del sistema."""
    print("\n" + "=" * 60)
    print("  🏦  BRANCH QUEUE — Gestor de Cola por Servicio")
    print("  Banco Meridional — Sistema de Gestión de Turnos")
    print("=" * 60)


def print_menu():
    """Imprime el menú de opciones disponible."""
    print("\n  📋 MENÚ PRINCIPAL:")
    print("  " + "-" * 56)
    print("    1. 📄 Emitir nuevo ticket")
    print("    2. 📞 Llamar al siguiente cliente")
    print("    3. 👀 Ver siguiente cliente (sin llamarlo)")
    print("    4. 📋 Ver lista de espera completa")
    print("    5. 📊 Ver estadísticas de la cola")
    print("    6. ❌ Salir")
    print("  " + "-" * 56)


def select_service_type(prompt: str) -> str:
    """
    Solicita al usuario que seleccione un tipo de servicio.

    Parámetros:
        prompt (str): Mensaje a mostrar al usuario.

    Retorna:
        str: El tipo de servicio seleccionado.
    """
    print(f"\n  {prompt}")
    print("  Opciones de servicio:")
    for i, service in enumerate(SERVICE_TYPES, 1):
        print(f"    {i}. {service}")
    while True:
        try:
            choice = input("  Seleccione el número de servicio: ").strip()
            idx = int(choice)
            if 1 <= idx <= len(SERVICE_TYPES):
                return SERVICE_TYPES[idx - 1]
            else:
                print(f"  ⚠️  Número inválido. Elija entre 1 y {len(SERVICE_TYPES)}.")
        except ValueError:
            print("  ⚠️  Por favor, ingrese un número válido.")


def run_cli():
    """
    Ejecuta el bucle principal del menú interactivo.

    Permite al usuario:
      - Emitir tickets (ingresando nombre del cliente y tipo de servicio)
      - Llamar al siguiente cliente para un servicio
      - Ver el siguiente cliente sin llamarlo
      - Ver la lista de espera completa
      - Ver estadísticas
      - Salir del programa
    """
    queue_system = BranchQueue()

    while True:
        print_header()
        print_menu()

        option = input("\n  ➤ Ingrese una opción: ").strip()

        # ---------------------------------------------------------
        # Opción 1: Emitir nuevo ticket
        # ---------------------------------------------------------
        if option == "1":
            print("\n  📄 EMITIR NUEVO TICKET")
            print("  " + "-" * 56)
            client_name = input("  Nombre del cliente: ").strip()
            if not client_name:
                print("  ⚠️  El nombre del cliente no puede estar vacío.")
                input("  Presione Enter para continuar...")
                continue

            service_type = select_service_type("Seleccione el tipo de servicio:")

            try:
                ticket = queue_system.issue_ticket(client_name, service_type)
                print(f"\n  ✅ Ticket emitido exitosamente:")
                print(f"     N° {ticket.number:04d} | Cliente: {ticket.client_name}")
                print(f"     Servicio: {ticket.service_type}")
                print(f"     Hora de emisión: {ticket.issued_at.strftime('%H:%M:%S')}")
            except ValueError as e:
                print(f"\n  ❌ Error: {e}")

            input("\n  Presione Enter para continuar...")

        # ---------------------------------------------------------
        # Opción 2: Llamar al siguiente cliente
        # ---------------------------------------------------------
        elif option == "2":
            print("\n  📞 LLAMAR AL SIGUIENTE CLIENTE")
            print("  " + "-" * 56)
            service_type = select_service_type("Seleccione el servicio del agente:")

            try:
                ticket = queue_system.call_next(service_type)
                print(f"\n  🔔 ¡Cliente llamando!")
                print(f"     Ticket N° {ticket.number:04d}")
                print(f"     Cliente: {ticket.client_name}")
                print(f"     Servicio: {ticket.service_type}")
                print(f"     Hora de emisión: {ticket.issued_at.strftime('%H:%M:%S')}")
            except IndexError as e:
                print(f"\n  ℹ️  {e}")
            except ValueError as e:
                print(f"\n  ❌ Error: {e}")

            input("\n  Presione Enter para continuar...")

        # ---------------------------------------------------------
        # Opción 3: Peek siguiente cliente
        # ---------------------------------------------------------
        elif option == "3":
            print("\n  👀 VER SIGUIENTE CLIENTE (SIN LLAMARLO)")
            print("  " + "-" * 56)
            service_type = select_service_type("Seleccione el servicio a consultar:")

            try:
                ticket = queue_system.peek_next(service_type)
                print(f"\n  🎯 Siguiente en la cola de '{service_type}':")
                print(f"     Ticket N° {ticket.number:04d}")
                print(f"     Cliente: {ticket.client_name}")
                print(f"     Hora de emisión: {ticket.issued_at.strftime('%H:%M:%S')}")
            except IndexError as e:
                print(f"\n  ℹ️  {e}")
            except ValueError as e:
                print(f"\n  ❌ Error: {e}")

            input("\n  Presione Enter para continuar...")

        # ---------------------------------------------------------
        # Opción 4: Ver lista de espera completa
        # ---------------------------------------------------------
        elif option == "4":
            print("\n  📋 LISTA DE ESPERA COMPLETA")
            print("  " + "-" * 56)
            waiting = queue_system.list_waiting()
            has_waiting = False

            for service in SERVICE_TYPES:
                tickets = waiting[service]
                print(f"\n  ─── {service.upper()} ───")
                if not tickets:
                    print("     (Sin clientes en espera)")
                else:
                    has_waiting = True
                    for ticket in tickets:
                        print(f"     N° {ticket.number:04d} | {ticket.client_name} "
                              f"| {ticket.issued_at.strftime('%H:%M:%S')}")

            if not has_waiting:
                print("\n  💤 No hay clientes esperando en ningún servicio.")

            input("\n  Presione Enter para continuar...")

        # ---------------------------------------------------------
        # Opción 5: Ver estadísticas
        # ---------------------------------------------------------
        elif option == "5":
            print("\n  📊 ESTADÍSTICAS DE LA COLA")
            print("  " + "-" * 56)
            stats_data = queue_system.stats()
            for service in SERVICE_TYPES:
                count = stats_data[service]
                bar = "█" * count if count > 0 else "—"
                print(f"     {service:20s}: {count:3d} clientes {bar}")
            print("  " + "-" * 56)
            print(f"     {'TOTAL':20s}: {stats_data['total']:3d} clientes")
            print("  " + "-" * 56)

            input("\n  Presione Enter para continuar...")

        # ---------------------------------------------------------
        # Opción 6: Salir
        # ---------------------------------------------------------
        elif option == "6":
            print("\n  👋 ¡Gracias por usar Branch Queue! Hasta luego.\n")
            break

        # ---------------------------------------------------------
        # Opción inválida
        # ---------------------------------------------------------
        else:
            print(f"\n  ⚠️  Opción inválida. Seleccione una opción del 1 al 6.")
            input("\n  Presione Enter para continuar...")


# =============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    """
    Punto de entrada del programa. Ejecuta la interfaz CLI interactiva.
    """
    print("\n" + "=" * 60)
    print("  🏦  BRANCH QUEUE — Gestor de Cola por Servicio")
    print("  Banco Meridional — Sistema de Gestión de Turnos")
    print("=" * 60)
    print("\n  🚀 Inicializando sistema...")
    print("  ✅ Sistema listo. Bienvenido.\n")

    try:
        run_cli()
    except KeyboardInterrupt:
        print("\n\n  👋 Interrupción recibida. ¡Hasta luego!\n")
        sys.exit(0)