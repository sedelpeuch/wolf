//Libraries
#include <SPI.h>//https://www.arduino.cc/en/reference/SPI
#include <MFRC522.h>//https://github.com/miguelbalboa/rfid
#include <WiFi.h>
#include <HTTPClient.h>
#include <LiquidCrystal.h>
#include <ArduinoJson.h>

const char* ssid = "eirlabIoT";
const char* password = "";
const char* token = "";

// Create An LCD Object. Signals: [ RS, EN, D4, D5, D6, D7 ]
LiquidCrystal My_LCD(13, 12, 14, 27, 26, 25);

//Constants
#define SS_PIN 5
#define RST_PIN 0

#define BUZZ_PIN 4
#define RED_PIN 22
#define GREEN_PIN 33
#define BLUE_PIN 32
//Parameters
const int ipaddress[4] = {103, 97, 67, 25};
//Variables
byte nuidPICC[4] = {0, 0, 0, 0};
MFRC522::MIFARE_Key key;
MFRC522 rfid = MFRC522(SS_PIN, RST_PIN);

String uid;

void setup() {
  pinMode(BUZZ_PIN, OUTPUT);
  digitalWrite(BUZZ_PIN, LOW);


  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);

  digitalWrite(RED_PIN, HIGH);

  // Initialize The LCD. Parameters: [ Columns, Rows ]
  My_LCD.begin(16, 2);
  // Clears The LCD Display
  My_LCD.clear();

  My_LCD.print("Initialize");

 //Init Serial USB
 Serial.begin(115200);
 Serial.println(F("Initialize System"));
 //init rfid D8,D5,D6,D7
 SPI.begin();
 rfid.PCD_Init();
 Serial.print(F("Reader :"));
 rfid.PCD_DumpVersionToSerial();

  delay(1000);

  My_LCD.clear();
  My_LCD.print("Connecting");
  My_LCD.setCursor(0,1);

  WiFi.mode(WIFI_STA); //Optional
  WiFi.begin(ssid, password);
  Serial.println("\nConnecting");

  while(WiFi.status() != WL_CONNECTED){
      Serial.print(".");
      My_LCD.print(".");
    delay(100);
  }


  My_LCD.clear();
  My_LCD.print("Connected");
  My_LCD.setCursor(0,1);
  My_LCD.print("IP: ");
  My_LCD.print(WiFi.localIP());

  Serial.println("\nConnected to the WiFi network");
  Serial.print("Local ESP32 IP: ");
  Serial.println(WiFi.localIP());

  digitalWrite(RED_PIN, LOW);
  digitalWrite(BLUE_PIN, HIGH);



  My_LCD.clear();
}
void loop() {
 My_LCD.setCursor(0,0);
 My_LCD.print("Pret a scanner");
 delay(100);
 readRFID(&uid);
}


