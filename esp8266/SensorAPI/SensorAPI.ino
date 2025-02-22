#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h> 
#include <ESP8266HTTPClient.h>


const char * ssid = "Lightdi";
const char * password = "!Lightdi1664";


String ipLocal = "192.168.68.57";
String portaLocal = "5000";

String equipe = "Equipe-Adson";

String serverName = "http://" + ipLocal + ":" + portaLocal + "/api/sensor";

const int trigPin = 12;
const int echoPin = 14;

//define sound velocity in cm/uS
#define SOUND_VELOCITY 0.034

long duration;
float distanceCm;

void setup() {
  Serial.begin(9600); // Starts the serial communication
  pinMode(trigPin, OUTPUT); // Sets the trigPin as an Output
  pinMode(echoPin, INPUT); // Sets the echoPin as an Input


  WiFi.begin(ssid, password);
  Serial.println("Connecting");
  while(WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("Connected to WiFi network with IP Address: ");
  Serial.println(WiFi.localIP());


}

void loop() {
  // Clears the trigPin
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  // Sets the trigPin on HIGH state for 10 micro seconds
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  // Reads the echoPin, returns the sound wave travel time in microseconds
  duration = pulseIn(echoPin, HIGH);
  
  // Calculate the distance
  distanceCm = duration * SOUND_VELOCITY/2;
  
  // Prints the distance on the Serial Monitor
  Serial.print("Distance (cm): ");
  Serial.println(distanceCm);

  // Verifica se o esp está conectado
  if (WiFi.status() == WL_CONNECTED) {  
    WiFiClient client;
    HTTPClient http;
    
    http.begin(client, serverName);

  // Specify content-type header
    http.addHeader("Content-Type", "application/json");
    // Data to send with HTTP POST
    String httpRequestData = "{\"distancia\":" + String(distanceCm) + ", \"equipe\":\"" + String(equipe) + "\"}";       
    // Send HTTP POST request
    int httpResponseCode = http.POST(httpRequestData);
    //fechando a conexão

    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);

    http.end();
  }
  
  delay(3000);
}