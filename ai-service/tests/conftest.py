"""
Aggiunge la directory ai-service al sys.path in modo che gli import funzionino
senza installare il pacchetto.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