void readRFID(String *uid) { /* function readRFID */
 ////Read RFID card
 for (byte i = 0; i < 6; i++) {
   key.keyByte[i] = 0xFF;
 }
 // Look for new 1 cards
 if ( ! rfid.PICC_IsNewCardPresent())
   return;
 // Verify if the NUID has been readed
 if (  !rfid.PICC_ReadCardSerial())
   return;
 // Store NUID into nuidPICC array
 for (byte i = 0; i < 4; i++) {
   nuidPICC[i] = rfid.uid.uidByte[i];
 }
 //Serial.print(F("RFID In dec: "));
 *uid = Uid_Hex(rfid.uid.uidByte, rfid.uid.size);

  Serial.println(*uid);

  digitalWrite(BLUE_PIN, LOW);
  digitalWrite(BUZZ_PIN, HIGH);
  digitalWrite(GREEN_PIN, HIGH);
  delay(200);
  digitalWrite(BUZZ_PIN, LOW);
  delay(500);
 // Halt PICC


  digitalWrite(BLUE_PIN, LOW);
  digitalWrite(RED_PIN, HIGH);


  My_LCD.clear();
  My_LCD.print("ID: ");
  for(int i = 0; i < 12; i++)
  {
    My_LCD.print((*uid)[i]);
  }
  My_LCD.setCursor(0,1);
  for(int i = 12; i < 20; i++)
  {
    My_LCD.print((*uid)[i]);
  }

 rfid.PICC_HaltA();
 // Stop encryption on PCD
 rfid.PCD_StopCrypto1();

 if ((WiFi.status() == WL_CONNECTED)) { //Check the current connection status
    HTTPClient http;
    for(int j=1; j<20; j++){
      String j_str = (String) j;
      My_LCD.clear();
      My_LCD.print("Recherche");
      My_LCD.setCursor(0,1);
      My_LCD.print("en cours ...");
      http.begin("https://gestion.eirlab.net/api/index.php/members/?sortfield=t.rowid&sortorder=ASC&limit=20&page="+j_str); //Specify the URL
      http.addHeader("Accept", "application/json");
      http.addHeader("DOLAPIKEY", token);
      int httpCode = http.GET();
      if (httpCode > 0 ) { //Check for the returning code
        DynamicJsonDocument doc(50000);
        String json = http.getString();

        DeserializationError error = deserializeJson(doc, json);

        if (error) {
          Serial.print("deserializeJson() failed: ");
          Serial.println(error.c_str());
          
            My_LCD.clear();
            My_LCD.print("Failed:");
            My_LCD.setCursor(0,1);
            My_LCD.print(error.c_str());
            delay(5000);

            My_LCD.clear();
            digitalWrite(RED_PIN, LOW);
            digitalWrite(GREEN_PIN, LOW);
            digitalWrite(BLUE_PIN, HIGH);
          return;
        }

        for (JsonObject item : doc.as<JsonArray>()) {

          const char* id = item["id"]; // "2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", ...
          const char* lastname = item["lastname"]; // "FRAYSSINOUS", "Amat", "Mongabure", "PARAISO", "Darmon", ...
          const char* firstname = item["firstname"]; // "Guy", "Paul", "Xan", "Aurèle", "Valentin", "Fatima", ...
          long datec = item["datec"]; // 1647471600, 1647385200, 1647212400, 1646694000, 1646262000, 1646262000, ...
          long datem = item["datem"]; // 1657384213, 1648315351, 1648315351, 1648315351, 1648315351, 1648315351, ...
          String nserie = item["array_options"]["options_nserie"];
          if(nserie == *uid){
            My_LCD.clear();
            My_LCD.print(lastname);
            Serial.println(lastname);
            My_LCD.setCursor(0,1);
            My_LCD.print(firstname);
            Serial.println(firstname);
            delay(5000);

            My_LCD.clear();

            digitalWrite(RED_PIN, LOW);
            digitalWrite(GREEN_PIN, LOW);
            digitalWrite(BLUE_PIN, HIGH);
            return;
          }
        }
      }

      else {
        Serial.println("Error on HTTP request");
      }

      http.end(); //Free the resources
      My_LCD.clear();
      My_LCD.print("Adhérent inconnu");
    }
  }



  delay(5000);

  My_LCD.clear();

  digitalWrite(RED_PIN, LOW);
  digitalWrite(GREEN_PIN, LOW);
  digitalWrite(BLUE_PIN, HIGH);

}
/**
   Helper routine to dump a byte array as hex values to Serial.
*/
String Uid_Hex(byte *buffer, byte bufferSize) {
  String uid;
  char provi[10];
 for (byte i = 0; i < bufferSize; i++) {
  if(i != bufferSize - 1)
   {
   sprintf(provi, "%s%X:", buffer[i] < 0x10 ? "" : "", buffer[i]);
   }
   else
   {
   sprintf(provi, "%s%X", buffer[i] < 0x10 ? "0" : "", buffer[i]);
   }

  uid.concat(provi);
 }
  //Serial.println(uid);
  return(uid);
}
