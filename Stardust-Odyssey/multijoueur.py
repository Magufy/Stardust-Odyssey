import socket
import threading
import time
import json


class P2PCommunication:
    def __init__(self, est_serveur=True, ip_hote=None, port=5555, local_skin_info=None):
        self.est_serveur = est_serveur
        self.ip_hote = ip_hote
        self.port = port
        self.socket = None
        self.connexion = None
        self.running = True
        self.data_lock = threading.Lock()
        self.last_send_time = 0
        self.buffer = b''
        self.message_separator = b'\n'
        self.local_skin_info = local_skin_info
        self.remote_skin_info = None
        self.send_interval = 1/30
        self.bullet_sync_interval=0.05

    def obtenir_adresse_ip_locale(self):
        """Obtient l'adresse IP locale de la machine"""
        try:
            # Créer une connexion socket temporaire pour obtenir l'IP locale
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_locale = s.getsockname()[0]
            s.close()
            return ip_locale
        except Exception as e:
            print(f"Erreur lors de l'obtention de l'adresse IP locale: {e}")
            return "127.0.0.1"

    def initialiser(self):
        """Initialise soit le serveur soit le client et échange les skins"""
        try:
            print(f"  Initialisation en tant que {'serveur' if self.est_serveur else 'client'}")
            if self.est_serveur:
                if not self.ip_hote:
                    self.ip_hote = self.obtenir_adresse_ip_locale()
                    print(f"  Adresse IP locale détectée: {self.ip_hote}")

                print("  Démarrage de l'initialisation du serveur")
                if not self.initialiser_serveur():
                    print("  Échec de l'initialisation du serveur")
                    return False
                print("  Serveur initialisé avec succès")
            else:
                print("  Démarrage de l'initialisation du client")
                if not self.initialiser_client():
                    print("  Échec de l'initialisation du client")
                    return False
                print("  Client initialisé avec succès")

            # Vérifier que la connexion est établie
            if not self.connexion:
                print("  Connexion non établie après initialisation")
                return False

            print("  Démarrage de l'échange d'informations sur les skins")
            if not self.exchange_skin_info():
                print("  Échec de l'échange d'informations sur le skin.")
                self.fermer()
                return False

            print(f"  Rôle: {'Serveur' if self.est_serveur else 'Client'}, Skin local: {self.local_skin_info.get('name', 'Inconnu')}, Skin distant: {self.remote_skin_info.get('name', 'Inconnu')}")

            return True
        except Exception as e:
            print(f"  Erreur lors de l'initialisation P2P: {e}")
            self.fermer()
            return False

    def initialiser_serveur(self):
        """Configure et démarre le serveur"""
        try:
            print("  Démarrage du serveur...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.settimeout(30.0)  # Timeout après 30 secondes

            try:
                print("  Tentative de bind sur 0.0.0.0:" + str(self.port))
                self.socket.bind(("0.0.0.0", self.port))
                print("  Bind réussi")
            except Exception as e:
                print(f"  Erreur lors du bind: {e}")
                return False

            self.socket.listen(1)

            print(f"\n=== INFORMATION DE CONNEXION ===")
            print(f"Serveur démarré sur l'adresse IP: {self.ip_hote}:{self.port}")
            print(f"Partagez cette adresse avec l'autre personne")
            print(f"============================\n")
            print("  En attente de connexion...")

            try:
                self.connexion, adresse = self.socket.accept()
                print(f"  Connexion acceptée de {adresse[0]}:{adresse[1]}")
            except socket.timeout as e:
                print(f"  Timeout lors de l'attente de connexion: {e}")
                return False
            except Exception as e:
                print(f"  Erreur lors de l'acceptation de la connexion: {e}")
                return False

            self.connexion.settimeout(None)
            print(f"Connexion établie avec {adresse[0]}:{adresse[1]}")
            return True
        except socket.timeout:
            print("  Aucune connexion reçue dans le délai imparti.")
            return False
        except Exception as e:
            print(f"  Erreur serveur générale: {e}")
            return False

    def initialiser_client(self):
        """Configure et connecte le client"""
        try:
            print(f"Tentative de connexion à {self.ip_hote}:{self.port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Définir un délai d'attente pour la connexion
            self.socket.settimeout(10.0)  # Délai d'attente de 10 secondes
            self.socket.connect((self.ip_hote, self.port))
            self.connexion = self.socket
            self.connexion.settimeout(None)

            print("Connexion établie!")
            return True
        except socket.timeout:
            print("Échec de la connexion : délai dépassé.")
            return False
        except Exception as e:
            print(f"Erreur client: {e}")
            return False

    def exchange_skin_info(self):
        """Exchanges skin info between server and client"""
        try:
            #  local_skin_info valide
            if not self.local_skin_info:
                print("  Aucune information de skin local à échanger.")
                return False

            # connexion valide
            if not self.connexion:
                print("  Pas de connexion établie pour échanger les skins.")
                return False

            print(f"  Envoi du skin local: {self.local_skin_info.get('name', 'Inconnu')}")

            local_skin_info_copy = {}

            if isinstance(self.local_skin_info, dict):

                for key, value in self.local_skin_info.items():
                    if isinstance(value, (str, int, float, bool, list, dict)) or value is None:
                        local_skin_info_copy[key] = value
            else:
                print(f"  Format de skin local invalide: {type(self.local_skin_info)}")
                local_skin_info_copy = {"name": "Basic Ship"}

            # info du skin local
            try:
                local_skin_payload = json.dumps({
                    'type': 'skin_info',
                    'skin': local_skin_info_copy
                }).encode('utf-8') + self.message_separator

                print(f"  Envoi payload: {local_skin_payload[:100]}...")
                self.connexion.sendall(local_skin_payload)
                print("  Skin local envoyé avec succès")
            except Exception as e:
                print(f"  Erreur lors de l'envoi du skin: {e}")
                return False

            # Recois les infos de skin du joueur a distance
            print("  Attente du skin distant...")
            self.connexion.settimeout(5.0)  # délai d'attente
            received_data = b''
            start_time = time.time()

            while self.message_separator not in received_data and time.time() - start_time < 5.0:
                try:
                    chunk = self.connexion.recv(1024)
                    if not chunk:
                        print("  Connexion fermée pendant l'échange de skins")
                        raise ConnectionAbortedError("La connexion a été fermée pendant l'échange de skins.")
                    received_data += chunk
                    print(f"  Reçu {len(chunk)} octets")
                except socket.timeout:
                    print("  Timeout lors de la réception, nouvelle tentative...")
                    continue
                except Exception as e:
                    print(f"  Erreur lors de la réception: {e}")
                    return False

            self.connexion.settimeout(None)  # Réinitialiser le délai d'attente

            if self.message_separator not in received_data:
                print("  Délai d'attente dépassé en attendant les infos du skin distant.")
                return False

            message = received_data[:received_data.find(self.message_separator)]
            print(f"  Message reçu: {message[:100]}...")

            try:
                data = json.loads(message.decode('utf-8'))
                print(f"  Message décodé: {data}")

                if data.get('type') == 'skin_info':
                    self.remote_skin_info = data.get('skin')
                    print(f"  Skin distant reçu avec succès: {self.remote_skin_info.get('name', 'Inconnu')}")
                    return True
                else:
                    print(f"  Type de message inattendu: {data.get('type')}")
                    return False
            except json.JSONDecodeError as e:
                print(f"  Erreur lors du décodage JSON: {e}")
                print(f"  Données reçues: {message.decode('utf-8', errors='replace')}")
                return False
            except Exception as e:
                print(f"  Erreur lors du traitement du skin distant: {e}")
                return False

        except (socket.timeout, json.JSONDecodeError, ConnectionAbortedError) as e:
            print(f"  Erreur lors de l'échange d'informations sur le skin: {e}")
            return False
        except Exception as e:
            print(f"  Erreur inattendue lors de l'échange skin: {e}")
            return False

    def envoyer_donnees(self, data):
        """Envoie des données JSON à l'autre pair, gère les différents types de messages."""
        try:
            current_time = time.time()
            # Limitation du débit pour les messages de type « état » uniquement
            if data.get('type') == 'state':
                if current_time - self.last_send_time < self.send_interval:
                    return  # Sauter l'envoi s'il est trop tôt
                self.last_send_time = current_time

            with self.data_lock:
                # S'assurer que les données sont un dictionnaire
                if not isinstance(data, dict):
                    print("Erreur: Les données à envoyer doivent être un dictionnaire.")
                    return False  # Ou gérer de manière appropriée

                # Préparer le message : Ajouter le type s'il manque (ne devrait pas se produire avec la nouvelle structure)
                if 'type' not in data:
                    data['type'] = 'unknown'  # Fallback, mais indique un problème

                # envoi
                message = json.dumps(data).encode('utf-8') + self.message_separator
                self.connexion.sendall(message)
                return True  # Indique que la tentative d'envoi a réussi

        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            print("Erreur de connexion lors de l'envoi (pair déconnecté?).")
            self.running = False  # Arrêter les fils de communication/les boucles
            return False
        except Exception as e:
            print(f"Erreur lors de l'envoi des données ({data.get('type', '?')}): {e}")
            return False  # défaillance

    def recevoir_donnees(self):
        """Reçoit et décode les messages JSON entrants."""
        try:
            data = self.connexion.recv(4096)
            if not data:
                
                # Connexion fermée par l'homologue
                print("Connexion fermée par le pair.")
                self.running = False
                return None

            self.buffer += data
            messages = []

            while self.message_separator in self.buffer:
                message_end = self.buffer.find(self.message_separator)
                message = self.buffer[:message_end]
                self.buffer = self.buffer[message_end + len(self.message_separator):]

                try:
                    # Decode le JSON
                    data_dict = json.loads(message.decode('utf-8'))
                    messages.append(data_dict) # Collect all received messages
                except json.JSONDecodeError:
                    print(f"Erreur de décodage JSON pour le message: {message[:100]}")  # skip les erreurs de message
                    continue
                except UnicodeDecodeError:
                    print(f"Erreur de décodage Unicode pour le message.")
                    continue

            # Return la list des messages recus
            return messages if messages else None

        except (BlockingIOError, socket.timeout):
            return None
        except (ConnectionResetError, ConnectionAbortedError):
            print("Erreur de connexion lors de la réception (pair déconnecté?).")
            self.running = False
            return None
        except Exception as e: # sauf erreur
            print(f"Erreur générique lors de la réception: {e}")
            self.running = False
            return None

    def démarrer_communication(self):
        self.running = True
        threading.Thread(target=self._recevoir_boucle, daemon=True).start()

    def _recevoir_boucle(self):
        while self.running:
            try:
                data = self.recevoir_donnees()
                if data:
                    pass
                time.sleep(0.01)  # sleep (évite des bugs/lags)
            except Exception as e:
                print(f"Erreur dans la boucle de réception: {e}")
                self.running = False
                break

    def fermer(self):
        if not self.running:  # Empêcher les fermetures multiples
            return
        self.running = False
        # Fermer la connexion
        if self.connexion:
            try:
                self.connexion.shutdown(socket.SHUT_RDWR)
            except OSError:  # Fermer le socket du serveur s'il existe# Le socket peut déjà être fermé
                pass
            except Exception as e:
                print(f"Erreur lors de l'arrêt de la connexion: {e}")
            finally:
                try:
                    self.connexion.close()
                except Exception as e:
                    print(f"Erreur lors de la fermeture de la connexion: {e}")
                self.connexion = None

        # Fermer le socket du serveur s'il existe
        if self.socket and self.est_serveur:
            try:
                self.socket.close()
            except Exception as e:
                print(f"Erreur lors de la fermeture du socket serveur: {e}")
            self.socket = None


class GameState:
    """Classe pour synchroniser l'état du jeu entre les joueurs"""
    def __init__(self):
        self.lock = threading.Lock()
        self.player1 = None
        self.player2 = None
        self.bullets_p1 = []
        self.bullets_p2 = []
        self.enemies = []
        self.wave_number = 1
        self.last_update_time = time.time()
        self.last_sync_time = time.time()
        self.sync_interval = 0.05  # Synchronisation toutes les 50ms

    def update_from_network(self, data, is_player1):
        current_time = time.time()
        if current_time - self.last_sync_time < self.sync_interval:
            return

        with self.lock:
            if is_player1:
                self.player1 = data.get('player', None)
                self.bullets_p1 = data.get('bullets', [])
            else:
                self.player2 = data.get('player', None)
                self.bullets_p2 = data.get('bullets', [])

            # Seul le serveur gère les ennemis
            if 'enemies' in data and len(data['enemies']) > 0:
                self.enemies = data['enemies']
            if 'wave' in data:
                self.wave_number = data['wave']

            self.last_sync_time = current_time
            self.last_update_time = current_time
