import sys
import time

import network
from machine import PWM, Pin
from umqtt.robust import MQTTClient

# Configurações da rede WiFi
SSID_WIFI = ""  # Nome da rede WiFi
SENHA_WIFI = ""  # Senha da rede WiFi
MAX_TENTATIVAS = 20  # Número máximo de tentativas para conectar ao WiFi

# Configurações do cliente MQTT
NOME_CLIENTE = bytes("cliente_" + "12321", "utf-8")
URL_BROKER_MQTT = ""  # Endereço do broker MQTT


class Embarcado:
    def __init__(self):
        # Inicializa os pinos para controle dos motores
        self.pino_motor_1 = Pin(18)  # Sustentação
        self.pino_motor_2 = Pin(19)  # Sustentação
        self.pino_motor_3 = Pin(27)  # Movimento
        self.pino_motor_4 = Pin(26)  # Movimento
        self.pino_led_esp32 = Pin(2) # LED

        # Inicializa PWM nos pinos
        self.motor_1 = PWM(self.pino_motor_1, freq=1000, duty=0)
        self.motor_2 = PWM(self.pino_motor_2, freq=1000, duty=0)
        self.motor_3 = PWM(self.pino_motor_3, freq=1000, duty=0)
        self.motor_4 = PWM(self.pino_motor_4, freq=1000, duty=0)
        self.led = PWM(self.pino_led_esp32, freq=1000, duty=0)

        # Tópicos MQTT
        self.TOPICO_LIGAR = b"ligar"               # on/off
        self.TOPICO_CONTROLE = b"controle/motores" # frente, virar_direita, virar_esquerda, parar

    def ligar_motores_sustentacao(self):
        """Ligar motores de sustentação (1 e 2)"""
        self.motor_1.duty(1023)
        self.motor_2.duty(1023)

    def desligar_motores_sustentacao(self):
        """Desligar motores de sustentação"""
        self.motor_1.duty(0)
        self.motor_2.duty(0)

    def ir_frente(self):
        """Ir para frente usando motores 3 e 4"""
        self.motor_3.duty(1023)
        self.motor_4.duty(1023)

    def virar_direita(self):
        """Virar à direita motor 3 on / motor 4 off"""
        self.motor_3.duty(1023)
        self.motor_4.duty(0)

    def virar_esquerda(self):
        """Virar à esquerda motor 3 off / motor 4 on"""
        self.motor_3.duty(0)
        self.motor_4.duty(1023)

    def parar_movimento(self):
        """Parar o movimento (motores 3 e 4)"""
        self.motor_3.duty(0)
        self.motor_4.duty(0)

    def ligar(self):
        """Ligar LED e motores de sustentação"""
        self.led.duty(1023)
        self.ligar_motores_sustentacao()

    def desligar(self):
        """Desligar LED e motores de sustentação"""
        self.led.duty(0)
        self.desligar_motores_sustentacao()
        self.parar_movimento()

    def setup(self):
        """Configurações iniciais"""
        self.ligar()  # Liga LED e sustentação inicialmente
        self.parar_movimento()

    def callback(self, topic, msg):

        print(f"Dados recebidos: TÓPICO = {topic}, MENSAGEM = {msg}")
        msg = msg.decode()

        # Callback de mensagens MQTT
        if topic == self.TOPICO_LIGAR:
            if msg == "on":
                self.ligar()
            elif msg == "off":
                self.desligar()

        elif topic == self.TOPICO_CONTROLE:
            if msg == "frente":
                self.ir_frente()
            elif msg == "virar_direita":
                self.virar_direita()
            elif msg == "virar_esquerda":
                self.virar_esquerda()


    def aguardar_conexao(self, wifi):
        """Aguarda até que a conexão WiFi seja estabelecida ou atinja o número máximo de tentativas."""
        tentativas = 0
        while not wifi.isconnected() and tentativas < MAX_TENTATIVAS:
            print(f"Tentativa {tentativas + 1}/{MAX_TENTATIVAS}")
            time.sleep(2)
            tentativas += 1
        return wifi.isconnected()

    def conectar_wifi(self):
        """Configura a interface WiFi e conecta à rede."""
        wifi = network.WLAN(network.STA_IF)
        wifi.active(True)
        wifi.disconnect()
        wifi.connect(SSID_WIFI, SENHA_WIFI)
        return wifi

    def executar(self):
        wifi = self.conectar_wifi()
        if self.aguardar_conexao(wifi):
            print("WiFi conectado")
        else:
            print("Não foi possível conectar ao WiFi")
            sys.exit()

        # Conecta ao broker MQTT
        client = MQTTClient(NOME_CLIENTE, URL_BROKER_MQTT, keepalive=60)
        time.sleep(3)

        while True:
            try:
                self.setup()
                print("Tentanto conectar")
                client.connect()
                print("SUCESSO | Conectado ao broker MQTT")
                break
            except Exception as e:
                print(
                   "Nao foi possivel conectar ao servidor MQTT {}{}".format(
                       type(e).__name__, e
                    )
                )
                sys.exit()
                time.sleep(2)


        # Conectar MQTT
        client.set_callback(self.callback)

        # Subscrever aos tópicos
        client.subscribe(self.TOPICO_LIGAR)
        client.subscribe(self.TOPICO_CONTROLE)

        # Loop principal
        while True:
            try:
                client.check_msg()
                time.sleep(1)
            except Exception:
                sys.exit()

if __name__ == "__main__":
    dispositivo = Embarcado()
    dispositivo.executar()
