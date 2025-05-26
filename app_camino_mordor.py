###############################################################################
#  CAMINO A MORDOR  –  APP STREAMLIT 100% en español
###############################################################################
import streamlit as st
import numpy as np
import copy
import io
import base64
from pathlib import Path

import mesa
import random


# =========== (1) IMAGEN DE FONDO =============
# Asegúrate que el archivo se llama igual (20061512.jpg)
def set_background(image_path):
    with open(image_path, "rb") as img_file:
        img_bytes = img_file.read()
    img_b64 = base64.b64encode(img_bytes).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{img_b64}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


set_background("papu.avif")  # Cambia si tu imagen tiene otro nombre

# =========== (2) TÍTULO ======================
st.markdown(
    """
    <div style='background-color: white; padding: 18px; border-radius: 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.07);'>
        <h2 style='color: #333;'>🗺️ Camino a Mordor – Simulador de la Comunidad del Anillo</h2>
        
    </div>
    """,
    unsafe_allow_html=True,
)


# =========== (3) PARÁMETROS EN SIDEBAR =======
with st.sidebar:
    st.header("⚙️ Parámetros de la aventura")
    pasos = st.number_input("Número de pasos", 1, 200, 15)
    st.subheader("Tamaño del mapa")
    width = st.number_input("Ancho del mapa", 6, 30, 12)
    height = st.number_input("Alto del mapa", 6, 30, 12)

    st.subheader("Enemigos (número de grupos y cantidad por grupo)")
    cols = st.columns(2)
    n_grp_isengard = cols[0].number_input(
        "Grupos Orco de Isengard", 0, 10, 2, key="n_grp_isengard"
    )
    per_grp_isengard = cols[1].number_input(
        "Cantidad por grupo", 0, 20, 2, key="per_grp_isengard"
    )

    cols2 = st.columns(2)
    n_grp_mordor = cols2[0].number_input(
        "Grupos Orco de Mordor", 0, 10, 3, key="n_grp_mordor"
    )
    per_grp_mordor = cols2[1].number_input(
        "Cantidad por grupo", 0, 20, 2, key="per_grp_mordor"
    )

    cols3 = st.columns(2)
    n_grp_trasgo = cols3[0].number_input(
        "Grupos de Trasgos", 0, 10, 2, key="n_grp_trasgo"
    )
    per_grp_trasgo = cols3[1].number_input(
        "Cantidad por grupo", 0, 20, 2, key="per_grp_trasgo"
    )

    cols4 = st.columns(2)
    n_grp_troll = cols4[0].number_input("Grupos de Trolls", 0, 5, 1, key="n_grp_troll")
    per_grp_troll = cols4[1].number_input(
        "Cantidad por grupo", 0, 10, 2, key="per_grp_troll"
    )

    nazguls = st.number_input("Cantidad de Nazgûl", 0, 9, 2)

    st.subheader("Dificultad (afecta la fuerza del Rey Brujo)")
    dificultad = st.selectbox("Nivel de dificultad", ["Fácil", "Media", "Difícil"])
    fuerza_rb = {"Fácil": 2, "Media": 5, "Difícil": 10}[dificultad]

    if st.button("🧭 Iniciar aventura"):
        st.session_state.start = True
        st.session_state.simul_done = False

# =========== (4) MODELO DE MORDOR ==============
# (Tu modelo completo y funciones van aquí)
# ----------- Pega aquí TODO tu código de clases --------------
# (OJO: todo el bloque de agentes, modelo, funciones de plot)
# -----------------------------------------------------------------
## scheluder


class CustomScheduler:
    def __init__(self, model):
        self.model = model
        self.agents = []
        self.steps = 0

    def add(self, agent):
        self.agents.append(agent)

    def remove(self, agent):
        if agent in self.agents:
            self.agents.remove(agent)

    def shuffle_do(self, method_name):
        agent_list = list(self.agents)
        random.shuffle(agent_list)
        for agent in agent_list:
            if agent in self.agents:
                getattr(agent, method_name)()

    def step(self):
        self.shuffle_do("step")
        self.steps += 1

    def step_by_type(self, agent_type):
        # """Ejecuta el paso solo para agentes de un tipo específico"""
        agents_of_type = [a for a in self.agents if isinstance(a, agent_type)]
        random.shuffle(agents_of_type)
        for agent in agents_of_type:
            if agent in self.agents:
                agent.step()


## agente comunidad

## primero creamos el agente padre para mis personajes principales"""


