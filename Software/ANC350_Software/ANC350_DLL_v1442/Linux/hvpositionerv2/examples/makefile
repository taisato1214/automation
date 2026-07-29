#
# Project:       ANC 350 user lib
#
# Filename:      makefile
#
# Purpose:       makefile for example 0 for Linux
#
# $Id: makefile,v 1.2 2009/01/19 00:10:51 trurl Exp $

example0: example0.o
	g++ -o example0 example0.o -L../lib -lhvpositionerv2 -lnhconnect -lpthread

example0.o: example0.cpp
	g++ -o example0.o -I../inc -c -g -Wall example0.cpp
