from machine import Pin
import network
import time
from time import sleep
from umqtt.robust import MQTTClient
import sys

from machine import Pin, PWM
import network
import time
from umqtt.robust import MQTTClient
import sys

# Configurações da rede WiFi
SSID_WIFI = "Claudiosalce"        # Nome da rede WiFi
SENHA_WIFI = 'eunaosei'        	  # Senha da rede WiFi
MAX_TENTATIVAS = 20               # Número máximo de tentativas para conectar ao WiFi

# Configurações do cliente MQTT
NOME_CLIENTE = bytes('cliente_'+'12321', 'utf-8')            # Nome do cliente MQTT
URL_BROKER_MQTT = '172.20.10.14'    # Endereço do broker MQTT

class Embarcado:
    def __init__(self):
        # Inicializa os pinos para controle dos motores
        self.pino_motor_esquerda = Pin(15)
        self.pino_led = Pin(2)

        # Inicializa PWM nos pinos correspondentes
        self.motor_esquerda = PWM(self.pino_motor_esquerda, freq=1000, duty=0)
        self.led = PWM(self.pino_led, freq=1000, duty=0)

        # Inicializa os tópicos MQTT
        self.TOPICO_LIGAR = b'ligar'
        self.TOPICO_DESLIGAR = b'desligar'

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
        print(f'Dados recebidos: TÓPICO = {topico}, MENSAGEM = {mensagem}')
        msg = mensagem.decode()


        if topico == self.TOPICO_DESLIGAR:
            if msg == "off":
               self.desligar()

        if topico == self.TOPICO_LIGAR:
            if msg == "on":
               self.ligar()

    def ligar(self):
        """Ligar"""
        self.led.duty(1023)

    def desligar(self):
        """Desligar"""
        self.led.duty(0)

    def executar(self):
        """Método principal para executar as operações do dispositivo embarcado."""
        # Conecta ao WiFi
        wifi = self.conectar_wifi()
        if self.aguardar_conexao(wifi):
            print('WiFi conectado')
        else:
            print('Não foi possível conectar ao WiFi')
            sys.exit()

        # Conecta ao broker MQTT
        cliente = MQTTClient(NOME_CLIENTE, URL_BROKER_MQTT, keepalive=60)
        time.sleep(3)


        while True:
             try:
                print("Tentanto conectar")
                cliente.connect()
                print('SUCESSO | Conectado ao broker MQTT')
                break
             except Exception as e:
                 print('Nao foi possivel conectar ao servidor MQTT {}{}'.format(type(e).__name__, e))
                 time.sleep(2)

        # Configura a função de callback e se inscreve nos tópicos MQTT
        cliente.set_callback(self.callback)
        cliente.subscribe(self.TOPICO_LIGAR)
        cliente.subscribe(self.TOPICO_DESLIGAR)

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
