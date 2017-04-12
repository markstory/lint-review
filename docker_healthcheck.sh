#!/bin/bash
set -eo pipefail

if [ "$1" == "web" ]; then
  curl -f http://localhost:5000/ping
fi

if [ "$1" == "worker" ]; then
  celery inspect ping -A lintreview.tasks -d "celery@$HOSTNAME"
fi
