
/*
	Arduino | Atmega - PC(Linux) serial communication
	Show Celsius temeperature in 7 segment 4 digit display. Principal model : sh5461as

	PROTOCOL: Begin digit - SYMBOL|ACTIVE|DOT_, End digit - SYMBOL|ACTIVE|DOT\r\n

	SYMBOL ACCEPT DATA:

	 SYMBOL    LED SYMBOL
	0,...,9  -  0,...,9
	     10  -  "-"

	Example.
	Number - "-1.23" - [ 10|1|0_1|1|1_2|1|0_3|1|0 ]
	Number - "56.3"  - [  0|0|0_5|1|0_6|1|1_3|1|0 ]
*/

bool ledNumbers[11][8] = {
  // 6 7 8 9 10 11 12 13
	{1,1,1,0,1,1,1,0},
	{0,0,1,0,1,0,0,0},
	{0,1,1,1,0,1,1,0},
	{0,1,1,1,1,1,0,0},
	{1,0,1,1,1,0,0,0},
	{1,1,0,1,1,1,0,0},
	{1,1,0,1,1,1,1,0},
	{0,1,1,0,1,0,0,0},
	{1,1,1,1,1,1,1,0},
	{1,1,1,1,1,1,0,0},
	{0,0,0,1,0,0,0,0}
};

//One digit LED - [|DL|DL|DL|DL|]

struct DigitLED {
	int number;
	bool isActive;
	bool isDot;
};

unsigned long lastMillisValue;

DigitLED ledDigits[4];

int currentDigitLED = 0;

bool isSegmentActive = false;

String receviedData = "";

void setup() {
	Serial.begin(9600);

	for (int i = 2; i <= 13; i++){
		pinMode(i,OUTPUT);
		digitalWrite(i,HIGH);
	}

	setNumberToSegment(0,false);
	for (int i = 1 ; i <= 4; i++)
		setSegmentActive(i,false);
	
	DigitLED firstLed;
	firstLed.isActive = true;
	firstLed.isDot = true;
	firstLed.number = 6;

	DigitLED secondLed;
	secondLed.isActive = true;
	secondLed.isDot = false;
	secondLed.number = 0;

	DigitLED thirdLed;
	thirdLed.isActive = true;
	thirdLed.isDot = false;
	thirdLed.number = 0;

	DigitLED fourthLed;
	fourthLed.isActive = true;
	fourthLed.isDot = false;
	fourthLed.number = 0;

	ledDigits[0] = firstLed;
	ledDigits[1] = secondLed;
	ledDigits[2] = thirdLed;
	ledDigits[3] = fourthLed;
}

void loop() {
	unsigned long currentMillis = millis();

	bool isPermitAction = isMillisChange(currentMillis);
	if (isPermitAction){
		if (currentDigitLED > 3) currentDigitLED = 0;
		DigitLED currentLed = ledDigits[currentDigitLED];

		int number = currentLed.number;
		bool isDot = currentLed.isDot;
		bool isActive = currentLed.isActive;

		setNumberToSegment(number,isDot);
		setOnlyOneSegmentActive(currentDigitLED + 1, isActive);

		++currentDigitLED;
	}

	if (Serial.available() > 0) {
		int inputByte = Serial.read();
		if (inputByte != 13){
			receviedData = receviedData + String((char)inputByte);
		}else{
			bool isReceviedDataValid = 
				isStringExistsDelimiter(receviedData,'_',3) &&
				isStringExistsDelimiter(receviedData,'|',8) ;
			if (isReceviedDataValid){
				for (int i = 0; i < 4; i++){
					String currentLED = split(receviedData,'_',i);
					DigitLED currentDigitLED = getDigitLED(currentLED);
					ledDigits[i] = currentDigitLED;
				}
			}
			receviedData = "";
		}
	}
}

DigitLED getDigitLED(String digit){
	DigitLED currentDigitLED;
	currentDigitLED.number = split(digit,'|',0).toInt();
	currentDigitLED.isActive = (bool) split(digit,'|',1).toInt();
	currentDigitLED.isDot = (bool) split(digit,'|',2).toInt();
	return currentDigitLED;
}

bool isStringExistsDelimiter(String data, char delimiter, int count){
	int delimiterCounter = 0;
	for (int i = 0; i < data.length(); i++){
		char currentSymbol = data.charAt(i);
		if (currentSymbol == delimiter)
			++delimiterCounter;
	}
	return delimiterCounter == count;
}

String split(String data, char separator, int index){
  int found = 0;
  int strIndex[] = {0, -1};
  int maxIndex = data.length() - 1;

	for (int i = 0; i <= maxIndex && found <= index; i++){
		if (data.charAt(i) == separator || i == maxIndex){
			found++;
			strIndex[0] = strIndex[1] + 1;
			strIndex[1] = (i == maxIndex) ? i + 1 : i;
		}
	}

  return found>index ? data.substring(strIndex[0], strIndex[1]) : "";
}


bool isMillisChange(unsigned long millis){
	if (millis != lastMillisValue){
		lastMillisValue = millis;
		return true;
	}
	return false;
}

void setNumberToSegment(int number, bool isDot){
	for (int i = 0; i < 8; i++){
		bool isCurrentBitActive = ledNumbers[number][i];
		digitalWrite(i + 6, isCurrentBitActive);
	}
	if (isDot)
		digitalWrite(13,HIGH);
}

// Start with "1" [|1|2|3|4|]
void setOnlyOneSegmentActive(int segmentIndex, bool isActive){
	setSegmentActive(segmentIndex, isActive);
	for (int i = 1; i <= 4; i++){
		if (segmentIndex != i)
			setSegmentActive(i, false);
	}
}

void setSegmentActive(int segmentIndex, bool isActive){
	digitalWrite(segmentIndex + 1, isActive);
}