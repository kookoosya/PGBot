#!/bin/bash
# Единственный рабочий прод-URL до смены домена владельцем.
CANONICAL_SITE_HOST="192-210-213-135.sslip.io"
CANONICAL_SITE_URL="https://${CANONICAL_SITE_HOST}"
export CANONICAL_SITE_HOST CANONICAL_SITE_URL
