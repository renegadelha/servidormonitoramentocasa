//Bibliotecas utilizada para realizar a conexão e as interações com a web
#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h> 
#include <ESP8266HTTPClient.h>

//Nome da rede (ssid) e senha (password)
const char * ssid = "Informatica";
const char * password = "1234567890";

//Dados do servidor (IP e porta do serviço)
String ipLocal = "192.168.0.100";
String portaLocal = "5000";

//Cada equipe deverá ter um nome diferente para armazenar no banco de dados
String equipe = "Equipe-Adson";

//Endereço do servidor feito pela composição do IP, porta e o path /api/sensor
String serverName = "http://" + ipLocal + ":" + portaLocal + "/api/sensor";

//Pinos utilizados pelo sensor ultrassônico
const int trigPin = 12;
const int echoPin = 14;

//Define a velocidade do som em cm por microsegundo
#define VELOCIDADE_SOM 0.034

//Variáveis utilizadas para calcular a distância em centímetros
long tempo;
float distancia;

void setup() {
  Serial.begin(9600); //Inicializa a comunicação serial
  pinMode(trigPin, OUTPUT); //Define o pino trig como de saída (OUTPUT)
  pinMode(echoPin, INPUT); //Define o pino echo como de entrada (INPUT)


  WiFi.begin(ssid, password); //Conecta na rede: nome da rede e senha
  Serial.println("Connecting");
  while(WiFi.status() != WL_CONNECTED) { //Se mantém nesse loop enquanto a conexão não for estabelecida
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("Connected to WiFi network with IP Address: ");
  Serial.println(WiFi.localIP());


}

void loop() {
  //Os comandos a seguir são utilizados para calcular a distância
  //Lembrando que a velocidade é divida por dois, visto que o som vai e volta (queremos apenas a ida)
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  tempo = pulseIn(echoPin, HIGH);
  distancia = tempo * VELOCIDADE_SOM / 2;
  
  //Imprime a distância no monitor serial
  Serial.print("Distancia (cm): ");
  Serial.println(distancia);

  // Verifica se o ESP está conectado
  if (WiFi.status() == WL_CONNECTED) {  
    WiFiClient client;
    HTTPClient http;
    
    http.begin(client, serverName); //Inicializa o serviço HTTP

    //Específica o cabeçalho do Content-Type: application/json
    http.addHeader("Content-Type", "application/json");
    //Especifica os dados que serão enviados por HTTP POST
    String httpRequestData = "{\"distancia\":" + String(distancia) + ", \"equipe\":\"" + String(equipe) + "\"}";
    //Envia requisição por HTTP POST
    int httpResponseCode = http.POST(httpRequestData);

    //Fechando a conexão
    http.end(); 
  }
  
  //Espera 1 segundo 
  delay(1000);
}