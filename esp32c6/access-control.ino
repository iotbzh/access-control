#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <SPI.h>
#include <MFRC522.h>

// ---- Configuration Porte ----
#define PORTE_NAME "porte1"  // Change en "porte2", "porte3", etc. pour chaque porte

#define RST_PIN   21   // RC522 reset pin
#define SS_PIN    22   // RC522 SDA (SS) pin

const int LED_VERTE = 1; //  (adapte selon ton câblage)
const int LED_ROUGE = 0; //  (adapte selon ton câblage)

// ---- WiFi Parameters ----
const char* ssid = "freebox_sly";
const char* password = "~zF<^^KL>4FHYE!Gh?^Z^RF!UCe(:8;~ndUaL>-w.=1@y41}nrl+lTO^-zhP+<3";

// ---- MQTT Parameters ----
const char* mqtt_server = "192.168.0.29";
const int mqtt_port = 1883;
const char* mqtt_user = "utilisateur_mqtt";
const char* mqtt_pass = "root";

// ---- MQTT Topics ----
String topic_uid = "controle_acces/" PORTE_NAME "/uid";
String topic_led = "controle_acces/" PORTE_NAME "/led";
String topic_status = "lecteur/" PORTE_NAME "/status";

// ---- RFID ----
MFRC522 mfrc522(SS_PIN, RST_PIN);   // Create MFRC522 instance

WiFiClient espClient;
PubSubClient client(espClient);

// ---- WiFi Connection ----
void setup_wifi() {
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected, IP address: ");
  Serial.println(WiFi.localIP());
}

// ---- MQTT Callback ----
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("MQTT message received on topic: ");
  Serial.println(topic);
  Serial.print("Payload: ");
  String msg;
  for (unsigned int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
    msg += (char)payload[i];
  }
  Serial.println();
  msg.trim(); // Remove whitespace/newlines

  if (msg == "OK") {
    Serial.println("Green LED ON, Red LED OFF");
    digitalWrite(LED_VERTE, HIGH);
    digitalWrite(LED_ROUGE, LOW);
    delay(2000);
    digitalWrite(LED_VERTE, LOW);
  } else if (msg == "NO") {
    Serial.println("Red LED ON, Green LED OFF");
    digitalWrite(LED_VERTE, LOW);
    digitalWrite(LED_ROUGE, HIGH);
    delay(2000);
    digitalWrite(LED_ROUGE, LOW);
  } else {
    Serial.println("Unknown message, LEDs OFF");
    digitalWrite(LED_VERTE, LOW);
    digitalWrite(LED_ROUGE, LOW);
  }
}

// ---- MQTT Reconnection ----
void reconnect() {
  String clientId = "ESP32-" PORTE_NAME;

  while (!client.connected()) {
    Serial.print("Connecting to MQTT broker...");
    // Pass LWT as arguments here:
    if (client.connect(
          clientId.c_str(),
          mqtt_user, mqtt_pass,
          topic_status.c_str(), // willTopic
          0,                   // willQoS
          true,                // willRetain
          "offline"            // willMessage
        )) {
      Serial.println("connected");
      client.subscribe(topic_led.c_str());
      Serial.print("Subscribed to: ");
      Serial.println(topic_led);
      // Publish "online" status after (re)connection
      client.publish(topic_status.c_str(), "online", true);
      Serial.println("Published 'online' status");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 2 seconds");
      delay(2000);
    }
  }
}


// ---- Setup ----
void setup() {
  Serial.begin(115200);
  pinMode(LED_VERTE, OUTPUT);
  pinMode(LED_ROUGE, OUTPUT);

  // Test LEDs at startup
  digitalWrite(LED_VERTE, HIGH);
  digitalWrite(LED_ROUGE, HIGH);
  delay(1000);
  digitalWrite(LED_VERTE, LOW);
  digitalWrite(LED_ROUGE, LOW);

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  SPI.begin();
  mfrc522.PCD_Init();
  Serial.println("RFID reader ready. Present a card...");
}

// ---- Main Loop ----
void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Check for new RFID card
  if (!mfrc522.PICC_IsNewCardPresent()) return;
  if (!mfrc522.PICC_ReadCardSerial()) return;

  // Get UID as hex string
  String uid = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();

  Serial.print("UID read: ");
  Serial.println(uid);

  // Publish UID to MQTT
  client.publish(topic_uid.c_str(), uid.c_str());
  Serial.println("UID published to MQTT");

  delay(2000); // Debounce
  mfrc522.PICC_HaltA(); // Stop reading
}
