import simpy
import random

# Parametri base (tempi produzione per prodotto e fase)
TEMPI_PRODUZIONE = {
    'Armadio': {'Taglio': (1, 2), 'Assemblaggio': (1, 2), 'Qualità': (0.5, 1)},
    'Cassettiera': {'Taglio': (2, 3), 'Assemblaggio': (2, 3), 'Qualità': (1, 1.5)},
    'Credenza': {'Taglio': (3, 4), 'Assemblaggio': (3, 4), 'Qualità': (1.5, 2)},
    'Tavolo': {'Taglio': (6, 8), 'Assemblaggio': (6, 10), 'Qualità': (2.5, 5)},
}

TURNO_INIZIO = 8     # h
TURNO_FINE = 17      # h

registro_fasi = []  # Lista globale per salvare i dati di ogni fase

def attendi_turno(env):
    ora_corrente = env.now % 24
    if ora_corrente < TURNO_INIZIO:
        attesa = TURNO_INIZIO - ora_corrente
    elif ora_corrente >= TURNO_FINE:
        attesa = 24 - ora_corrente + TURNO_INIZIO
    else:
        attesa = 0
    if attesa > 0:
        # print(f"[{env.now:.2f}h] Operatore in attesa del turno (pausa {attesa:.2f}h)")
        yield env.timeout(attesa)

def lavorazione(env, prodotto, id_lotto, fasi, linea, operatori):
    with linea.request() as req_linea:
        yield req_linea  # Richiede accesso esclusivo alla linea
        for fase in ['Taglio', 'Assemblaggio', 'Qualità']:
            with operatori.request() as op:
                yield op
                yield from attendi_turno(env)
                tempo = random.uniform(*fasi[fase])
                inizio = env.now
                # print(f"[{inizio:.2f}h] Lotto {id_lotto} ({prodotto}) inizia {fase}")
                yield env.timeout(tempo)
                fine = env.now
                # print(f"[{fine:.2f}h] Lotto {id_lotto} ({prodotto}) finisce {fase}")

                # Registra i dati della fase
                registro_fasi.append({
                    "Lotto": id_lotto,
                    "Prodotto": prodotto,
                    "Fase": fase,
                    "Inizio": inizio,
                    "Fine": fine
                })

def genera_dati_lotti(num_operatori=2):
    """
    Genera i dati di produzione con la simulazione.
    num_operatori: numero di operatori disponibili (capacità risorsa).
    Restituisce la lista di dizionari con dati fasi.
    """
    global registro_fasi
    registro_fasi = []

    env = simpy.Environment()
    linea = simpy.Resource(env, capacity=1)  # Solo 1 lotto per volta sulla linea
    operatori = simpy.Resource(env, capacity=num_operatori)  # Numero operatori

    # Lotti da produrre: prodotti A, B, C con quantità casuali min 3
    lotti = []
    for prodotto in ['Armadio', 'Cassettiera', 'Credenza','Tavolo']:
        quantita = random.randint(3, 6)  # almeno 3
        for _ in range(quantita):
            lotti.append(prodotto)

    id_lotto = 1
    for prodotto in lotti:
        env.process(lavorazione(env, prodotto, id_lotto, TEMPI_PRODUZIONE[prodotto], linea, operatori))
        id_lotto += 1

    env.run()

    return registro_fasi


# Per test veloce
if __name__ == "__main__":
    dati = genera_dati_lotti(num_operatori=2)
    #for riga in dati:
       # print(riga)
        
