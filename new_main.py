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
        # Inicializa os pinos para controle dos motores e LED
        # Defina os pinos conforme sua configuração
        self.pino_motor_sustentacao_1 = Pin(XX)  # Substitua XX pelo número do pino
        self.pino_motor_sustentacao_2 = Pin(XX)  # Substitua XX pelo número do pino
        self.pino_motor_virar_direita = Pin(XX)  # Substitua XX pelo número do pino
        self.pino_motor_virar_esquerda = Pin(XX)  # Substitua XX pelo número do pino
        self.pino_led = Pin(XX)  # Substitua XX pelo número do pino

        # Inicializa PWM nos pinos correspondentes
        self.motor_sustentacao_1 = PWM(self.pino_motor_sustentacao_1, freq=1000, duty=0)
        self.motor_sustentacao_2 = PWM(self.pino_motor_sustentacao_2, freq=1000, duty=0)
        self.motor_virar_direita = PWM(self.pino_motor_virar_direita, freq=1000, duty=0)
        self.motor_virar_esquerda = PWM(self.pino_motor_virar_esquerda, freq=1000, duty=0)
        self.led = PWM(self.pino_led, freq=1000, duty=0)

        # Inicializa os tópicos MQTT
        self.TOPICO_LIGAR = b""  # Defina o tópico para ligar
        self.TOPICO_DESLIGAR = b""  # Defina o tópico para desligar
        self.TOPICO_VIRAR_DIREITA = b""  # Defina o tópico para virar à direita
        self.TOPICO_VIRAR_ESQUERDA = b""  # Defina o tópico para virar à esquerda

    def conectar_wifi(self):
        """Configura a interface WiFi e conecta à rede."""
        wifi = network.WLAN(network.STA_IF)
        wifi.active(True)
        wifi.disconnect()
        wifi.connect(SSID_WIFI, SENHA_WIFI)
        return wifi

    def aguardar_conexao(self, wifi):
        """Aguarda até que a conexão WiFi seja estabelecida ou atinja o número máximo de tentativas."""
        tentativas = 0
        while not wifi.isconnected() and tentativas < MAX_TENTATIVAS:
            print(f"Tentativa {tentativas + 1}/{MAX_TENTATIVAS}")
            time.sleep(2)
            tentativas += 1
        return wifi.isconnected()

    def callback(self, topico, mensagem):
        """Função de callback chamada ao receber uma mensagem MQTT."""

        print(f"Dados recebidos: TÓPICO = {topico}, MENSAGEM = {mensagem}")
        msg = mensagem.decode()

        if topico == self.TOPICO_LIGAR:
            if msg == "on":
                self.ligar_motores_sustentacao()
                self.ligar_led()
            elif msg == "off":
                self.desligar_motores_sustentacao()
                self.desligar_led()

        elif topico == self.TOPICO_VIRAR_DIREITA:
            if msg == "on":
                self.ligar_motor_virar_direita()
            elif msg == "off":
                self.desligar_motor_virar_direita()

        elif topico == self.TOPICO_VIRAR_ESQUERDA:
            if msg == "on":
                self.ligar_motor_virar_esquerda()
            elif msg == "off":
                self.desligar_motor_virar_esquerda()

    def ligar_motores_sustentacao(self):
        """Ligar motores de sustentação"""
        self.motor_sustentacao_1.duty(1023)
        self.motor_sustentacao_2.duty(1023)

    def desligar_motores_sustentacao(self):
        """Desligar motores de sustentação"""
        self.motor_sustentacao_1.duty(0)
        self.motor_sustentacao_2.duty(0)

    def ligar_motor_virar_direita(self):
        """Ligar motor para virar à direita"""
        self.motor_virar_direita.duty(1023)
        self.motor_virar_esquerda.duty(0)

    def desligar_motor_virar_direita(self):
        """Desligar motor para virar à direita"""
        self.motor_virar_direita.duty(0)

    def ligar_motor_virar_esquerda(self):
        """Ligar motor para virar à esquerda"""
        self.motor_virar_esquerda.duty(1023)
        self.motor_virar_direita.duty(0)

    def desligar_motor_virar_esquerda(self):
        """Desligar motor para virar à esquerda"""
        self.motor_virar_esquerda.duty(0)

    def ligar_led(self):
        """Ligar LED"""
        self.led.duty(1023)

    def desligar_led(self):
        """Desligar LED"""
        self.led.duty(0)

    def setup(self):
        """Configurações iniciais do dispositivo embarcado."""
        self.desligar_motores_sustentacao()
        self.desligar_motor_virar_direita()
        self.desligar_motor_virar_esquerda()
        self.desligar_led()

    def executar(self):
        """Método principal para executar as operações do dispositivo embarcado."""
        # Conecta ao WiFi
        wifi = self.conectar_wifi()
        if self.aguardar_conexao(wifi):
            print("WiFi conectado")
        else:
            print("Não foi possível conectar ao WiFi")
            sys.exit()

        # Conecta ao broker MQTT
        cliente = MQTTClient(NOME_CLIENTE, URL_BROKER_MQTT, keepalive=60)
        time.sleep(3)

        self.setup()

        while True:
            try:
                print("Tentando conectar ao broker MQTT")
                cliente.connect()
                print("SUCESSO | Conectado ao broker MQTT")
                break
            except Exception as e:
                print(
                    "Não foi possível conectar ao servidor MQTT {}{}".format(
                        type(e).__name__, e
                    )
                )
                time.sleep(2)

        # Configura a função de callback e se inscreve nos tópicos MQTT
        cliente.set_callback(self.callback)

        # Inscreve nos tópicos MQTT
        cliente.subscribe(self.TOPICO_LIGAR)
        cliente.subscribe(self.TOPICO_VIRAR_DIREITA)
        cliente.subscribe(self.TOPICO_VIRAR_ESQUERDA)

        # Loop principal para verificar mensagens MQTT
        while True:
            try:
                cliente.check_msg()
            except Exception:
                cliente.disconnect()
                sys.exit()


# Instancia e executa a classe Embarcado
if __name__ == "__main__":
    dispositivo = Embarcado()
    dispositivo.executar()
