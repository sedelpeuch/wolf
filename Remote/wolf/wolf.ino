#include <SPI.h> // SPI
#include <MFRC522.h> // RFID

#define SS_PIN 10
#define RST_PIN 9

#define BUZZ_PIN 2
#define RED_PIN 7
#define GREEN_PIN 6
#define BLUE_PIN 8

#define N 20

int etat = 1;
    
// Déclaration 
MFRC522 rfid(SS_PIN, RST_PIN); 

// Tableau contentent l'ID
byte nuidPICC[N];

void setup() 
{ 
  // Init RS232
  Serial.begin(9600);

  // Init SPI bus
  SPI.begin(); 

  // Init MFRC522 
  rfid.PCD_Init(); 

  pinMode(BUZZ_PIN, OUTPUT);
  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);
}
 
void loop() 
{  
//  if (Serial.available() > 0) {
//    // read the incoming byte:
//    etat = Serial.read();
//  }

  if(etat)
  {
  
    digitalWrite(RED_PIN, LOW);    
    digitalWrite(BLUE_PIN, HIGH);
    
  // Initialisé la boucle si aucun badge n'est présent 
  if ( !rfid.PICC_IsNewCardPresent())
    return;

  // Vérifier la présence d'un nouveau badge 
  if ( !rfid.PICC_ReadCardSerial())
    return;

  //etat = 0;

  // Enregistrer l'ID du badge (4 octets)
  
  for (byte i = 0; i < N ; i++) 
  {
    nuidPICC[i] = rfid.uid.uidByte[i];
  }
  
  // Affichage de l'ID 
  //Serial.println("Un badge est détecté");
  //Serial.println(" L'UID du tag est:");
  for (byte i = 0; i < N; i++) 
  {
    
    Serial.print(nuidPICC[i], HEX);    
    
    if(nuidPICC[i+1] == 0){
      break;
    }
        
    if(i != N-1){
    Serial.print(":");}
  }
  Serial.println();

  // Re-Init RFID
  rfid.PICC_HaltA(); // Halt PICC
  rfid.PCD_StopCrypto1(); // Stop encryption on PCD

  digitalWrite(BLUE_PIN, LOW);
  digitalWrite(BUZZ_PIN, HIGH);
  digitalWrite(GREEN_PIN, HIGH);
  delay(200);
  digitalWrite(BUZZ_PIN, LOW);
  delay(500); 
  digitalWrite(GREEN_PIN, LOW);
  }
  else{    
    digitalWrite(RED_PIN, HIGH);
  }
}
