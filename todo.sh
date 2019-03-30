#!/usr/bin/env bash
grep -rniC 2 TODO --exclude=.* --exclude-dir=.* --exclude=todo.sh --exclude=TODO > TODO 2> /dev/null