class AgenteComunidad(mesa.Agent):
    def __init__(self, model, nombre, fuerza, defensa, vida, energia):
        super().__init__(model)
        self.nombre = nombre
        self.fuerza = fuerza
        self.defensa_base = defensa
        self.defensa_actual = defensa
        self.vida = vida
        self.vida_maxima = vida
        self.energia = energia
        self.pos = None
        self.historial_posiciones = []
        self.activo = True
        self.turnos_veneno = 0
        self.recien_revivido = False

    def step(self):
        if not self.activo or getattr(self, "recien_revivido", False):
            if getattr(self, "recien_revivido", False):
                self.recien_revivido = False
            return

        if self.turnos_veneno > 0 and self.vida > 0:
            self.vida -= 1
            self.vida = max(0, self.vida)
            self.turnos_veneno -= 1
            self.model.log(
                f"{self.nombre} sufre por el veneno del orco. Vida restante {self.vida}. {self.turnos_veneno} turnos restantes."
            )
            if self.vida == 0:
                self.morir()
                return

        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        enemigos_vivos = [a for a in cellmates if isinstance(a, Enemigo) and a.vida > 0]
        frodo = next(
            (a for a in self.model.schedule.agents if isinstance(a, Frodo)), None
        )
        frodo_muerto = frodo is not None and frodo.vida <= 0

        if enemigos_vivos or frodo_muerto:
            ejecutar_ataque = True
            if hasattr(self, "usar_habilidad"):
                ejecutar_ataque = self.usar_habilidad()
            if ejecutar_ataque and enemigos_vivos:
                self.atacar(enemigos_vivos[0])
        else:
            if isinstance(self, Gimli) and getattr(self, "endurecido", False):
                self.defensa_actual = self.defensa_base
                self.endurecido = False
                self.model.log(
                    f"{self.nombre} relaja su cuerpo y vuelve a su defensa normal de {self.defensa_actual}."
                )
            if hasattr(self, "invisible") and self.invisible:
                self.invisible = False
                self.model.log(
                    f"{self.nombre} deja de ser invisible, el efecto del Anillo ha terminado."
                )

        self.regenerar_defensa()

    def moverse(self):
        posibles_pasos = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        pasos_validos = [
            p for p in posibles_pasos if p not in self.historial_posiciones
        ]
        nuevo_pos = self.random.choice(
            pasos_validos if pasos_validos else posibles_pasos
        )
        self.model.grid.move_agent(self, nuevo_pos)
        self.pos = nuevo_pos
        self.historial_posiciones.append(nuevo_pos)
        zona = self.model.obtener_zona(nuevo_pos)
        self.model.log(f"{self.nombre} se movió a {nuevo_pos} en la zona {zona}")

    def calcular_daño(self, enemigo):
        return max(0, self.fuerza - enemigo.defensa_actual)

    def atacar(self, enemigo):
        if not enemigo.activo or enemigo.vida <= 0:
            return
        self.model.log(f"{self.nombre} intenta atacar a {enemigo.nombre}...")
        daño = self.calcular_daño(enemigo)
        enemigo.recibir_daño(daño, self)

    def recibir_daño(self, daño, atacante):
        if self.defensa_actual > 0:
            daño_bloqueado = min(daño, self.defensa_actual)
            self.defensa_actual -= daño_bloqueado
            daño -= daño_bloqueado
            self.model.log(
                f"{self.nombre} bloqueó {daño_bloqueado} a {atacante.nombre} con su defensa. Defensa restante: {self.defensa_actual}"
            )
        if daño > 0:
            self.vida -= daño
            self.vida = max(0, self.vida)
            self.model.log(
                f"{self.nombre} recibió {daño} de daño de {atacante.nombre}. Vida restante: {self.vida}"
            )
        if self.vida == 0:
            self.morir()

    def morir(self):
        self.activo = False
        self.model.log(f"{self.nombre} ha caído en la batalla.")
        self.model.grid.remove_agent(self)
        self.model.schedule.remove(self)

    def regenerar_defensa(self):
        if self.defensa_actual < self.defensa_base:
            self.defensa_actual += 1
            self.model.log(
                f"{self.nombre} regenera 1 punto de defensa. Defensa actual: {self.defensa_actual}"
            )


class Frodo(AgenteComunidad):
    def __init__(self, model):
        super().__init__(model, "Frodo", fuerza=2, defensa=1, vida=10, energia=25)
        self.invisible = False
        self.vida_maxima = 10

    def usar_habilidad(self):
        if not self.invisible and self.vida > 0 and self.model.random.random() < 0.3:
            self.invisible = True
            self.model.log(
                f"{self.nombre} usa el Anillo Único y se vuelve invisible... pero los Nazgûl sienten su presencia."
            )
            for agent in self.model.schedule.agents:
                if isinstance(agent, Nazgul):
                    agent.objetivo_frodo = self.pos
        return True

    def morir(self):
        if self.vida == 0 and self.activo:
            self.model.log(f"{self.nombre} ha caído… pero quizá no sea el fin.")
            self.activo = False

    def revivir(self, vida_restaurada=5):
        if not self.activo and self.vida <= 0:
            self.vida = vida_restaurada
            self.activo = True
            self.recien_revivido = True
            self.model.log(
                f"¡{self.nombre} ha sido revivido gracias al sacrificio de Sam! Vida restaurada: {self.vida}"
            )


class Sam(AgenteComunidad):
    def __init__(self, model):
        super().__init__(model, "Sam", fuerza=3, defensa=1, vida=12, energia=20)
        self.vida_maxima = 12

    def usar_habilidad(self):
        frodo = next(
            (a for a in self.model.schedule.agents if isinstance(a, Frodo)), None
        )
        if frodo and frodo.vida <= 0 and frodo.pos == self.pos and self.vida > 0:
            self.model.log(
                f"{self.nombre} se sacrifica por Frodo, devolviéndole la vida."
            )
            frodo.revivir(vida_restaurada=10)
            self.morir()
            return False
        return True


class Aragorn(AgenteComunidad):
    def __init__(self, model):
        super().__init__(
            model, nombre="Aragorn", fuerza=5, defensa=4, vida=30, energia=25
        )
        self.capitan = True
        self.vida_maxima = 30
        self.grito_activado = False
        self.ultimo_suspiro_activado = False

    def usar_habilidad(self):
        if not self.grito_activado and self.model.random.random() < 0.4:
            self.grito_activado = True
            self.model.log(
                f"{self.nombre} lanza un grito de guerra que inspira a la Comunidad. ¡+2 fuerza para todos!"
            )
            for agente in self.model.schedule.agents:
                if isinstance(agente, AgenteComunidad):
                    agente.fuerza += 2

        if not self.ultimo_suspiro_activado and self.vida <= self.vida_maxima * 0.1:
            self.ultimo_suspiro_activado = True
            self.fuerza += 5
            self.model.log(
                f"{self.nombre}, al borde de la muerte, reúne su última fuerza: ¡+5 de fuerza!"
            )
        return True

    def morir(self):
        self.model.log(f"{self.nombre} ha caído... la Comunidad pierde a su Capitán.")
        for agente in self.model.schedule.agents:
            if isinstance(agente, AgenteComunidad) and agente != self:
                agente.fuerza = max(0, agente.fuerza - 1)
                self.model.log(
                    f"{agente.nombre} pierde 1 punto de fuerza por la pérdida de {self.nombre}."
                )
        self.model.grid.remove_agent(self)
        self.model.schedule.remove(self)


class Gandalf(AgenteComunidad):
    def __init__(self, model):
        super().__init__(
            model, nombre="Gandalf", fuerza=4, defensa=3, vida=25, energia=30
        )
        self.vida_maxima = 25

    def usar_habilidad(self):
        if self.model.random.random() < 0.3:
            self.model.log(
                f"{self.nombre} extiende su báculo y sana a la Comunidad (+2 de vida para todos)."
            )
            for agente in self.model.schedule.agents:
                if isinstance(agente, AgenteComunidad):
                    agente.vida = min(agente.vida + 2, agente.vida_maxima)
                    self.model.log(
                        f"  {agente.nombre} recupera 2 de vida. Vida actual: {agente.vida}"
                    )
        frodo = next(
            (a for a in self.model.schedule.agents if isinstance(a, Frodo)), None
        )
        if frodo and self.model.random.random() < 0.4:
            frodo.defensa_actual = frodo.defensa_base
            self.model.log(
                f"{self.nombre} protege a Frodo con un escudo mágico. Defensa restaurada a {frodo.defensa_actual}."
            )
        enemigos_vivos = [
            a
            for a in self.model.schedule.agents
            if isinstance(a, Enemigo) and not isinstance(a, ReyBrujo)
        ]
        if enemigos_vivos and self.model.random.random() < 0.05:
            objetivo = self.random.choice(enemigos_vivos)
            self.model.log(
                f"{self.nombre} invoca un rayo y elimina a {objetivo.nombre} instantáneamente."
            )
            objetivo.morir()
        return True


