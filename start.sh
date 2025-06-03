#!/bin/bash
export PATH="/usr/local/bin:$PATH"
streamlit run src/app.py --server.port=$PORT --server.address=0.0.0.0 