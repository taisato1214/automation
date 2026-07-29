/*******************************************************************************
 *
 *  Project:        HVPositioner Library
 *
 *  Filename:       example0.c
 *
 *  Purpose:        Trivial application example for use of hvpositionerv2 lib
 *
 *  Author:         NHands GmbH & Co KG
 *
 *******************************************************************************/
/* $Id: example0.cpp,v 1.4.10.3 2011/01/11 09:56:47 trurl Exp $ */

#include <cstdio>
#include <cstdlib>
#ifdef unix
#include <unistd.h>
#define Sleep(ms) usleep(ms*1000)
#else
#include <windows.h>
#endif
#include "hvpositionerv2.h"


void checkError( Int32 code )
{
  switch ( code ) {
  case NCB_Ok:                return;
  case NCB_BootIgnored:       printf( "Warning: boot ignored\n" );    return;
  case NCB_Error:             printf( "Error: unspecific\n" );        break;
  case NCB_Timeout:           printf( "Error: comm. timeout\n" );     break;
  case NCB_NotConnected:      printf( "Error: not connected\n" );     break;
  case NCB_DriverError:       printf( "Error: driver error\n" );      break;
  case NCB_FileNotFound:      printf( "Error: file not found\n" );    break;
  case NCB_InvalidParam:      printf( "Error: invalid parameter\n" ); break;
  case NCB_DeviceLocked:      printf( "Error: device locked\n" );     break;
  case NCB_NotSpecifiedParam: printf( "Error: unspec. parameter\n" ); break;
  default:                    printf( "Error: unknown\n" );
  }
  exit( 1 );
}


int main( int /* argc */, char ** /* argv */ )
{
  PositionerInfo * pi = 0;
  Int32 devCount = PositionerCheck( &pi );
  printf( "%d devices found.\n", devCount );
  for ( int i = 0; pi && i < devCount; ++i ) {
    printf( "  ID=%d, locked=%s\n", pi[i] .id, pi[i] .locked ? "yes" : "no" );
  }

  for ( int i = 0; pi && i < devCount; ++i ) {
    if ( pi[i] .locked )
      continue;

    printf( "Trying to connect to device %d\n", pi[i] .id );
    Int32 handle = 0;
    checkError( PositionerConnect( i, &handle ) );
    printf( "PositionerConnect returned with handle %d\n", handle );

    checkError( PositionerDCLevel( handle, 0, 1 ) );

    printf( "You should here the axis0 relais clicking...\n" );
    Sleep( 1000 );
    printf( "CLICK (on)\n" );
    checkError( PositionerSetOutput( handle, 0, true ) );
    Sleep( 1500 );
    printf( "CLICK (off)\n" );
    checkError( PositionerSetOutput( handle, 0, false ) );

    // Don't close before command is sent (close is not very graceful).
    // Send delay seems to be a consequence of Nagle's algorithm.
    Sleep( 500 );
    PositionerClose( handle );
  }

  return 0;
}
