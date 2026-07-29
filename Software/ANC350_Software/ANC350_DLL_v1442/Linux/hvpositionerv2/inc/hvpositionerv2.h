/******************************************************************
 *
 *  Project:        Positioner
 *
 *  Filename:       hvpositioner.h
 *
 *  Zweck:          Positioner Schnittstelle
 *
 *  Autor:          NHands GmbH & Co KG
 *
 *   Datum | Autor | Beschreibung
 * --------+-------+--------------------------------
 * 29.01.08 HK      erstellt
 */
/******************************************************************/
/** @file
 *  Positioner Programmierschnittstelle
 *
 *  Definiert Funktionen für die Ansprache des Positioner:
 *  Verbinden, Konfigurieren, Daten abholen.
 */
/******************************************************************/
/* $Id: hvpositionerv2.h,v 1.5.4.7 2011/04/20 14:45:03 zaphod Exp $ */

#ifndef __POSITIONER_H__
#define __POSITIONER_H__


// Definitionen für die Windows-DLL-Schnittstelle
#ifdef unix
#define NCB_API
#else
#ifdef  NCB_EXPORTS
#define NCB_API __declspec(dllexport) _stdcall
#else
#define NCB_API __declspec(dllimport) _stdcall
#endif
#endif




#ifdef __cplusplus
extern "C" {
#endif

typedef int Int32;                       /**< Basis-Typ                          */

/** Rückgabewerte der Funktionen */
#define NCB_Ok               0               /**< Kein Fehler                        */
#define NCB_Error            (-1)            /**< Unbekannter/sonstiger Fehler       */
#define NCB_Timeout          1               /**< Timeout bei Datenabruf             */
#define NCB_NotConnected     2               /**< Kein Kontakt zum Positioner über USB    */
#define NCB_DriverError      3               /**< Fehler bei der Treiberansprache    */
#define NCB_BootIgnored      4               /**< Booten ignoriert, Gerät lief schon */
#define NCB_FileNotFound     5               /**< Boot-Image nicht gefunden          */
#define NCB_InvalidParam     6               /**< Übergebener Parameter ungültig     */
#define NCB_DeviceLocked     7               /**< Ein Verbindungsversuch schlug fehl, da das Device schon verwendet wird */
#define NCB_NotSpecifiedParam 8              /**< Übergebener Parameter ist außerhalb der Spezifikation     */





/** Testet die USB-Verbindung zum NCore
 *
 *  Prüft, ob der USB-Treiber für den NCore ansprechbar ist und wenn ja,
 *  ob eine USB-Verbindung zum Gerät besteht.
 *  Die Funktion ist nicht zwingend notwendig, wenn ohnehin mit NCB_boot()
 *  gebootet werden soll.
 *
 *  @return Testergebnis, Anzahl gefundener Positionierer
 */

struct PositionerInfo{
  int id;
  bool locked;
};

Int32 NCB_API PositionerCheck( PositionerInfo** posInfo );


/** Verbindet den Positionierer
 *
 *  Initialisiert die USB-Kommunikation mit dem Positionierer und verbindet das gewählte Gerät.
 *  Muss vor dem Konfigurieren und Daten-Abholen aufgerufen werden.
 *
 *  @param  deviceNo: Nummer des zu verbindenen Devices
 *
 *  @return Ergebnis der Initialisierung
 *  @n      NCB_Ok           - Verbindungsversuch erfolgreich
 *  @n      NCB_DriverError  - Treiberproblem, nicht installiert?
 *  @n      NCB_NotConnected - Kein Kontakt zum Gerät, USB-Kabel? DC-Power?
 *  @n      NCB_Error        - Unklarer Fehler
 */
Int32 NCB_API PositionerConnect( Int32 deviceNo, Int32* deviceHandle );


/** Beendet die Verbindung zum NCore
 *
 *  Baut die USB-Verbindung zum Gerät sauber ab.
 *  Ist aber nicht zwingend erforderlich.
 *
 *  @param  deviceNo: Nummer des zu schliessenden Devices
 *
 *  @return  Ergebnis:  NCB_Ok (einziger Rückgabewert)
 */
Int32 NCB_API PositionerClose( Int32 deviceHandle );



/** Ermittelt den Status der Steuerung einer Achse
 *
 *  Baut die USB-Verbindung zum Gerät sauber ab.
 *  Ist aber nicht zwingend erforderlich.
 *
 *  @param  deviceNo: Nummer des Devices
 *
 *  @param  axisNo: Nummer der Achse
 *
 *  @param  status: Zeiger auf Status. Bit0: Achse bewegt sich
 *                                     Bit1: Anschlag detektiert
 *                                     Bit2: Fehler im Sensor
 *                                     Bit3: Sensor nicht angeschlossen
 *
 *  @return  Ergebnis der Abfrage
 *  @n      NCB_Ok           - Abfrage erfolgreich
 *  @n      NCB_DriverError  - Treiberproblem, nicht installiert?
 *  @n      NCB_NotConnected - Kein Kontakt zum Gerät, USB-Kabel? DC-Power?
 *  @n      NCB_Error        - Unklarer Fehler
 */
Int32 NCB_API PositionerGetStatus( Int32 deviceHandle, Int32 axisNo, Int32* status );


Int32 NCB_API PositionerSetHardwareId( Int32 deviceHandle, Int32 id );


Int32 NCB_API PositionerSetOutput( Int32 deviceHandle, Int32 axisNo, bool enable );


Int32 NCB_API PositionerStaticAmplitude( Int32 deviceHandle, Int32 amplitude);


Int32 NCB_API PositionerGetPosition( Int32 deviceHandle, Int32 axisNo, Int32* position );


Int32 NCB_API PositionerGetRotCount( Int32 deviceHandle, Int32 axisNo, Int32* count );


Int32 NCB_API PositionerGetReference( Int32 deviceHandle, Int32 axisNo, Int32* position, bool* valid );


Int32 NCB_API PositionerGetReferenceRotCount( Int32 deviceHandle, Int32 axisNo, Int32* count );


Int32 NCB_API PositionerGetSpeed( Int32 deviceHandle, Int32 axisNo, Int32* speed );


Int32 NCB_API PositionerGetStepwidth( Int32 deviceHandle, Int32 axisNo, Int32* stepwidth );


Int32 NCB_API PositionerGetAmplitude( Int32 deviceHandle, Int32 axisNo, Int32* amplitude );


Int32 NCB_API PositionerGetFrequency( Int32 deviceHandle, Int32 axisNo, Int32* frequency );


Int32 NCB_API PositionerResetPosition( Int32 deviceHandle, Int32 axisNo );


Int32 NCB_API PositionerMoveAbsolute( Int32 deviceHandle, Int32 axisNo, Int32 position, Int32 rotCount = 0 );


Int32 NCB_API PositionerSetTargetPos( Int32 deviceHandle, Int32 axisNo, Int32 position, Int32 rotCount = 0 );


Int32 NCB_API PositionerMoveAbsoluteSync( Int32 deviceHandle, Int32 axes );


Int32 NCB_API PositionerUpdateAbsolute( Int32 deviceHandle, Int32 axisNo, Int32 position );


Int32 NCB_API PositionerMoveRelative( Int32 deviceHandle, Int32 axisNo, Int32 position, Int32 rotCount = 0 );


Int32 NCB_API PositionerMoveReference( Int32 deviceHandle, Int32 axisNo );


Int32 NCB_API PositionerStopDetection( Int32 deviceHandle, Int32 axisNo, bool enable );


Int32 NCB_API PositionerSingleCircleMode( Int32 deviceHandle, Int32 axisNo, bool enable );


Int32 NCB_API PositionerAmplitudeControl( Int32 deviceHandle, Int32 axisNo, Int32 mode );


Int32 NCB_API PositionerMoveSingleStep( Int32 deviceHandle, Int32 axisNo, Int32 dir );


Int32 NCB_API PositionerMoveContinuous( Int32 deviceHandle, Int32 axisNo, Int32 dir );


Int32 NCB_API PositionerStopMoving( Int32 deviceHandle, Int32 axisNo );


Int32 NCB_API PositionerStopApproach( Int32 deviceHandle, Int32 axisNo );


Int32 NCB_API PositionerAmplitude( Int32 deviceHandle, Int32 axisNo, Int32 amplitude );


Int32 NCB_API PositionerFrequency( Int32 deviceHandle, Int32 axisNo, Int32 frequency );


Int32 NCB_API PositionerDCLevel( Int32 deviceHandle, Int32 axisNo, Int32 level );


Int32 NCB_API PositionerTrigger( Int32 deviceHandle, Int32 triggerNo, Int32 lowLevel, Int32 highLevel );


Int32 NCB_API PositionerTriggerPolarity( Int32 deviceHandle, Int32 triggerNo, Int32 polarity );


Int32 NCB_API PositionerTriggerAxis( Int32 deviceHandle, Int32 triggerNo, Int32 axis );


Int32 NCB_API PositionerTriggerEpsilon( Int32 deviceHandle, Int32 triggerNo, Int32 epsilon );


Int32 NCB_API PositionerLoad( Int32 deviceHandle, Int32 axisNo, char* filename );


Int32 NCB_API PositionerDcInEnable( Int32 deviceHandle, Int32 axisNo, bool enable );


Int32 NCB_API PositionerAcInEnable( Int32 deviceHandle, Int32 axisNo, bool enable );


Int32 NCB_API PositionerIntEnable( Int32 deviceHandle, Int32 axisNo, bool enable );


Int32 NCB_API PositionerGetDcInEnable( Int32 deviceHandle, Int32 axisNo, bool* enable );


Int32 NCB_API PositionerGetDcLevel( Int32 deviceHandle, Int32 axisNo, Int32* level );


Int32 NCB_API PositionerGetAcInEnable( Int32 deviceHandle, Int32 axisNo, bool* enable );


Int32 NCB_API PositionerGetIntEnable( Int32 deviceHandle, Int32 axisNo, bool* enable );


Int32 NCB_API PositionerExternalStepFwdInput( Int32 deviceHandle, Int32 axisNo, Int32 input );


Int32 NCB_API PositionerExternalStepBkwInput( Int32 deviceHandle, Int32 axisNo, Int32 input );


Int32 NCB_API PositionerExternalStepInputEdge( Int32 deviceHandle, Int32 axisNo, Int32 edge );


Int32 NCB_API PositionerBandwidthLimitEnable( Int32 deviceHandle, Int32 axisNo, bool enable );


Int32 NCB_API PositionerGetBandwidthLimitEnable( Int32 deviceHandle, Int32 axisNo, bool* enable );


Int32 NCB_API PositionerCapMeasure( Int32 deviceHandle, Int32 axisNo, Int32* capacity );


Int32 NCB_API PositionerSetStopDetectionSticky( Int32 deviceHandle, Int32 axisNo, bool enable );


Int32 NCB_API PositionerClearStopDetection( Int32 deviceHandle, Int32 axisNo );


Int32 NCB_API PositionerSetTargetGround( Int32 deviceHandle, Int32 axisNo, bool enable );


Int32 NCB_API PositionerTriggerModeIn( Int32 deviceHandle, Int32 mode );


Int32 NCB_API PositionerTriggerModeOut( Int32 deviceHandle, Int32 mode );


Int32 NCB_API PositionerQuadratureAxis( Int32 deviceHandle, Int32 quadratureNo, Int32 axisNo );


Int32 NCB_API PositionerQuadratureInputPeriod( Int32 deviceHandle, Int32 quadratureNo, Int32 period );


Int32 NCB_API PositionerQuadratureOutputPeriod( Int32 deviceHandle, Int32 quadratureNo, Int32 period );


Int32 NCB_API PositionerStepCount( Int32 deviceHandle, Int32 axisNo, Int32 stepCount );


Int32 NCB_API PositionerSensorPowerGroupA( Int32 deviceHandle, bool enable );


Int32 NCB_API PositionerSensorPowerGroupB( Int32 deviceHandle, bool enable );


#ifdef __cplusplus
}
#endif

#endif 

