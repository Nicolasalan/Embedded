# Embedded

## Instalação do Node-RED

```bash

```bash
brew link mosquitto
brew install mosquitto-clients
sudo install mosquitto
ls $(brew --prefix mosquitto)/etc/mosquitto/mosquitto.conf
sudo nano $(brew --prefix mosquitto)/etc/mosquitto/mosquitto.conf
brew services start mosquitto
launchctl unload ~/Library/LaunchAgents/org.node-red.plist
launchctl load ~/Library/LaunchAgents/org.node-red.plist
brew services restart node-red
launchctl load ~/Library/LaunchAgents/node-red.plist
```

## Execução do Node-RED

1. Inicie o Node-RED, executando o seguinte comando:

```bash
node-red
```
2. Abrir o navegador e acessar o endereço:

```bash
http://localhost:1880/ui
```