class Legolas(AgenteComunidad):
    def __init__(self, model):
        super().__init__(
            model, nombre="Legolas", fuerza=3, defensa=2, vida=20, energia=30
        )
        self.arquero = True
        self.agilidad = 2
        self.evasion_elfica_activada = False

    def usar_habilidad(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        enemigos = [a for a in cellmates if isinstance(a, Enemigo)]
        if enemigos and self.model.random.random() < 0.3:
            objetivo = self.random.choice(enemigos)
            self.model.log(
                f"{self.nombre} realiza un disparo doble contra {objetivo.nombre}!"
            )
            for _ in range(2):
                daño = max(self.fuerza - objetivo.defensa_actual, 0)
                objetivo.recibir_daño(daño, self)
        return True

    def recibir_daño(self, daño, atacante):
        if not self.evasion_elfica_activada and self.model.random.random() < 0.1:
            self.model.log(
                f"{self.nombre} esquiva ágilmente el ataque de {atacante.nombre}. ¡No recibe daño!"
            )
            self.evasion_elfica_activada = True
            return
        self.evasion_elfica_activada = False
        super().recibir_daño(daño, atacante)


class Gimli(AgenteComunidad):
    def __init__(self, model):
        super().__init__(
            model, nombre="Gimli", fuerza=4, defensa=5, vida=25, energia=20
        )
        self.provocar_activado = False
        self.endurecido = False
        self.defensa_base = self.defensa_actual

    def usar_habilidad(self):
        if not self.provocar_activado and self.model.random.random() < 0.2:
            self.provocar_activado = True
            self.model.log(
                f"{self.nombre} provoca a los enemigos, atrayendo su atención."
            )
        if self.provocar_activado and not self.endurecido:
            self.model.log(f"{self.nombre} endurece su cuerpo, ganando +15 de defensa.")
            self.defensa_actual += 15
            self.endurecido = True
            self.provocar_activado = False
        return True


class Boromir(AgenteComunidad):
    def __init__(self, model):
        super().__init__(
            model, nombre="Boromir", fuerza=4, defensa=3, vida=25, energia=20
        )
        self.ha_sacrificado = False

    def usar_habilidad(self):
        if self.ha_sacrificado or self.vida <= 0:
            return
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        minijefes = [
            a
            for a in cellmates
            if isinstance(a, Enemigo)
            and getattr(a, "es_minijefe", False)
            and a.vida <= 10
        ]
        if minijefes:
            minijefe = minijefes[0]
            self.model.log(
                f"{self.nombre} se sacrifica heroicamente para eliminar a {minijefe.nombre} y proteger a la Comunidad."
            )
            minijefe.morir()
            self.ha_sacrificado = True
            self.morir()
            return False
        return True


### agente enemigo

## Segundo creacion de mi superclase Enemigo


class Enemigo(mesa.Agent):
    def __init__(self, model, nombre, fuerza, defensa, vida):
        super().__init__(model)
        self.nombre = nombre
        self.fuerza = fuerza
        self.defensa_base = defensa
        self.defensa_actual = defensa
        self.vida = vida
        self.pos = None
        self.historial_posiciones = []
        self.activo = True

    def patrullar(self):
        posibles_pasos = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        nuevo_pos = self.random.choice(posibles_pasos)
        self.model.grid.move_agent(self, nuevo_pos)
        self.pos = nuevo_pos
        self.historial_posiciones.append(nuevo_pos)
        self.model.log(f"{self.nombre} patrulla su territorio y se mueve a {nuevo_pos}")

    def calcular_daño(self, objetivo):
        return max(0, self.fuerza - objetivo.defensa_actual)

    def atacar(self, objetivos):
        if not isinstance(objetivos, list):
            objetivos = [objetivos]
        provocadores = [a for a in objetivos if getattr(a, "provocar_activado", False)]
        if provocadores:
            objetivo = self.random.choice(provocadores)
            self.model.log(
                f"{self.nombre} cae en la provocación de {objetivo.nombre} y lo ataca directamente."
            )
        else:
            objetivo = self.random.choice(objetivos)
            self.model.log(f"{self.nombre} intenta atacar a {objetivo.nombre}.")

        # Caso especial: Frodo invisible
        if isinstance(objetivo, Frodo) and getattr(objetivo, "invisible", False):
            if not isinstance(self, Nazgul):
                self.model.log(
                    f"{self.nombre} no puede ver a {objetivo.nombre}, está invisible."
                )
                return

        daño = max(self.fuerza - objetivo.defensa_actual, 0)
        objetivo.recibir_daño(daño, self)

    def recibir_daño(self, daño, atacante):
        if not self.activo or self.vida <= 0:
            return
        if self.defensa_actual > 0:
            daño_bloqueado = min(daño, self.defensa_actual)
            self.defensa_actual -= daño_bloqueado
            daño -= daño_bloqueado
            self.model.log(
                f"{self.nombre} bloqueó {daño_bloqueado} a {atacante.nombre} con su defensa. Defensa restante: {self.defensa_actual}"
            )
        if daño > 0:
            self.vida -= daño
            self.vida = max(0, self.vida)
            self.model.log(
                f"{self.nombre} recibió {daño} de daño de {atacante.nombre}. Vida restante: {self.vida}"
            )
        if self.vida == 0:
            self.morir()

    def morir(self):
        self.activo = False
        self.model.log(f"{self.nombre} ha sido derrotado.")
        if self.pos is not None:
            self.model.grid.remove_agent(self)
        self.model.schedule.remove(self)
        self.pos = None


class Trasgo(Enemigo):
    def __init__(self, model, numero):
        super().__init__(model, nombre=f"Trasgo {numero}", fuerza=1, defensa=0, vida=5)
        self.fuerza_base = 1

    def step(self):
        vecinos = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        trasgos_vecinos = [
            agent
            for pos in vecinos
            for agent in self.model.grid.get_cell_list_contents([pos])
            if isinstance(agent, Trasgo) and agent.vida > 0
        ]
        trasgos_en_celda = [
            agent
            for agent in self.model.grid.get_cell_list_contents([self.pos])
            if isinstance(agent, Trasgo) and agent.vida > 0
        ]
        grupo_trasgos = list(set(trasgos_vecinos + trasgos_en_celda))
        if len(grupo_trasgos) >= 2:
            for trasgo in grupo_trasgos:
                trasgo.fuerza = trasgo.fuerza_base + 1
            self.model.log("¡Los trasgos se agrupan y ganan coraje (+1 fuerza)!")
        else:
            self.fuerza = self.fuerza_base

        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        comunidad = [
            a for a in cellmates if isinstance(a, AgenteComunidad) and a.vida > 0
        ]
        if comunidad:
            objetivo = self.random.choice(comunidad)
            self.atacar(objetivo)
        else:
            self.patrullar()
        self.fuerza = self.fuerza_base


class Troll(Enemigo):
    def __init__(self, model, numero):
        super().__init__(model, nombre=f"Troll {numero}", fuerza=7, defensa=2, vida=20)

    def step(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        comunidad = [
            agent
            for agent in cellmates
            if isinstance(agent, AgenteComunidad) and agent.vida > 0
        ]
        if comunidad and self.model.random.random() < 0.2:
            self.model.log(
                f"¡{self.nombre} arranca un árbol y golpea a toda la Comunidad! Todos reciben 3 de daño."
            )
            for agente in comunidad:
                agente.recibir_daño(3, self)
            return
        if comunidad:
            objetivo = self.random.choice(comunidad)
            self.atacar(objetivo)
        else:
            self.patrullar()

    def morir(self):
        if self.pos is not None:
            cellmates = self.model.grid.get_cell_list_contents([self.pos])
            comunidad_en_celda = [
                a for a in cellmates if isinstance(a, AgenteComunidad) and a.vida > 0
            ]
            if self.model.random.random() < 0.5 and comunidad_en_celda:
                self.model.log(
                    f"{self.nombre} cae aplastando a la Comunidad, que no logra esquivar y recibe 2 de daño."
                )
                for agente in comunidad_en_celda:
                    agente.recibir_daño(2, self)
            else:
                self.model.log(
                    f"¡{self.nombre} cae pesadamente, pero la Comunidad logra esquivar el peligro!"
                )
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            self.pos = None
        else:
            if self in self.model.schedule.agents:
                self.model.schedule.remove(self)


class OrcoIsengard(Enemigo):
    def __init__(self, model, numero):
        super().__init__(
            model, nombre=f"Orco de Isengard {numero}", fuerza=3, defensa=2, vida=15
        )
        self.refuerzos_llamados = False

    def step(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        agentes_vivos = [
            agent
            for agent in cellmates
            if isinstance(agent, AgenteComunidad) and agent.vida > 0
        ]
        if agentes_vivos:
            if not self.refuerzos_llamados and self.random.random() < 0.15:
                self.llamar_refuerzos()
                self.refuerzos_llamados = True
            for objetivo in agentes_vivos:
                super().atacar(objetivo)
        else:
            self.patrullar()
            self.refuerzos_llamados = False

    def llamar_refuerzos(self):
        self.model.log(
            f"¡{self.nombre} grita por ayuda y aparecen 3 trasgos como refuerzo!"
        )
        for _ in range(3):
            nuevo_trasgo = Trasgo(self.model, self.model.siguiente_id())
            numero_refuerzo = self.model.contador_trasgos_refuerzo
            nuevo_trasgo.nombre = f"Trasgo (Refuerzo {numero_refuerzo})"
            self.model.grid.place_agent(nuevo_trasgo, self.pos)
            self.model.schedule.add(nuevo_trasgo)
            self.model.log(
                f"  Un Trasgo llega como refuerzo a la posición {self.pos} ({self.model.obtener_zona(self.pos)})"
            )
            self.model.contador_trasgos_refuerzo += 1


class OrcoMordor(Enemigo):
    def __init__(self, model, numero):
        super().__init__(
            model, nombre=f"Orco de Mordor {numero}", fuerza=4, defensa=2, vida=20
        )
        self.activo = True

    def step(self):
        if not self.activo or self.vida <= 0:
            return
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        agentes_vivos = [
            agent
            for agent in cellmates
            if isinstance(agent, AgenteComunidad) and agent.vida > 0
        ]
        if agentes_vivos:
            objetivo = self.random.choice(agentes_vivos)
            self.atacar(objetivo)
        else:
            self.patrullar()

    def atacar(self, objetivo):
        super().atacar(objetivo)
        if getattr(objetivo, "activo", True) and getattr(objetivo, "vida", 1) > 0:
            if (
                self.model.random.random() < 0.1
                and getattr(objetivo, "turnos_veneno", 0) == 0
            ):
                objetivo.turnos_veneno = 3
                self.model.log(
                    f"¡{objetivo.nombre} es herido por un arma envenenada de orco y empieza a sentirse débil!"
                )

    def morir(self):
        self.activo = False
        if self.pos is not None:
            cellmates = self.model.grid.get_cell_list_contents([self.pos])
            comunidad_viva = [
                a for a in cellmates if isinstance(a, AgenteComunidad) and a.vida > 0
            ]
            if comunidad_viva:
                victima = self.random.choice(comunidad_viva)
                victima.vida -= 1
                victima.vida = max(0, victima.vida)
                self.model.log(
                    f"¡{self.nombre}, en un último acto de furia, hiere a {victima.nombre} antes de caer! {victima.nombre} pierde 1 de vida (ignora defensa). Vida restante: {victima.vida}"
                )
                if victima.vida == 0:
                    victima.morir()
            else:
                self.model.log(
                    f"{self.nombre} cae sin nadie a quien herir con su último aliento."
                )
            self.model.grid.remove_agent(self)
            self.pos = None
        self.model.schedule.remove(self)


class Nazgul(Enemigo):
    def __init__(self, model, numero):
        super().__init__(
            model, nombre=f"Nazgûl {numero}", fuerza=10, defensa=1, vida=20
        )

    def step(self):
        frodo = next(
            (a for a in self.model.schedule.agents if isinstance(a, Frodo)), None
        )
        if frodo and getattr(frodo, "invisible", False):
            nuevo_pos = frodo.pos
        else:
            posibles_pasos = self.model.grid.get_neighborhood(
                self.pos, moore=True, include_center=False
            )
            nuevo_pos = self.random.choice(posibles_pasos)
        self.model.grid.move_agent(self, nuevo_pos)
        self.pos = nuevo_pos
        self.model.log(
            f"{self.nombre} se mueve {'siguiendo el Anillo' if frodo and getattr(frodo, 'invisible', False) else 'libremente'} a {nuevo_pos}"
        )
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        agentes_vivos = [
            agent
            for agent in cellmates
            if isinstance(agent, AgenteComunidad) and agent.vida > 0
        ]
        if agentes_vivos:
            objetivo = self.random.choice(agentes_vivos)
            self.atacar(objetivo)


class ReyBrujo(Enemigo):
    def __init__(self, model):
        super().__init__(
            model, nombre="Rey Brujo de Angmar", fuerza=8, defensa=5, vida=100
        )
        self.refuerzos_llamados = False
        self.vida_max = 100

    def step(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        agentes_vivos = [
            agent
            for agent in cellmates
            if isinstance(agent, AgenteComunidad) and agent.vida > 0
        ]
        if agentes_vivos:
            if not self.refuerzos_llamados and self.vida < self.vida_max * 0.5:
                self.llamar_refuerzos()
            for objetivo in agentes_vivos:
                self.atacar(objetivo)
        else:
            self.model.log(
                f"{self.nombre} custodia el Monte del Destino, esperando a la Comunidad..."
            )

    def llamar_refuerzos(self):
        self.model.log(f"¡{self.nombre} grita por ayuda y aparece su guardia personal!")
        for _ in range(1):
            nuevo_orco_I = OrcoIsengard(self.model, self.model.siguiente_id())
            nuevo_orco_I.nombre = "Orco de Isengard Elite"
            nuevo_orco_m = OrcoMordor(self.model, self.model.siguiente_id())
            nuevo_orco_m.nombre = "Orco de Mordor Elite"
            self.model.grid.place_agent(nuevo_orco_I, self.pos)
            self.model.grid.place_agent(nuevo_orco_m, self.pos)
            self.model.schedule.add(nuevo_orco_I)
            self.model.schedule.add(nuevo_orco_m)
            self.model.log(
                f"  Un orco de mordor y un orco de Isengard llega como refuerzo a la posición {self.pos} ({self.model.obtener_zona(self.pos)})"
            )
        self.refuerzos_llamados = True


class Lurtz(Enemigo):
    def __init__(self, model):
        super().__init__(
            model, nombre="Lurtz, Capitán Uruk-hai", fuerza=15, defensa=4, vida=60
        )
        self.es_minijefe = True
        self.vida_maxima = 60

    def step(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        agentes_vivos = [
            agent
            for agent in cellmates
            if isinstance(agent, AgenteComunidad) and agent.vida > 0
        ]
        if agentes_vivos:
            objetivo = self.random.choice(agentes_vivos)
            self.atacar(objetivo)


### modelo


class CaminoAMordor(mesa.Model):
    def __init__(self, width=12, height=12):
        super().__init__()
        self.width = width
        self.height = height
        self.grid = mesa.space.MultiGrid(width, height, torus=False)
        self.schedule = CustomScheduler(self)
        self.lurtz_aparecio = False
        self.ultimo_id = 0
        self.contador_trasgos_refuerzo = 1
        self.logs = []
        self.historial_estadisticas = []

        # Zonas completamente cubiertas
        self.zonas = {
            "Rivendel": [(x, y) for x in range(0, 4) for y in range(0, 6)],
            "Moria": [(x, y) for x in range(4, 8) for y in range(0, 6)],
            "Rohan": [(x, y) for x in range(8, 12) for y in range(0, 6)],
            "Gondor": [(x, y) for x in range(0, 4) for y in range(6, 12)],
            "Mordor": [(x, y) for x in range(4, 8) for y in range(6, 12)],
            "Monte del Destino": [(x, y) for x in range(8, 12) for y in range(6, 12)],
        }

        # Después de definir self.zonas …
        self.destino_comunidad = self.zonas["Monte del Destino"][0]  # e.g. (8, 6)

        # Crear agentes y enemigos distribuidos en las zonas
        self.create_agents()
        self.create_trasgos(2, 2)
        self.create_trolls(1, 2)
        self.create_orcos_isengard(2, 2)
        self.create_orcos_mordor(3, 2)
        self.create_nazgul(2)
        self.create_rey_brujo()

    def log(self, msg):
        print(msg)  # Lo imprime en consola
        self.logs.append(msg)  # Lo guarda para mostrarlo luego

    def limpiar_logs(self):
        self.logs = []

    def colocar_agente_en_zona(self, agente, zona_nombre):
        posiciones = self.zonas.get(zona_nombre, [])
        if posiciones:
            pos = self.random.choice(posiciones)
            self.grid.place_agent(agente, pos)
            agente.pos = pos
            self.schedule.add(agente)
            print(
                f"Se creó {agente.nombre} en la posición {agente.pos} de la zona {zona_nombre}"
            )
        else:
            print(f"No hay posiciones definidas para la zona {zona_nombre}")

    def colocar_grupo_en_zona(self, agentes, *zonas_nombres):
        posiciones_disponibles = []
        for zona in zonas_nombres:
            posiciones_disponibles.extend(self.zonas.get(zona, []))

        if posiciones_disponibles:
            pos = self.random.choice(posiciones_disponibles)
            zonas_reales = [
                zona for zona in zonas_nombres if pos in self.zonas.get(zona, [])
            ]
            zonas_texto = (
                ", ".join(zonas_reales) if zonas_reales else "Zona desconocida"
            )

            for agente in agentes:
                self.grid.place_agent(agente, pos)
                agente.pos = pos
                self.schedule.add(agente)

            print(
                f"Se creó un grupo de {len(agentes)} {type(agentes[0]).__name__} en la posición {pos} en la zona de {zonas_texto}"
            )
        else:
            print(
                f"No hay posiciones definidas para las zonas {', '.join(zonas_nombres)}"
            )

    def crear_grupos_en_zona(
        self, cantidad_grupos, tamaño_grupo, clase_agente, *zonas_nombres
    ):
        for g in range(cantidad_grupos):
            agentes = [
                clase_agente(self, numero=(g * tamaño_grupo + i + 1))
                for i in range(tamaño_grupo)
            ]
            self.colocar_grupo_en_zona(agentes, *zonas_nombres)

    def obtener_zona(self, pos):
        for nombre_zona, posiciones in self.zonas.items():
            if pos in posiciones:
                return nombre_zona
        return "Zona desconocida"

    def mover_comunidad(self):
        comunidad = [
            agente
            for agente in self.schedule.agents
            if isinstance(agente, AgenteComunidad) and agente.vida > 0
        ]
        if not comunidad:
            return

        lider = comunidad[0]
        cellmates = self.grid.get_cell_list_contents([lider.pos])
        enemigos_vivos = [
            agent
            for agent in cellmates
            if isinstance(agent, Enemigo) and agent.vida > 0
        ]

        if enemigos_vivos:
            print("La comunidas esta en combate")
            return

        if not self.lurtz_aparecio and self.random.random() < 0.5:
            self.crear_lurtz_en_posicion(lider.pos)
            self.lurtz_aparecio = True

            print("¡Lurtz ha bloqueado el avance de la Comunidad!")
            return

        destino = self.destino_comunidad
        vecinos = self.grid.get_neighborhood(
            lider.pos, moore=True, include_center=False
        )

        # para cada vecino calculamos la distancia al destino
        mejor_vecino = min(
            vecinos, key=lambda pos: abs(pos[0] - destino[0]) + abs(pos[1] - destino[1])
        )

        for agente in comunidad:
            self.grid.move_agent(agente, mejor_vecino)
            agente.pos = mejor_vecino
            agente.historial_posiciones.append(mejor_vecino)
            zona = self.obtener_zona(mejor_vecino)

            print(
                f"{agente.nombre} se movió en grupo a {mejor_vecino} en la zona {zona}"
            )

    def create_agents(self):
        miembros = [
            Aragorn(self),
            Gandalf(self),
            Gimli(self),
            Legolas(self),
            Frodo(self),
            Boromir(self),
            Sam(self),
        ]
        self.colocar_grupo_en_zona(miembros, "Rivendel")

    def create_trasgos(self, cantidad_grupos, tamaño_grupo):
        self.crear_grupos_en_zona(cantidad_grupos, tamaño_grupo, Trasgo, "Moria")

    def create_trolls(self, cantidad_grupos, tamaño_grupo):
        self.crear_grupos_en_zona(
            cantidad_grupos, tamaño_grupo, Troll, "Moria", "Rivendel"
        )

    def create_orcos_isengard(self, cantidad_grupos, tamaño_grupo):
        self.crear_grupos_en_zona(
            cantidad_grupos, tamaño_grupo, OrcoIsengard, "Rohan", "Mordor"
        )

    def create_orcos_mordor(self, cantidad_grupos, tamaño_grupo):
        self.crear_grupos_en_zona(
            cantidad_grupos, tamaño_grupo, OrcoMordor, "Mordor", "Gondor"
        )

    def create_nazgul(self, cantidad):
        for i in range(cantidad):
            nazgul = Nazgul(self, numero=i + 1)
            x = self.random.randint(0, self.width - 1)
            y = self.random.randint(0, self.height - 1)
            self.grid.place_agent(nazgul, (x, y))
            nazgul.pos = (x, y)
            self.schedule.add(nazgul)
            print(
                f"Se creó {nazgul.nombre} en la posición {nazgul.pos} en zona {self.obtener_zona(nazgul.pos)}"
            )

    def create_rey_brujo(self):
        rey_brujo = ReyBrujo(self)
        pos = self.zonas["Monte del Destino"][0]
        self.grid.place_agent(rey_brujo, pos)
        rey_brujo.pos = pos
        self.schedule.add(rey_brujo)
        print(
            f"Se creó {rey_brujo.nombre} en la posición {rey_brujo.pos} defendiendo el Monte del Destino"
        )

    def crear_lurtz_en_posicion(self, pos):
        lurtz = Lurtz(self)
        self.grid.place_agent(lurtz, pos)
        lurtz.pos = pos
        self.lurtz_aparecio = True
        self.schedule.add(lurtz)
        print(
            f"⚠️ Lurtz ha aparecido de sorpresa en la posición {pos} para enfrentar al grupo."
        )

    def step(self):
        print("\n--- Nuevo paso de la simulación ---")
        self.mover_comunidad()

        # Permitir que enemigos y comunidad actúen normalmente
        for agent in self.schedule.agents:
            if isinstance(agent, (Enemigo, AgenteComunidad)):
                agent.step()

        self.schedule.steps += 1

        # ========== GUARDAR HISTORIAL DEL ESTADO DE TODOS LOS AGENTES ==========

        if not hasattr(self, "historial_estadisticas"):
            self.historial_estadisticas = []

        snapshot = []
        for agent in self.schedule.agents:
            snapshot.append(
                {
                    "nombre": agent.nombre,
                    "vida": getattr(agent, "vida", None),
                    "activo": getattr(agent, "activo", True),
                    "tipo": (
                        "Comunidad" if isinstance(agent, AgenteComunidad) else "Enemigo"
                    ),
                }
            )
        self.historial_estadisticas.append(snapshot)

    def siguiente_id(self):
        self.ultimo_id += 1
        return self.ultimo_id


# =========== (5) VISUALIZACIÓN GRID + LOGS ==============
# (Usa tu función plot_grid de antes, aquí la llamo plot_grid_pro)
def plot_grid_pro(model, step, show_logs=True):
    width, height = model.width, model.height
    logs = getattr(model, "logs", [])

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.set_facecolor("#f5f5f5")
    if hasattr(model, "obtener_zona"):
        for x in range(width):
            for y in range(height):
                zona = model.obtener_zona((x, y))
                colores = {
                    "Rivendel": "#B4D9FF",
                    "Moria": "#E1E1E1",
                    "Gondor": "#F3E7BA",
                    "Rohan": "#C0E9B4",
                    "Mordor": "#CBBCB0",
                    "Monte del Destino": "#FFCBCB",
                }
                if zona in colores:
                    ax.add_patch(
                        plt.Rectangle(
                            (x - 0.5, y - 0.5), 1, 1, color=colores[zona], alpha=0.16
                        )
                    )
    leyenda = []
    vistos = set()
    AGENTE_MARKERS = {
        "Aragorn": ("*", "blue"),
        "Gandalf": ("h", "gray"),
        "Gimli": ("v", "sienna"),
        "Legolas": ("^", "forestgreen"),
        "Frodo": ("o", "black"),
        "Sam": ("o", "olive"),
        "Boromir": ("p", "red"),
        "Nazgûl": ("D", "indigo"),
        "Rey Brujo": ("X", "crimson"),
        "Lurtz": ("P", "darkorange"),
        "Troll": ("s", "dimgray"),
        "Trasgo": ("x", "limegreen"),
        "Orco de Mordor Elite": ("1", "gold"),
        "Orco de Isengard Elite": ("2", "gold"),
        "Orco de Mordor": ("1", "black"),
        "Orco de Isengard": ("2", "maroon"),
    }
    for ag in model.schedule.agents:
        if getattr(ag, "pos", None) and ag.vida > 0:
            x, y = ag.pos
            mk, col = ("*", "gray")
            for key in AGENTE_MARKERS:
                if key in ag.nombre:
                    mk, col = AGENTE_MARKERS[key]
            s = (
                240
                if any(k in ag.nombre for k in ["Rey Brujo", "Frodo", "Lurtz"])
                else 160
            )
            ax.scatter(x, y, marker=mk, c=col, s=s, edgecolors="k", zorder=3)
            lbl = f"{ag.nombre} ({ag.vida})"
            if lbl not in vistos:
                leyenda.append(
                    plt.Line2D(
                        [],
                        [],
                        marker=mk,
                        color=col,
                        linestyle="",
                        markeredgecolor="k",
                        markersize=9,
                        label=lbl,
                    )
                )
                vistos.add(lbl)
    ax.set_title(f"Paso {step}", fontsize=14)
    ax.set_xlim(-0.5, width - 0.5)
    ax.set_ylim(-0.5, height - 0.5)
    ax.set_xticks(range(width))
    ax.set_yticks(range(height))
    ax.grid(ls=":", lw=0.5)
    ax.legend(
        handles=leyenda,
        fontsize=8,
        bbox_to_anchor=(1.05, 0.5),
        loc="center left",
        title="Agentes",
    )
    ax.set_aspect("equal")
    plt.tight_layout()
    return fig, logs


import matplotlib.pyplot as plt
import textwrap


def resumen_simulacion_v3(vidas_hist, comunidad_inicial, enemigos_inicial, max_steps):
    # Detecta comunidad y enemigos (dinámicos)
    nombres_comunidad = [
        n for n in vidas_hist if any(n0 in n for n0 in comunidad_inicial)
    ]
    nombres_enemigos = [n for n in vidas_hist if n not in nombres_comunidad]

    vivos_comunidad = [n for n in nombres_comunidad if vidas_hist[n][-1] > 0]
    vivos_enemigos = [n for n in nombres_enemigos if vidas_hist[n][-1] > 0]
    muertos_comunidad = [n for n in nombres_comunidad if vidas_hist[n][-1] <= 0]
    muertos_enemigos = [n for n in nombres_enemigos if vidas_hist[n][-1] <= 0]

    fig = plt.figure(figsize=(22, 11))
    fig.suptitle(
        "🛡️ Resumen de la Simulación - Camino a Mordor 🛡️", fontsize=26, weight="bold"
    )

    # --- 1. Evolución de Vida - Comunidad ---
    ax1 = plt.subplot2grid((3, 7), (0, 0), colspan=3)
    for n in nombres_comunidad:
        ax1.plot(range(1, len(vidas_hist[n]) + 1), vidas_hist[n], marker="o", label=n)
    ax1.set_title("Evolución de Vida - Comunidad", fontsize=15)
    ax1.set_xlabel("Paso", fontsize=12)
    ax1.set_ylabel("Vida", fontsize=12)
    ax1.legend(fontsize=9, loc="upper right", ncol=2)
    ax1.grid(True, alpha=0.3)

    # --- 2. Evolución de Vida - Enemigos Destacados ---
    enemigos_destacados = [
        n
        for n in vidas_hist
        if any(tag in n for tag in ["Lurtz", "Nazgûl", "Rey Brujo", "Gollum", "Elite"])
        or max(vidas_hist[n]) >= 40
    ]
    if len(enemigos_destacados) < 5:
        extras = [n for n in nombres_enemigos if n not in enemigos_destacados][
            : 5 - len(enemigos_destacados)
        ]
        enemigos_destacados += extras

    ax2 = plt.subplot2grid((3, 7), (0, 3), colspan=4)
    for nombre in enemigos_destacados:
        ax2.plot(
            range(1, len(vidas_hist[nombre]) + 1),
            vidas_hist[nombre],
            marker="s",
            label=nombre,
        )
    ax2.set_title("Evolución de Vida - Enemigos Destacados", fontsize=15)
    ax2.set_xlabel("Paso", fontsize=12)
    ax2.set_ylabel("Vida", fontsize=12)
    ax2.legend(fontsize=9, loc="upper right")
    ax2.grid(True, alpha=0.3)

    # --- 3. Barras de sobrevivientes finales ---
    ax3 = plt.subplot2grid((3, 7), (1, 3), colspan=4, rowspan=1)
    grupos = ["Comunidad", "Enemigos"]
    sobrevivientes = [len(vivos_comunidad), len(vivos_enemigos)]
    bars = ax3.barh(grupos, sobrevivientes, color=["royalblue", "crimson"], alpha=0.85)
    for bar in bars:
        w = bar.get_width()
        ax3.text(
            w + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{int(w)}",
            va="center",
            fontsize=18,
            weight="bold",
        )
    ax3.set_title("Sobrevivientes Finales", fontsize=14)
    ax3.set_xlim(0, max(sobrevivientes + [1]) + 4)

    # --- 4. Resumen textual en panel separado, bien organizado ---
    ax4 = plt.subplot2grid((3, 7), (1, 0), colspan=3, rowspan=2)
    max_bajas = 8  # máx nombres antes de cortar

    def format_bajas(lst, max_bajas=8):
        if not lst:
            return "Ninguna"
        mostrados = lst[:max_bajas]
        texto = "\n".join(f"- {n}" for n in mostrados)
        if len(lst) > max_bajas:
            texto += f"\n...y {len(lst)-max_bajas} más"
        return texto

    resumen = (
        "🧙‍♂️ **Resumen Final** 🧙‍♂️\n\n"
        f"Comunidad viva: {len(vivos_comunidad)}/{len(nombres_comunidad)}\n"
        f"Enemigos vivos: {len(vivos_enemigos)}/{len(nombres_enemigos)}\n\n"
        f"Duración total: {max_steps} pasos\n"
        f"Vida total Comunidad: {sum(vidas_hist[n][-1] for n in nombres_comunidad)}\n"
        f"Vida total Enemigos: {sum(vidas_hist[n][-1] for n in nombres_enemigos)}\n"
        "\n"
        "Bajas Comunidad:\n" + format_bajas(muertos_comunidad) + "\n\n"
        "Enemigos derrotados:\n" + format_bajas(muertos_enemigos)
    )
    ax4.axis("off")
    ax4.text(0, 1, resumen, fontsize=15, va="top", family="monospace")

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.show()


# =========== (6) LÓGICA DE SIMULACIÓN =============
if (
    "start" in st.session_state
    and st.session_state.start
    and not st.session_state.get("simul_done", False)
):
    st.markdown(
        f"""
    <div style='background-color: white; padding: 24px 28px; border-radius: 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.10); margin-bottom: 1.2rem;'>
        <h2 style='color:#1d3557; margin-top:0;'>🧙‍♂️ Parámetros elegidos</h2>
        <p style='font-size:1.13em; color:#222; margin-bottom:0.7em;'><b>Tamaño mapa:</b> {width} x {height}<br>
        <b>Pasos:</b> {pasos}<br>
        <b>Orcos Isengard:</b> {n_grp_isengard} grupos x {per_grp_isengard}<br>
        <b>Orcos Mordor:</b> {n_grp_mordor} grupos x {per_grp_mordor}<br>
        <b>Trasgos:</b> {n_grp_trasgo} grupos x {per_grp_trasgo}<br>
        <b>Trolls:</b> {n_grp_troll} grupos x {per_grp_troll}<br>
        <b>Nazgûl:</b> {nazguls}<br>
        <b>Fuerza Rey Brujo:</b> {fuerza_rb}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.info("¡Listo para iniciar! Haz clic en el slider para avanzar paso a paso.")
    # --- 1. Crear modelo y enemigos según input ---
    model = CaminoAMordor(width, height)
    model.create_orcos_isengard(n_grp_isengard, per_grp_isengard)
    model.create_orcos_mordor(n_grp_mordor, per_grp_mordor)
    model.create_trasgos(n_grp_trasgo, per_grp_trasgo)
    model.create_trolls(n_grp_troll, per_grp_troll)
    model.create_nazgul(nazguls)
    # Cambia fuerza RB
    for ag in model.schedule.agents:
        if "Rey Brujo" in ag.nombre:
            ag.fuerza = fuerza_rb
            model.rey_brujo = ag
            break
    else:
        model.rey_brujo = None

    # --- 2. Simula y guarda todos los estados ---
    estados = []
    vidas_hist = {}
    logs_por_paso = []
    for paso in range(pasos):
        model.step()
        estados.append(copy.deepcopy(model))
        logs_por_paso.append(list(model.logs))
        model.limpiar_logs()
    for idx, estado in enumerate(estados):
        for ag in estado.schedule.agents:
            vidas_hist.setdefault(ag.nombre, [0] * pasos)
            vidas_hist[ag.nombre][idx] = ag.vida
    comunidad_inicial = [
        n
        for n in vidas_hist
        if any(
            h in n
            for h in [
                "Aragorn",
                "Gandalf",
                "Gimli",
                "Legolas",
                "Frodo",
                "Sam",
                "Boromir",
            ]
        )
    ]
    st.session_state.estados = estados
    st.session_state.vidas_hist = vidas_hist
    st.session_state.comunidad_inicial = comunidad_inicial
    st.session_state.simul_done = True
    st.session_state.logs_por_paso = logs_por_paso

# =========== (7) VISUALIZACIÓN INTERACTIVA CON BOTONES ========
# =========== (7) VISUALIZACIÓN INTERACTIVA CON BOTONES ========

if st.session_state.get("simul_done", False):
    st.header("🪄 Simulación paso a paso")

    if "current_step" not in st.session_state:
        st.session_state.current_step = 0

    pasos = len(st.session_state.estados)
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    with col1:
        if st.button("⏪", use_container_width=True):
            st.session_state.current_step = 0
    with col2:
        if st.button("⏮️", use_container_width=True):
            st.session_state.current_step = max(0, st.session_state.current_step - 1)
    with col3:
        if st.button("▶️", use_container_width=True):
            st.session_state.current_step = min(
                pasos - 1, st.session_state.current_step + 1
            )
    with col4:
        if st.button("⏭️", use_container_width=True):
            st.session_state.current_step = pasos - 1
    with col5:
        if st.button("🔄 Reiniciar", use_container_width=True):
            st.session_state.current_step = 0

    paso_idx = st.session_state.current_step
    estado = st.session_state.estados[paso_idx]
    fig, logs = plot_grid_pro(estado, paso_idx + 1)
    st.pyplot(fig)

    logs = st.session_state.logs_por_paso[paso_idx]
    keywords = [
        "ataca",
        "recibió",
        "derrotad",
        "caíd",
        "rayo",
        "sacrifica",
        "grita",
        "veneno",
        "habilidad",
        "provoca",
        "invisible",
        "sana",
        "protege",
        "aplasta",
        "elimina",
        "esquiva",
        "grito de guerra",
        "escudo",
        "golpea",
        "defensa",
        "disparo",
    ]
    relevantes = [l for l in logs if any(k in l.lower() for k in keywords)]
    st.text_area(
        f"📜 Logs de combate – Paso {paso_idx+1}/{pasos}",
        "\n".join(relevantes) if relevantes else "(Sin eventos en este paso)",
        height=210,
    )

    # Resumen PRO
    # Resumen PRO y música/resultado final
    if paso_idx == pasos - 1:
        if st.button("📊 Mostrar gráficos y resultado final"):
            vidas_hist = st.session_state.vidas_hist
            comunidad_inicial = st.session_state.comunidad_inicial
            enemigos_inicial = [n for n in vidas_hist if n not in comunidad_inicial]
            max_steps = pasos
            resumen_simulacion_v3(
                vidas_hist, comunidad_inicial, enemigos_inicial, max_steps
            )
            st.pyplot(plt.gcf())  # Muestra el resumen PRO como gráfico

            # MENSAJE Y MÚSICA FINAL
            rey_brujo_vencido = any(
                "Rey Brujo" in n and vidas_hist[n][-1] <= 0 for n in vidas_hist
            )
            if rey_brujo_vencido:
                st.success(
                    "🎉 ¡LA COMUNIDAD HA TRIUNFADO! ¡SE LOGRÓ LA AVENTURA, TRIUNFÓ EL BIEN! 🎶"
                )
                st.audio("goku.mp3")
                st.balloons()
            else:
                st.error(
                    "💀 El mal prevalece… ¡Sauron ríe! ESPERABA MÁS DE TI FRODO Y COMPAÑÍA."
                )
                st.audio("triste.mp3")
