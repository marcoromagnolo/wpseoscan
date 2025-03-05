#!/bin/bash

ps -p `cat wpseoscan.pid` -o pid,ppid,cmd,%cpu,%mem,stime,user,time