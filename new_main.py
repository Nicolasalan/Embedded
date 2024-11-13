import sys
import time

import network
from machine import PWM, Pin
from umqtt.robust import MQTTClient

# Configurações da rede WiFi
SSID_WIFI = "Claudiosalce"  # Nome da rede WiFi
SENHA_WIFI = "eunaosei"  # Senha da rede WiFi
MAX_TENTATIVAS = 20  # Número máximo de tentativas para conectar ao WiFi

# Configurações do cliente MQTT
NOME_CLIENTE = bytes("cliente_" + "12321", "utf-8")
URL_BROKER_MQTT = "172.20.10.14"  # Endereço do broker MQTT
TIMEOUT_VIRAR = 5

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
        self.TOPICO_LIGAR = b"ligar"  # Defina o tópico para ligar
        self.TOPICO_MOVER = b"controle/motores"  # Defina o tópico para virar à direita
        self.TOPICO_STATUS = b"status/"  # Tópico para publicar o status
        self.TOPICO_INTERVALO = b"intervalo"  # Tópico para receber valores do slider

        self.ultimo_comando_direita = 0
        self.ultimo_comando_esquerda = 0

        self.potencia_maxima = 1023

        # Cliente MQTT será inicializado no método executar
        self.cliente = None

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
                self.publicar_status("ligado")
            elif msg == "off":
                self.desligar_motores_sustentacao()
                self.desligar_led()
                self.publicar_status("desligado")

        elif topico == self.TOPICO_MOVER:
            if msg == "virar_direita":
                self.ligar_motor_virar_direita()
                self.ultimo_comando_direita = time.time()

            elif msg == "virar_esquerda":
                self.ligar_motor_virar_esquerda()
                self.ultimo_comando_esquerda = time.time()

        elif topico == self.TOPICO_INTERVALO:
            try:
                valor = int(msg)
                if 10 <= valor <= 1023:
                    self.ajustar_potencia(valor)
                else:
                    print(f"Valor de potência fora do intervalo: {valor}")
            except ValueError:
                print(f"Valor inválido recebido no tópico intervalo: {msg}")

    def publicar_status(self, estado):
        """Publica o estado atual no tópico de status."""
        if self.cliente:
            try:
                self.cliente.publish(self.TOPICO_STATUS, estado.encode())
                print(f"Status publicado: {estado}")
            except Exception as e:
                print(f"Erro ao publicar status: {e}")

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
        self.motor_virar_direita.duty(self.potencia_maxima)
        self.motor_virar_esquerda.duty(0)

    def desligar_motor_virar_direita(self):
        """Desligar motor para virar à direita"""
        self.motor_virar_direita.duty(0)

    def ligar_motor_virar_esquerda(self):
        """Ligar motor para virar à esquerda"""
        self.motor_virar_esquerda.duty(self.potencia_maxima)
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

    def ajustar_potencia(self, valor):
        """Ajusta a potência dos motores de sustentação"""
        print(f"Ajustando potência para: {valor}")
        self.potencia_maxima = valor

    def setup(self):
        """Configurações iniciais do dispositivo embarcado."""
        self.desligar_motores_sustentacao()
        self.desligar_motor_virar_direita()
        self.desligar_motor_virar_esquerda()
        self.desligar_led()
        self.publicar_status("desligado")  # Publica o estado inicial

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
        cliente.subscribe(self.TOPICO_MOVER)
        cliente.subscribe(self.TOPICO_INTERVALO)

        # Loop principal para verificar mensagens MQTT e controlar timeout
        while True:
            try:
                cliente.check_msg()

                current_time = time.time()

                # Verifica timeout para virar à direita
                if (current_time - self.ultimo_comando_direita) > TIMEOUT_VIRAR:
                    self.desligar_motor_virar_direita()

                # Verifica timeout para virar à esquerda
                if (current_time - self.ultimo_comando_esquerda) > TIMEOUT_VIRAR:
                    self.desligar_motor_virar_esquerda()

                time.sleep(0.1)  # Pequena pausa para evitar sobrecarga
            except Exception:
                cliente.disconnect()
                sys.exit()

# Instancia e executa a classe Embarcado
if __name__ == "__main__":
    dispositivo = Embarcado()
    dispositivo.executar()
